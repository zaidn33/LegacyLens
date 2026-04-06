"""
LLM provider abstraction with swappable implementations.

Ships with:
  - GraniteProvider  — IBM Granite 4.0 (primary, requires API key)
  - OpenAIProvider   — OpenAI GPT-4o (high-capacity, requires API key)
  - GeminiProvider   — Google Gemini 1.5 Flash (free, high-limit)
  - MockProvider     — deterministic stub for development & CI
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from abc import ABC, abstractmethod
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential


class LLMProvider(ABC):
    """Abstract base class — implement ``generate`` for each backend."""

    def _parse_json(self, content: str) -> dict:
        """Parse JSON response with a fault-tolerant fallback using json-repair."""
        import json
        try:
            # First try standard parsing
            parsed = json.loads(content, strict=False)
        except json.JSONDecodeError:
            # Fallback to json-repair for truncated or malformed responses
            try:
                from json_repair import repair_json
                repaired = repair_json(content)
                parsed = json.loads(repaired)
            except Exception as e:
                # If repair fails, re-raise the original error or a clearer one
                raise ValueError(f"Failed to parse or repair JSON response: {content[:100]}...") from e

        # --- Safety Net: Flatten List Wrappers ---
        # If the LLM returned a list containing a single object, extract it.
        # This handles common accidents like `[{ "key": "val" }]`.
        if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
            return parsed[0]
            
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")
            
        return parsed

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict:
        """Return a parsed JSON dict conforming to *schema*."""
        ...


# ---------------------------------------------------------------------------
# Granite (production)
# ---------------------------------------------------------------------------

class GraniteProvider(LLMProvider):
    """
    IBM Granite provider via WatsonX.

    Uses the WatsonX REST API directly with IAM token authentication.
    Handles token exchange, retries, and JSON schema enforcement.
    """

    IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("WATSONX_APIKEY")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        watsonx_url = base_url or os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.base_url = watsonx_url.rstrip("/")
        self.model = model or os.getenv("WATSONX_MODEL", "ibm/granite-3-8b-instruct")

        if not self.api_key:
            raise ValueError("WATSONX_APIKEY is required for GraniteProvider")
        if not self.project_id:
            raise ValueError("WATSONX_PROJECT_ID is required for GraniteProvider")

        # Token is fetched lazily on first generate() call
        self._iam_token: str | None = None
        self._token_expiry: float = 0

    def _refresh_iam_token(self) -> None:
        """Exchange IBM Cloud API key for a time-limited IAM bearer token."""
        import time
        import httpx

        resp = httpx.post(
            self.IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        self._iam_token = body["access_token"]
        # Refresh 60s before expiry
        self._token_expiry = body.get("expiration", time.time() + 3600) - 60

    def _get_token(self) -> str:
        """Return a valid IAM token, refreshing if expired."""
        import time
        if time.time() >= self._token_expiry:
            self._refresh_iam_token()
        return self._iam_token

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict:
        import httpx

        token = self._get_token()
        url = (
            f"{self.base_url}/ml/v1/text/chat"
            f"?version=2024-05-31&project_id={self.project_id}"
        )

        # Build schema instructions for the system prompt so the model
        # returns JSON matching the expected shape.
        schema_hint = json.dumps(schema, indent=2)
        full_system = (
            f"{system_prompt}\n\n"
            f"IMPORTANT: You MUST respond with valid JSON matching this exact schema. "
            f"Do not include any text before or after the JSON object.\n\n"
            f"```json\n{schema_hint}\n```"
        )

        payload = {
            "model_id": self.model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
            "parameters": {
                "max_tokens": 16000,
                "temperature": 0.0,
            },
            "project_id": self.project_id,
        }

        try:
            resp = httpx.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=120,
            )
            resp.raise_for_status()
            body = resp.json()

            # Extract the assistant message content
            choices = body.get("choices", [])
            if not choices:
                raise ValueError(f"WatsonX returned no choices. Full response: {body}")

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("WatsonX returned empty content")

            # Strip markdown fences if present
            text = content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            return self._parse_json(text)

        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"WatsonX HTTP {e.response.status_code}: {e.response.text[:500]}"
            )
        except Exception as e:
            raise ValueError(f"Provider execution failed: {e}")


# ---------------------------------------------------------------------------
# Groq (fast, free tier)
# ---------------------------------------------------------------------------

class GroqProvider(LLMProvider):
    """
    Groq provider via OpenAI-compatible API.

    Uses langchain_openai.ChatOpenAI pointed at Groq's endpoint.
    Structured output is enforced via JSON schema instructions.
    """

    GROQ_BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for GroqProvider")

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=45),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict:
        import httpx

        full_system = (
            f"{system_prompt}\n\n"
            "IMPORTANT: Respond with a valid JSON object only. "
            "No prose, no markdown fences, no text before or after the JSON.\n\n"
            "Nested field formats (follow exactly):\n"
            "- dependencies: [{\"reference_name\": \"...\", \"resolved_filename\": \"...\" or null, \"status\": \"resolved\" or \"unresolved\"}]\n"
            "- logic_dictionary: [{\"legacy_name\": \"...\", \"proposed_modern_name\": \"...\", \"meaning\": \"...\", \"confidence\": \"High\"|\"Medium\"|\"Low\"}]\n"
            "- inputs_and_outputs: {\"inputs\": [...], \"outputs\": [...], \"external_touchpoints\": [...]}\n"
            "- assumptions_and_ambiguities: {\"observed\": [...], \"inferred\": [...], \"unknown\": [...]}\n"
            "- confidence_assessment: {\"level\": \"High\"|\"Medium\"|\"Low\", \"rationale\": \"...\"}\n"
            "- logic_step_mapping: [{\"function_or_test_name\": \"...\", \"logic_step\": \"...\", \"notes\": \"...\"}]\n"
            "- defects: [{\"description\": \"...\", \"severity\": \"critical\"|\"major\"|\"minor\", \"logic_step\": \"...\", \"suggested_fix\": \"...\"}]\n"
            "- confidence (in reviewer output): {\"level\": \"High\"|\"Medium\"|\"Low\", \"rationale\": \"...\"}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 8000,
        }

        try:
            resp = httpx.post(
                f"{self.GROQ_BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )
            resp.raise_for_status()
            body = resp.json()

            choices = body.get("choices", [])
            if not choices:
                raise ValueError(f"Groq returned no choices. Response: {body}")

            content = choices[0].get("message", {}).get("content", "").strip()
            if not content:
                raise ValueError("Groq returned empty content")

            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            content = content.strip()

            return self._parse_json(content)

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Groq HTTP {e.response.status_code}: {e.response.text[:500]}")
        except Exception as e:
            raise ValueError(f"Provider execution failed: {e}")


# ---------------------------------------------------------------------------
# OpenAI (standard high-capacity)
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """
    OpenAI provider via OpenAI's native API.

    Handles structured output via JSON schema enforcement.
    Requires OPENAI_API_KEY to be set in .env.
    """

    OPENAI_BASE_URL = "https://api.openai.com/v1"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict:
        import httpx

        full_system = (
            f"{system_prompt}\n\n"
            "IMPORTANT: Respond with a valid JSON object only. "
            "No prose, no markdown fences, no text before or after the JSON.\n\n"
            "JSON structure MUST follow the schema provided."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens or 16384,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = httpx.post(
                f"{self.OPENAI_BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=180,
            )
            resp.raise_for_status()
            body = resp.json()

            choices = body.get("choices", [])
            if not choices:
                raise ValueError(f"OpenAI returned no choices. Response: {body}")

            content = choices[0].get("message", {}).get("content", "").strip()
            if not content:
                raise ValueError("OpenAI returned empty content")

            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            content = content.strip()

            return self._parse_json(content)

        except httpx.HTTPStatusError as e:
            raise ValueError(f"OpenAI HTTP {e.response.status_code}: {e.response.text[:500]}")
        except Exception as e:
            raise ValueError(f"Provider execution failed: {e}")


# ---------------------------------------------------------------------------
# Gemini (stable, high-limit free tier)
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    """
    Google Gemini provider via Google AI Studio API.

    Uses Gemini 1.5 Flash for high-speed, high-token-limit analysis.
    Requires GEMINI_API_KEY to be set in .env.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider")

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=15),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict:
        import httpx

        # Clean the model name to avoid double 'models/' prefix
        model_name = self.model
        if model_name.startswith("models/"):
            model_name = model_name.replace("models/", "", 1)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            f"?key={self.api_key}"
        )

        full_system = (
            f"{system_prompt}\n\n"
            "IMPORTANT: Respond with a valid JSON object only. "
            "No prose, no markdown fences, no text before or after the JSON.\n\n"
            f"Schema:\n{json.dumps(schema, indent=2)}"
        )

        print(f"[PROVIDER: GEMINI] Calling {model_name} with ~{len(full_system) + len(user_prompt)} characters (max_tokens={max_tokens})...")


        payload = {
            "contents": [{
                "parts": [{"text": f"System Instruction: {full_system}\n\nUser Input: {user_prompt}"}]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "response_mime_type": "application/json",
                "max_output_tokens": max_tokens,
            }
        }

        try:
            resp = httpx.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=180,
            )
            resp.raise_for_status()
            body = resp.json()

            # Extract content from Gemini's specific response structure
            candidates = body.get("candidates", [])
            if not candidates:
                raise ValueError(f"Gemini returned no candidates. Response: {body}")

            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            if not text:
                raise ValueError("Gemini returned empty text content")

            # Strip markdown fences if Gemini ignored the instruction
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            return self._parse_json(text)

        except httpx.HTTPStatusError as e:
            raise ValueError(f"Gemini HTTP {e.response.status_code}: {e.response.text[:500]}")
        except Exception as e:
            raise ValueError(f"Provider execution failed: {e}")


# ---------------------------------------------------------------------------
# Mock (development & CI)
# ---------------------------------------------------------------------------

class MockProvider(LLMProvider):
    """
    Deterministic mock that returns pre-built responses for each agent.

    Detects which agent is calling based on system prompt content and
    returns the appropriate mock response. When ``mock_response`` is
    supplied, it bypasses detection and always returns that dict.
    """

    def __init__(self, mock_response: dict | None = None):
        self._mock_response = mock_response

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict:
        if self._mock_response is not None:
            return self._mock_response

        import re
        m = re.search(r"run_version=(\d+)", user_prompt)
        run_version = int(m.group(1)) if m else 1

        # Route based on system prompt identity
        if "Legacy Logic Architect" in system_prompt:
            is_multi_file = "Auxiliary Dependency Files Provided" in user_prompt
            return self._analyst_response(is_multi_file, run_version)
        elif "Mapper Agent" in system_prompt:
            return self._mapper_response(run_version)
        elif "Coder Agent" in system_prompt:
            return self._coder_response(run_version)
        elif "Generate Pytest tests" in system_prompt:
            return self._test_gen_response(run_version)
        elif "Reviewer Agent" in system_prompt:
            return self._reviewer_response(run_version)
        else:
            return self._analyst_response(False, run_version)  # fallback

    # ------------------------------------------------------------------
    # Mapper mock
    # ------------------------------------------------------------------

    @staticmethod
    def _mapper_response(run_version: int = 1) -> dict:
        """Realistic MapperOutput for the sample COBOL billing module."""
        return {
            "variables": [
                {"cobol_name": "WS-CUST-FS", "python_name": "cust_file_status", "python_type": "str", "initial_value": "None", "pic_clause": "PIC XX", "level": "05"},
                {"cobol_name": "WS-RATE-FS", "python_name": "rate_file_status", "python_type": "str", "initial_value": "None", "pic_clause": "PIC XX", "level": "05"},
                {"cobol_name": "WS-BILL-FS", "python_name": "bill_file_status", "python_type": "str", "initial_value": "None", "pic_clause": "PIC XX", "level": "05"},
                {"cobol_name": "WS-ERR-FS", "python_name": "err_file_status", "python_type": "str", "initial_value": "None", "pic_clause": "PIC XX", "level": "05"},
                {"cobol_name": "WS-EOF-FLAG", "python_name": "eof_flag", "python_type": "str", "initial_value": "'N'", "pic_clause": "PIC X", "level": "05"},
                {"cobol_name": "WS-CUST-ID", "python_name": "customer_id", "python_type": "str", "initial_value": "None", "pic_clause": "PIC X(10)", "level": "05"},
                {"cobol_name": "WS-CUST-NAME", "python_name": "customer_name", "python_type": "str", "initial_value": "None", "pic_clause": "PIC X(30)", "level": "05"},
                {"cobol_name": "WS-CUST-STATUS", "python_name": "account_status", "python_type": "str", "initial_value": "None", "pic_clause": "PIC X", "level": "05"},
                {"cobol_name": "WS-USAGE-AMT", "python_name": "monthly_usage_units", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(7)V99", "level": "05"},
                {"cobol_name": "WS-BASE-RATE", "python_name": "base_rate", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(3)V9(4)", "level": "05"},
                {"cobol_name": "WS-TIER2-THRESHOLD", "python_name": "tier2_threshold", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(7)V99", "level": "05"},
                {"cobol_name": "WS-TIER2-RATE", "python_name": "tier2_rate", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(3)V9(4)", "level": "05"},
                {"cobol_name": "WS-TIER3-THRESHOLD", "python_name": "tier3_threshold", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(7)V99", "level": "05"},
                {"cobol_name": "WS-TIER3-RATE", "python_name": "tier3_rate", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(3)V9(4)", "level": "05"},
                {"cobol_name": "WS-DAYS-OVERDUE", "python_name": "days_overdue", "python_type": "int", "initial_value": "None", "pic_clause": "PIC 9(4)", "level": "05"},
                {"cobol_name": "WS-LATE-FEE-PCT", "python_name": "late_fee_percentage", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9V9(4)", "level": "05"},
                {"cobol_name": "WS-BASE-CHARGES", "python_name": "base_charges", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(9)V99", "level": "05"},
                {"cobol_name": "WS-TIER2-CHARGES", "python_name": "tier2_charges", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(9)V99", "level": "05"},
                {"cobol_name": "WS-TIER3-CHARGES", "python_name": "tier3_charges", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(9)V99", "level": "05"},
                {"cobol_name": "WS-SUBTOTAL", "python_name": "subtotal", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(9)V99", "level": "05"},
                {"cobol_name": "WS-PENALTY", "python_name": "penalty", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(9)V99", "level": "05"},
                {"cobol_name": "WS-TOTAL-DUE", "python_name": "total_amount_due", "python_type": "Decimal", "initial_value": "None", "pic_clause": "PIC 9(9)V99", "level": "05"},
                {"cobol_name": "WS-BILLING-DT", "python_name": "billing_date", "python_type": "str", "initial_value": "None", "pic_clause": "PIC X(10)", "level": "01"},
                {"cobol_name": "WS-RECORDS-READ", "python_name": "records_read", "python_type": "int", "initial_value": "0", "pic_clause": "PIC 9(6)", "level": "05"},
                {"cobol_name": "WS-RECORDS-BILLED", "python_name": "records_billed", "python_type": "int", "initial_value": "0", "pic_clause": "PIC 9(6)", "level": "05"},
                {"cobol_name": "WS-RECORDS-ERROR", "python_name": "records_error", "python_type": "int", "initial_value": "0", "pic_clause": "PIC 9(6)", "level": "05"},
                {"cobol_name": "WS-ERR-CODE", "python_name": "error_code", "python_type": "int", "initial_value": "None", "pic_clause": "PIC 9(4)", "level": "01"},
                {"cobol_name": "WS-ERR-MSG", "python_name": "error_message", "python_type": "str", "initial_value": "None", "pic_clause": "PIC X(50)", "level": "01"},
            ],
            "global_state_summary": "Extracted 27 variables from COBOL DATA DIVISION covering file status, customer data, rate tables, billing calculations, and counters.",
        }

    # ------------------------------------------------------------------
    # Test generation mock
    # ------------------------------------------------------------------

    @staticmethod
    def _test_gen_response(run_version: int = 1) -> dict:
        """Mock response for the chunked test generation call."""
        return {
            "generated_tests": (
                "import pytest\n\n"
                "def test_placeholder():\n"
                "    assert True  # Mock test generated during chunked execution\n"
            ),
        }

    # ------------------------------------------------------------------
    # Analyst mock
    # ------------------------------------------------------------------

    @staticmethod
    def _analyst_response(is_multi_file: bool = False, run_version: int = 1) -> dict:
        """Realistic Logic Map for the sample COBOL billing module."""
        return {
            "executive_summary": (
                "This module calculates monthly billing amounts for customer "
                "accounts based on usage tiers, applies late-payment penalties, "
                "and produces a billing summary record. It is a core component "
                "of the accounts receivable pipeline within a financial services "
                "billing system."
            ),
            "business_objective": (
                "Calculate tiered monthly billing charges with late-payment "
                "penalties and output a formatted billing summary for "
                "downstream invoice generation."
            ),
            "inputs_and_outputs": {
                "inputs": [
                    "CUSTOMER-RECORD: customer account details "
                    "(ID, name, status, balance)",
                    "USAGE-RECORD: monthly usage amount in units",
                    "RATE-TABLE: tiered pricing structure "
                    "(base rate, tier thresholds, tier rates)",
                    "PAYMENT-HISTORY: last payment date and amount",
                ],
                "outputs": [
                    "BILLING-SUMMARY: calculated charges, penalties, "
                    "total due, billing date",
                    "ERROR-REPORT: validation failures written to error "
                    "log file",
                ],
                "external_touchpoints": [
                    "CUSTOMER-FILE: sequential file read for customer records",
                    "RATE-FILE: indexed file read for rate table lookup",
                    "BILLING-OUTPUT: sequential file write for billing summaries",
                    "ERROR-LOG: sequential file write for error reporting",
                ],
            },
            "logic_dictionary": [
                {
                    "legacy_name": "WS-CUST-ID",
                    "proposed_modern_name": "customer_id",
                    "meaning": "Unique customer account identifier",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-CUST-NAME",
                    "proposed_modern_name": "customer_name",
                    "meaning": "Customer display name",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-CUST-STATUS",
                    "proposed_modern_name": "account_status",
                    "meaning": "Account status flag: A=Active, S=Suspended, C=Closed",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-USAGE-AMT",
                    "proposed_modern_name": "monthly_usage_units",
                    "meaning": "Usage quantity for the billing period",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-BASE-RATE",
                    "proposed_modern_name": "base_rate",
                    "meaning": "Base charge per unit for tier 1",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-TIER2-THRESHOLD",
                    "proposed_modern_name": "tier2_threshold",
                    "meaning": "Usage threshold above which tier 2 rate applies",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-TIER2-RATE",
                    "proposed_modern_name": "tier2_rate",
                    "meaning": "Rate per unit for usage above tier 2 threshold",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-TIER3-THRESHOLD",
                    "proposed_modern_name": "tier3_threshold",
                    "meaning": "Usage threshold above which tier 3 rate applies",
                    "confidence": "Medium",
                },
                {
                    "legacy_name": "WS-TIER3-RATE",
                    "proposed_modern_name": "tier3_rate",
                    "meaning": "Rate per unit for usage above tier 3 threshold",
                    "confidence": "Medium",
                },
                {
                    "legacy_name": "WS-LATE-FEE-PCT",
                    "proposed_modern_name": "late_fee_percentage",
                    "meaning": "Percentage penalty applied for overdue payments",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-DAYS-OVERDUE",
                    "proposed_modern_name": "days_overdue",
                    "meaning": "Number of days since last payment was due",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-TOTAL-DUE",
                    "proposed_modern_name": "total_amount_due",
                    "meaning": "Final calculated billing amount including penalties",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-BILLING-DT",
                    "proposed_modern_name": "billing_date",
                    "meaning": "Date the billing calculation was performed",
                    "confidence": "High",
                },
                {
                    "legacy_name": "WS-ERR-CODE",
                    "proposed_modern_name": "error_code",
                    "meaning": "Numeric error identifier for validation failures",
                    "confidence": "Medium",
                },
                {
                    "legacy_name": "WS-ERR-MSG",
                    "proposed_modern_name": "error_message",
                    "meaning": "Human-readable error description",
                    "confidence": "Medium",
                },
            ],
            "step_by_step_logic_flow": [
                "1. Open input files (CUSTOMER-FILE, RATE-FILE) and output "
                "files (BILLING-OUTPUT, ERROR-LOG).",
                "2. Read the RATE-TABLE to load tier thresholds and rates "
                "into working storage.",
                "3. Read the next CUSTOMER-RECORD. If end-of-file, go to "
                "step 12.",
                "4. Validate the customer record: check that CUST-ID is not "
                "empty, CUST-STATUS is 'A' (active). If validation fails, "
                "write to ERROR-LOG and go to step 3.",
                "5. Read the corresponding USAGE-RECORD for this customer.",
                "6. Calculate base charges: multiply usage units by base rate "
                "for units up to tier 2 threshold.",
                "7. If usage exceeds tier 2 threshold, calculate tier 2 "
                "charges: multiply excess units (up to tier 3 threshold) by "
                "tier 2 rate.",
                "8. If usage exceeds tier 3 threshold, calculate tier 3 "
                "charges: multiply excess units beyond tier 3 threshold by "
                "tier 3 rate.",
                "9. Sum base + tier 2 + tier 3 charges into subtotal.",
                "10. Check payment history: if days overdue > 30, apply late "
                "fee percentage to subtotal and add to total. If days "
                "overdue > 90, cap penalty at 25% of subtotal.",
                "11. Write BILLING-SUMMARY record (customer ID, name, "
                "subtotal, penalty, total due, billing date) to "
                "BILLING-OUTPUT. Go to step 3.",
                "12. Close all files. Write processing summary count to "
                "console. Stop.",
            ],
            "business_rules": [
                "Only active accounts (status = 'A') are billed; suspended "
                "and closed accounts are skipped with a log entry.",
                "Billing uses three pricing tiers: base rate up to tier 2 "
                "threshold, tier 2 rate for usage between tier 2 and tier 3 "
                "thresholds, tier 3 rate for usage above tier 3 threshold.",
                "Late payment penalty applies only when payment is overdue "
                "by more than 30 days.",
                "Late penalty is calculated as: subtotal * late_fee_percentage.",
                "Late penalty is capped at 25% of subtotal when payment is "
                "overdue by more than 90 days.",
                "Customers with zero usage still receive a billing record "
                "with $0.00 charges.",
                "Error records are logged but do not halt batch processing.",
            ],
            "edge_cases": [
                "Customer with exactly 0 usage units: should produce a "
                "$0.00 billing record, not be skipped.",
                "Usage exactly at a tier boundary: the threshold value "
                "itself falls in the lower tier.",
                "Days overdue exactly at 30: no penalty applied (penalty "
                "Negative usage is treated as zero.",
                "Missing account creation dates trigger an automatic default to standard rates.",
                "Delinquent records missing past-due flags silently skip penalties."
            ],
            "dependencies": [
                {
                    "reference_name": "definitions.cpy",
                    "resolved_filename": "definitions.cpy",
                    "status": "resolved"
                } if is_multi_file else {
                    "reference_name": "CUSTOMER-RECORD-FILE",
                    "resolved_filename": None,
                    "status": "unresolved"
                }
            ],
            "critical_constraints": [
                "Tier calculation order must be preserved: base -> tier 2 -> "
                "tier 3. Charges must never double-count units across tiers.",
                "Late fee cap at 25% for >90 days overdue must not be "
                "removed during modernization.",
                "Only active accounts may be billed. This is a compliance "
                "requirement, not just a filter.",
                "Error logging must not halt the batch — processing "
                "continues with next record.",
                "Billing date must be set to the actual processing date, "
                "not a hardcoded value.",
            ],
            "assumptions_and_ambiguities": {
                "observed": [
                    "Tier thresholds are loaded from RATE-FILE at program "
                    "start and do not change during execution.",
                    "The program processes all customers in a single "
                    "sequential pass.",
                    "Error records include the customer ID and a numeric "
                    "error code.",
                ],
                "inferred": [
                    "The 25% penalty cap appears to be a regulatory or "
                    "compliance safeguard, though no comment explains "
                    "the rationale.",
                    "COPY CUSTOMER-RECORD and COPY RATE-RECORD are standard "
                    "copybooks — field layouts inferred from variable naming "
                    "conventions.",
                ],
                "unknown": [
                    "Whether negative usage values are possible in production "
                    "data and how they should be handled.",
                    "Whether rate table can contain more than 3 tiers (the "
                    "code only references 3).",
                    "The exact file path or JCL configuration for "
                    "input/output files.",
                ],
            },
            "test_relevant_scenarios": [
                "Active customer with usage in tier 1 only: verify "
                "base-rate calculation.",
                "Active customer with usage spanning tiers 1 and 2: verify "
                "tier boundary math.",
                "Active customer with usage spanning all 3 tiers: verify "
                "cumulative calculation.",
                "Active customer with 0 usage: verify $0.00 record is "
                "produced.",
                "Customer with status 'S' (suspended): verify record is "
                "skipped and logged.",
                "Customer with status 'C' (closed): verify record is "
                "skipped and logged.",
                "Customer with empty CUST-ID: verify error logging.",
                "Payment 31 days overdue: verify penalty is applied.",
                "Payment exactly 30 days overdue: verify no penalty.",
                "Payment 91 days overdue: verify penalty is capped at 25%.",
                "Payment exactly 90 days overdue: verify standard penalty "
                "(not capped).",
                "Usage exactly at tier 2 threshold: verify boundary falls "
                "in lower tier.",
                "Multiple customers processed: verify batch continues past "
                "errors.",
            ],
            "confidence_assessment": {
                "level": "Medium",
                "rationale": (
                    "Core billing logic, tier calculations, and late-fee "
                    "rules are well-supported by the source code structure "
                    "and variable naming. However, two copybooks "
                    "(CUSTOMER-RECORD, RATE-RECORD) are referenced but not "
                    "provided, so field layouts are inferred. Negative usage "
                    "handling and extensibility beyond 3 tiers remain "
                    "unresolved."
                ),
            },
        }

    # ------------------------------------------------------------------
    # Coder mock
    # ------------------------------------------------------------------

    @staticmethod
    def _coder_response(run_version: int = 1) -> dict:
        """Realistic Coder output for the billing module."""
        
        prefix = ""
        if run_version > 1:
            prefix = f'# Modifying logic for run version {run_version}\n\n'
            
        generated_code = prefix + '''\
"""
Billing Calculator — modernized from COBOL BILL-CALC.

Implements tiered usage billing with late-payment penalties.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


class ErrorLogger(Protocol):
    """Protocol for error logging — batch must not halt on errors."""

    def log_error(self, customer_id: str, error_code: int, message: str) -> None:
        ...


@dataclass
class RateTable:
    """Tiered pricing configuration."""
    base_rate: float
    tier2_threshold: float
    tier2_rate: float
    tier3_threshold: float
    tier3_rate: float


@dataclass
class CustomerRecord:
    """Customer account details."""
    customer_id: str
    customer_name: str
    account_status: str  # 'A' = Active, 'S' = Suspended, 'C' = Closed


@dataclass
class UsageRecord:
    """Monthly usage for a customer."""
    customer_id: str
    monthly_usage_units: float


@dataclass
class PaymentHistory:
    """Payment history for penalty calculation."""
    customer_id: str
    days_overdue: int
    late_fee_percentage: float


@dataclass
class BillingSummary:
    """Output billing record."""
    customer_id: str
    customer_name: str
    subtotal: float
    penalty: float
    total_amount_due: float
    billing_date: date


class InMemoryErrorLogger:
    """Simple error logger that collects errors in memory."""

    def __init__(self) -> None:
        self.errors: list[dict] = []

    def log_error(self, customer_id: str, error_code: int, message: str) -> None:
        self.errors.append({
            "customer_id": customer_id,
            "error_code": error_code,
            "message": message,
        })


def validate_customer(customer: CustomerRecord) -> tuple[bool, int, str]:
    """
    Validate a customer record.

    Returns (is_valid, error_code, error_message).
    Only active accounts pass validation.
    """
    if not customer.customer_id or customer.customer_id.strip() == "":
        return False, 1001, "EMPTY CUSTOMER ID"
    if customer.account_status != "A":
        return False, 1002, "ACCOUNT NOT ACTIVE"
    return True, 0, ""


def calculate_tiered_charges(
    usage_units: float,
    rate_table: RateTable,
) -> tuple[float, float, float]:
    """
    Calculate charges across three pricing tiers.

    Tier order: base -> tier 2 -> tier 3.
    Units are never double-counted across tiers.
    Threshold value itself falls in the lower tier.
    """
    # Base tier: usage up to tier 2 threshold
    if usage_units <= rate_table.tier2_threshold:
        base_charges = usage_units * rate_table.base_rate
    else:
        base_charges = rate_table.tier2_threshold * rate_table.base_rate

    # Tier 2: usage between tier 2 and tier 3 thresholds
    tier2_charges = 0.0
    if usage_units > rate_table.tier2_threshold:
        tier2_units = min(
            usage_units - rate_table.tier2_threshold,
            rate_table.tier3_threshold - rate_table.tier2_threshold,
        )
        tier2_charges = tier2_units * rate_table.tier2_rate

    # Tier 3: usage above tier 3 threshold
    tier3_charges = 0.0
    if usage_units > rate_table.tier3_threshold:
        tier3_units = usage_units - rate_table.tier3_threshold
        tier3_charges = tier3_units * rate_table.tier3_rate

    return base_charges, tier2_charges, tier3_charges


def apply_late_penalty(
    subtotal: float,
    days_overdue: int,
    late_fee_percentage: float,
) -> float:
    """
    Apply late-payment penalty.

    - No penalty if days_overdue <= 30
    - Standard penalty if 30 < days_overdue <= 90
    - Capped at 25% of subtotal if days_overdue > 90
    """
    if days_overdue <= 30:
        return 0.0

    penalty = subtotal * late_fee_percentage

    if days_overdue > 90:
        cap = subtotal * 0.25
        if penalty > cap:
            penalty = cap

    return penalty


def process_billing(
    customers: list[CustomerRecord],
    usage_records: dict[str, UsageRecord],
    payment_history: dict[str, PaymentHistory],
    rate_table: RateTable,
    error_logger: ErrorLogger | None = None,
    billing_date: date | None = None,
) -> list[BillingSummary]:
    """
    Process billing for a batch of customers.

    Error logging does not halt the batch — processing continues
    with the next record.
    """
    if billing_date is None:
        billing_date = date.today()

    if error_logger is None:
        error_logger = InMemoryErrorLogger()

    results: list[BillingSummary] = []

    for customer in customers:
        is_valid, err_code, err_msg = validate_customer(customer)
        if not is_valid:
            error_logger.log_error(customer.customer_id, err_code, err_msg)
            continue

        usage = usage_records.get(customer.customer_id)
        usage_units = usage.monthly_usage_units if usage else 0.0

        base, tier2, tier3 = calculate_tiered_charges(usage_units, rate_table)
        subtotal = base + tier2 + tier3

        payment = payment_history.get(customer.customer_id)
        if payment:
            penalty = apply_late_penalty(
                subtotal, payment.days_overdue, payment.late_fee_percentage
            )
        else:
            penalty = 0.0

        total_due = subtotal + penalty

        results.append(BillingSummary(
            customer_id=customer.customer_id,
            customer_name=customer.customer_name,
            subtotal=subtotal,
            penalty=penalty,
            total_amount_due=total_due,
            billing_date=billing_date,
        ))

    return results
'''

        generated_tests = '''\
"""
Tests for the billing calculator.

Covers all critical constraints and major business rules from the Logic Map.
"""

import pytest
from datetime import date
from billing_calculator import (
    RateTable,
    CustomerRecord,
    UsageRecord,
    PaymentHistory,
    InMemoryErrorLogger,
    validate_customer,
    calculate_tiered_charges,
    apply_late_penalty,
    process_billing,
)


# --- Fixtures ---

@pytest.fixture
def rate_table():
    return RateTable(
        base_rate=0.10,
        tier2_threshold=1000.0,
        tier2_rate=0.08,
        tier3_threshold=5000.0,
        tier3_rate=0.05,
    )


@pytest.fixture
def billing_date():
    return date(2024, 3, 15)


# --- Critical Constraint Tests ---

class TestCriticalConstraints:
    """Tests that MUST pass — they gate the pipeline."""

    def test_tier_order_no_double_counting(self, rate_table):
        """Tier calculation: base -> tier2 -> tier3, no double-counting."""
        base, tier2, tier3 = calculate_tiered_charges(6000.0, rate_table)
        expected_base = 1000.0 * 0.10   # 100.0
        expected_tier2 = 4000.0 * 0.08  # 320.0
        expected_tier3 = 1000.0 * 0.05  # 50.0
        assert base == pytest.approx(expected_base)
        assert tier2 == pytest.approx(expected_tier2)
        assert tier3 == pytest.approx(expected_tier3)
        total = base + tier2 + tier3
        assert total == pytest.approx(470.0)

    def test_late_fee_cap_at_25_percent(self):
        """Late fee capped at 25% when >90 days overdue."""
        subtotal = 1000.0
        penalty = apply_late_penalty(subtotal, days_overdue=91, late_fee_percentage=0.50)
        assert penalty == pytest.approx(250.0)  # 25% cap

    def test_only_active_accounts_billed(self, rate_table, billing_date):
        """Suspended/closed accounts must not be billed."""
        customers = [
            CustomerRecord("C001", "Active User", "A"),
            CustomerRecord("C002", "Suspended User", "S"),
            CustomerRecord("C003", "Closed User", "C"),
        ]
        usage = {
            "C001": UsageRecord("C001", 500.0),
            "C002": UsageRecord("C002", 500.0),
            "C003": UsageRecord("C003", 500.0),
        }
        logger = InMemoryErrorLogger()
        results = process_billing(
            customers, usage, {}, rate_table,
            error_logger=logger, billing_date=billing_date,
        )
        billed_ids = [r.customer_id for r in results]
        assert "C001" in billed_ids
        assert "C002" not in billed_ids
        assert "C003" not in billed_ids

    def test_error_logging_does_not_halt_batch(self, rate_table, billing_date):
        """Errors must not stop processing of remaining records."""
        customers = [
            CustomerRecord("", "Bad User", "A"),     # invalid
            CustomerRecord("C002", "Good User", "A"),  # valid
        ]
        usage = {"C002": UsageRecord("C002", 100.0)}
        logger = InMemoryErrorLogger()
        results = process_billing(
            customers, usage, {}, rate_table,
            error_logger=logger, billing_date=billing_date,
        )
        assert len(results) == 1
        assert results[0].customer_id == "C002"
        assert len(logger.errors) == 1

    def test_billing_date_is_actual_processing_date(self, rate_table):
        """Billing date must be the actual processing date."""
        customers = [CustomerRecord("C001", "User", "A")]
        usage = {"C001": UsageRecord("C001", 100.0)}
        results = process_billing(customers, usage, {}, rate_table)
        assert results[0].billing_date == date.today()


# --- Business Rule Tests ---

class TestBusinessRules:
    """Tests for major business rules."""

    def test_tier1_only(self, rate_table):
        """Usage within tier 1 only."""
        base, tier2, tier3 = calculate_tiered_charges(500.0, rate_table)
        assert base == pytest.approx(50.0)
        assert tier2 == pytest.approx(0.0)
        assert tier3 == pytest.approx(0.0)

    def test_tier1_and_tier2(self, rate_table):
        """Usage spanning tiers 1 and 2."""
        base, tier2, tier3 = calculate_tiered_charges(3000.0, rate_table)
        assert base == pytest.approx(100.0)   # 1000 * 0.10
        assert tier2 == pytest.approx(160.0)  # 2000 * 0.08
        assert tier3 == pytest.approx(0.0)

    def test_penalty_at_31_days(self):
        """Penalty applies at >30 days overdue."""
        penalty = apply_late_penalty(1000.0, days_overdue=31, late_fee_percentage=0.10)
        assert penalty == pytest.approx(100.0)

    def test_no_penalty_at_30_days(self):
        """No penalty at exactly 30 days."""
        penalty = apply_late_penalty(1000.0, days_overdue=30, late_fee_percentage=0.10)
        assert penalty == pytest.approx(0.0)

    def test_zero_usage_produces_record(self, rate_table, billing_date):
        """Zero-usage customer still gets a $0 billing record."""
        customers = [CustomerRecord("C001", "User", "A")]
        usage = {"C001": UsageRecord("C001", 0.0)}
        results = process_billing(
            customers, usage, {}, rate_table, billing_date=billing_date,
        )
        assert len(results) == 1
        assert results[0].total_amount_due == pytest.approx(0.0)


# --- Edge Case Tests ---

class TestEdgeCases:
    """Tests for boundary conditions."""

    def test_usage_exactly_at_tier2_boundary(self, rate_table):
        """Threshold value falls in the lower tier."""
        base, tier2, tier3 = calculate_tiered_charges(1000.0, rate_table)
        assert base == pytest.approx(100.0)  # 1000 * 0.10
        assert tier2 == pytest.approx(0.0)

    def test_penalty_at_exactly_90_days(self):
        """At exactly 90 days, standard penalty (not capped)."""
        penalty = apply_late_penalty(1000.0, days_overdue=90, late_fee_percentage=0.50)
        assert penalty == pytest.approx(500.0)  # not capped

    def test_empty_customer_id_validation(self):
        """Empty customer ID is a validation failure."""
        is_valid, code, msg = validate_customer(
            CustomerRecord("", "Bad User", "A")
        )
        assert not is_valid
        assert code == 1001
'''

        return {
            "generated_code": generated_code,
            "generated_tests": generated_tests,
            "implementation_choices": (
                "Used dataclasses for data structures to match the COBOL record "
                "layout style while being idiomatic Python. The ErrorLogger is "
                "defined as a Protocol to allow flexible logging backends without "
                "coupling to a specific implementation. Tier calculation is split "
                "into a pure function (calculate_tiered_charges) to make the "
                "no-double-counting constraint testable in isolation. The batch "
                "processor (process_billing) continues on errors per the critical "
                "constraint that error logging must not halt the batch."
            ),
            "logic_step_mapping": [
                {
                    "function_or_test_name": "validate_customer",
                    "logic_step": "4. Validate the customer record",
                    "notes": "Returns tuple for error code propagation",
                },
                {
                    "function_or_test_name": "calculate_tiered_charges",
                    "logic_step": "6-9. Calculate base, tier 2, tier 3, and sum",
                    "notes": "Pure function covering steps 6 through 9",
                },
                {
                    "function_or_test_name": "apply_late_penalty",
                    "logic_step": "10. Check payment history and apply penalty",
                    "notes": "Includes the 25% cap for >90 days overdue",
                },
                {
                    "function_or_test_name": "process_billing",
                    "logic_step": "1-3, 11-12. Main batch loop",
                    "notes": (
                        "File I/O replaced with in-memory data structures; "
                        "the sequential processing pattern is preserved"
                    ),
                },
            ],
            "deferred_items": [
                "Negative usage handling: Logic Map marks this as unknown. "
                "No guard added; deferred for clarification.",
                "File I/O: Original COBOL uses sequential/indexed files. "
                "Replaced with in-memory structures; actual I/O adapters "
                "are out of scope for the code generation stage.",
            ],
        }

    # ------------------------------------------------------------------
    # Reviewer mock
    # ------------------------------------------------------------------

    @staticmethod
    def _reviewer_response(run_version: int = 1) -> dict:
        """Realistic Reviewer output for the generated Coder output."""
        return {
            "logic_parity_findings": (
                "The generated code correctly implements all five critical "
                "constraints and all seven business rules from the Logic Map. "
                "Tier calculation preserves the base -> tier 2 -> tier 3 order "
                "without double-counting. The 25% late-fee cap is correctly "
                "applied only when days_overdue > 90. Only active accounts are "
                "billed, and error logging does not halt the batch. The billing "
                "date defaults to the actual processing date."
            ),
            "defects": [
                {
                    "description": "Missing module docstring on tests",
                    "severity": "minor",
                    "logic_step": "",
                    "suggested_fix": "Add a descriptive docstring to test_modernized.py"
                }
            ],
            "suggested_corrections": [],
            "passed": True,
            "confidence": {
                "level": "Medium",
                "rationale": (
                    "All critical constraints and business rules are correctly "
                    "implemented and tested. However, two items are deferred "
                    "(negative usage, file I/O) and copybook layouts are inferred "
                    "rather than confirmed. Overall logic parity is strong."
                ),
            },
            "known_limitations": [
                "Negative usage values are not guarded against; behavior is "
                "undefined per the Logic Map.",
                "File I/O is replaced with in-memory structures; production "
                "deployment requires I/O adapters.",
                "Copybook field layouts (CUSTOMER-RECORD, RATE-RECORD) are "
                "inferred, not confirmed from source artifacts.",
            ],
        }

