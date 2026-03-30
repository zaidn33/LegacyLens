from backend.pipeline import run_pipeline
import json

if __name__ == "__main__":
    print("Executing Pipeline with deliberately missing dependencies...")
    res = run_pipeline(
        source_path="samples/main_routine.cbl",
        provider_name="mock",
        output_dir="runs/test_missing",
        dependencies_dict={}  # Empty dependencies
    )
    
    print("\n--- Pipeline Result Struct ---")
    print(f"Dependencies mapped: {len(res.logic_map.dependencies)}")
    for d in res.logic_map.dependencies:
        print(f"  - {d.reference_name} -> {d.status} ({d.resolved_filename})")
    
    print(f"\nReviewer Output: {res.reviewer_output.logic_parity_findings if res.reviewer_output else 'None'}")
    print(f"Reviewer Passed: {res.reviewer_output.passed if res.reviewer_output else False}")
