"""
Error handling tests for the LegacyLens pipeline.

Covers failure-path behavior: Coder repeated ValidationError, Reviewer
failure, scoring failure, happy-path errors==[], partial-result disk
persistence, and API failure-path verification.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.contracts import ConfidenceLevel, PipelineError
from backend.pipeline import run_pipeline
from backend.provider import LLMProvider, MockProvider


# ---------------------------------------------------------------------------
# Helpers: failing providers
# ---------------------------------------------------------------------------

class _CoderFailProvider(LLMProvider):
    """Provider that returns valid analyst/reviewer output but raises
    ValidationError on every coder call."""

    _mock = MockProvider()

    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        if "Coder Agent" in system_prompt:
            # Force a ValidationError by returning data missing required fields
            raise ValidationError.from_exception_data(
                title="CoderOutput",
                line_errors=[
                    {
                        "type": "missing",
                        "loc": ("generated_code",),
                        "msg": "Field required",
                        "input": {},
                    }
                ],
            )
        return self._mock.generate(system_prompt, user_prompt, schema)


class _ReviewerFailProvider(LLMProvider):
    """Provider that returns valid analyst/coder output but raises on
    the reviewer call."""

    _mock = MockProvider()

    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        if "Reviewer Agent" in system_prompt:
            raise RuntimeError("Simulated reviewer crash")
        return self._mock.generate(system_prompt, user_prompt, schema)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "samples" / "sample.cbl"


@pytest.fixture
def tmp_output(tmp_path):
    """Provide a clean temp directory for run history output."""
    return tmp_path / "runs"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Failure-path tests for the procedural pipeline."""

    def test_happy_path_has_empty_errors(self, tmp_output):
        """Standard mock run should produce zero errors."""
        result = run_pipeline(
            source_path=SAMPLE_PATH,
            provider_name="mock",
            output_dir=str(tmp_output),
        )
        assert result.errors == []
        assert result.coder_output is not None
        assert result.reviewer_output is not None

    def test_coder_repeated_validation_error_exhausts_iterations(self, tmp_output):
        """Coder raises ValidationError on every call. Pipeline retries 3
        times, then returns a partial result with logic_map but no coder output."""
        provider = _CoderFailProvider()

        # Inject the failing provider into the pipeline by patching provider selection
        with patch("backend.pipeline.MockProvider", return_value=provider):
            result = run_pipeline(
                source_path=SAMPLE_PATH,
                provider_name="mock",
                output_dir=str(tmp_output),
            )

        # Logic map should be populated (analyst succeeded)
        assert result.logic_map is not None
        assert len(result.logic_map.business_rules) > 0

        # Coder failed on all iterations → no coder output
        assert result.coder_output is None

        # Reviewer never ran → no reviewer output
        assert result.reviewer_output is None

        # Should have 3 errors (one per iteration)
        assert len(result.errors) == 3
        for i, err in enumerate(result.errors):
            assert err.stage == "coder"
            assert err.error_type == "ValidationError"
            assert err.recoverable is True
            assert err.iteration == i + 1

        # iterations should reflect all 3 attempts
        assert result.iterations == 3

    def test_reviewer_failure_preserves_coder_output(self, tmp_output):
        """Reviewer crashes. Result should have coder_output but no
        reviewer_output, with a structured error logged."""
        provider = _ReviewerFailProvider()

        with patch("backend.pipeline.MockProvider", return_value=provider):
            result = run_pipeline(
                source_path=SAMPLE_PATH,
                provider_name="mock",
                output_dir=str(tmp_output),
            )

        # Analyst and Coder succeeded
        assert result.logic_map is not None
        assert result.coder_output is not None

        # Reviewer failed
        assert result.reviewer_output is None

        # Error should be logged
        assert len(result.errors) >= 1
        reviewer_err = result.errors[0]
        assert reviewer_err.stage == "reviewer"
        assert reviewer_err.error_type == "RuntimeError"
        assert reviewer_err.recoverable is False

    def test_scoring_failure_uses_fallback_confidence(self, tmp_output):
        """If aggregate_confidence raises, pipeline uses fallback Low
        confidence and logs the error."""
        with patch(
            "backend.pipeline.aggregate_confidence",
            side_effect=RuntimeError("Simulated scoring crash"),
        ):
            result = run_pipeline(
                source_path=SAMPLE_PATH,
                provider_name="mock",
                output_dir=str(tmp_output),
            )

        # Pipeline should still complete
        assert result.logic_map is not None
        assert result.coder_output is not None
        assert result.reviewer_output is not None

        # Confidence should be fallback Low
        assert result.final_confidence.level == ConfidenceLevel.LOW
        assert "Scoring failed" in result.final_confidence.rationale

        # Error logged
        scoring_errors = [e for e in result.errors if e.stage == "scoring"]
        assert len(scoring_errors) == 1
        assert scoring_errors[0].recoverable is True

    def test_partial_result_persists_to_disk(self, tmp_output):
        """After coder failure, run history should contain logic_map.json
        and errors.json but NOT modernized.py."""
        provider = _CoderFailProvider()

        with patch("backend.pipeline.MockProvider", return_value=provider):
            result = run_pipeline(
                source_path=SAMPLE_PATH,
                provider_name="mock",
                output_dir=str(tmp_output),
            )

        # Find the run directory
        run_dirs = list(tmp_output.glob("*"))
        assert len(run_dirs) == 1, f"Expected 1 run dir, found {len(run_dirs)}"
        run_dir = run_dirs[0]

        # logic_map always written
        assert (run_dir / "logic_map.json").exists()
        assert (run_dir / "logic_map.md").exists()

        # errors.json always written and non-empty
        import json
        errors_data = json.loads((run_dir / "errors.json").read_text())
        assert len(errors_data) > 0

        # modernized.py NOT written (coder failed)
        assert not (run_dir / "modernized.py").exists()
        assert not (run_dir / "test_modernized.py").exists()

        # confidence.json always written
        assert (run_dir / "confidence.json").exists()

        # pipeline_result.json always written
        assert (run_dir / "pipeline_result.json").exists()


class TestAPIErrorHandling:
    """Failure-path test for the FastAPI server."""

    def test_api_failure_returns_structured_errors(self):
        """POST a job with a provider that fails at the coder stage.
        GET should return structured errors."""
        import time
        from fastapi.testclient import TestClient

        # Patch the server's provider to use the failing one
        with patch("backend.server.provider", _CoderFailProvider()):
            # Re-build the graph and server objects with the failing provider
            from backend.server import app, analyst, coder, reviewer
            from backend.graph import build_pipeline_graph

            failing_provider = _CoderFailProvider()
            patched_analyst = type(analyst)(failing_provider)
            patched_coder = type(coder)(failing_provider)
            patched_reviewer = type(reviewer)(failing_provider)

            with patch("backend.server.pipeline_graph",
                        build_pipeline_graph(patched_analyst, patched_coder, patched_reviewer)):
                client = TestClient(app)
                
                # Setup Auth
                client.post("/api/v1/auth/register", json={"username": "apifailuser", "password": "password"})
                client.post("/api/v1/auth/login", data={"username": "apifailuser", "password": "password"})

                # Submit job
                with open(SAMPLE_PATH, "rb") as f:
                    response = client.post(
                        "/api/v1/jobs",
                        files={"file": ("sample.cbl", f.read(), "text/plain")},
                    )
                assert response.status_code == 200
                job_id = response.json()["job_id"]

                # Poll until done
                max_polls = 20
                for _ in range(max_polls):
                    res = client.get(f"/api/v1/jobs/{job_id}")
                    assert res.status_code == 200
                    data = res.json()
                    if data["status"] in ("completed", "completed_with_errors", "failed"):
                        break
                    time.sleep(0.05)

                # Verify structured errors returned
                assert data["status"] == "completed_with_errors", \
                    f"Expected 'completed_with_errors', got '{data['status']}'"
                assert len(data["errors"]) > 0
                assert data["errors"][0]["stage"] == "coder"
                # Partial result should include logic_map
                assert data["result"] is not None
                assert "logic_map" in data["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
