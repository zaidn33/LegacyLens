"""
LLM provider abstraction with swappable implementations.

Ships with:
  - GraniteProvider  — IBM Granite 4.0 (primary, requires API key)
  - MockProvider     — deterministic stub for development & CI
"""

from __future__ import annotations

import os
import json
from abc import ABC, abstractmethod
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential


class LLMProvider(ABC):
    """Abstract base class — implement ``generate`` for each backend."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> dict:
        """Return a parsed JSON dict conforming to *schema*."""
        ...


# ---------------------------------------------------------------------------
# Granite (production)
# ---------------------------------------------------------------------------

class GraniteProvider(LLMProvider):
    """
    IBM Granite 4.0 provider (via OpenAI compatible endpoint).

    Handles rate limits, timeouts, and malformed JSON via tenacity retries
    and explicit error mapping.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "granite-3.0-8b-instruct",
    ):
        self.api_key = api_key or os.environ.get("GRANITE_API_KEY", "dummy-local-key")
        self.base_url = base_url or os.environ.get("OPENAI_API_BASE", "http://localhost:11434/v1")
        self.model = model

        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("langchain-openai is required for GraniteProvider")

        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            max_retries=0,  # Let tenacity handle it
            temperature=0.0,
        )

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
    ) -> dict:
        from langchain_core.messages import SystemMessage, HumanMessage
        import httpx
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        structured_llm = self.llm.with_structured_output(schema)

        try:
            result = structured_llm.invoke(messages)
            if not result:
                raise ValueError("LLM returned empty or malformed output")
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse structured JSON output: {e}")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Provider HTTP error {e.response.status_code}: {e}")
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
    ) -> dict:
        if self._mock_response is not None:
            return self._mock_response

        # Route based on system prompt identity
        # Route based on system prompt identity
        if "Legacy Logic Architect" in system_prompt:
            is_multi_file = "Auxiliary Dependency Files Provided" in user_prompt
            return self._analyst_response(is_multi_file)
        elif "Coder Agent" in system_prompt:
            return self._coder_response()
        elif "Reviewer Agent" in system_prompt:
            return self._reviewer_response()
        else:
            return self._analyst_response(False)  # fallback

    # ------------------------------------------------------------------
    # Analyst mock
    # ------------------------------------------------------------------

    @staticmethod
    def _analyst_response(is_multi_file: bool = False) -> dict:
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
    def _coder_response() -> dict:
        """Realistic Coder output for the billing module."""
        generated_code = '''\
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
    def _reviewer_response() -> dict:
        """Realistic Reviewer output — passes on first review."""
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

