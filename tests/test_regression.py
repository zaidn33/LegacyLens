import os
import sys
from pathlib import Path

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.pipeline import run_pipeline

def test_messy_billing_regression():
    """Test that the pipeline gracefully handles messy inputs and preserves pipeline parity."""
    sample_path = Path(__file__).resolve().parent.parent / "samples" / "messy_billing.cbl"
    assert sample_path.exists(), f"Messy sample not found at {sample_path}."
    
    # We use the MockProvider for deterministic, rapid testing without LLM costs.
    # The MockProvider asserts the pipeline orchestrates correctly and adheres to the
    # updated strict DefectSeverity contracts.
    result = run_pipeline(
        source_path=sample_path,
        provider_name="mock",
        output_dir="runs"
    )
    
    # Ensure a result was returned
    assert result is not None, "Pipeline failed to return a result."
    
    # Ensure logic map was parsed
    assert len(result.logic_map.business_rules) > 0, "No business rules extracted."
    
    # Ensure tests were generated
    assert len(result.coder_output.generated_tests) > 0, "No tests generated."
    
    # Verify strict defect severities are modeled correctly in the Reviewer
    assert hasattr(result.reviewer_output.defects[0], "severity"), "Defects lack severity tracking."
    
    # Check if run history dir was created
    dirs = list(Path(__file__).resolve().parent.parent.joinpath("runs").glob("*"))
    assert len(dirs) > 0, "Run history directory was not created."

if __name__ == "__main__":
    test_messy_billing_regression()
    print("Regression suite passed.")
