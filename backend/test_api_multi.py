from backend.pipeline import run_pipeline

if __name__ == "__main__":
    with open("samples/definitions.cpy", "r", encoding="utf-8") as f:
        copy_text = f.read()

    deps = {"definitions.cpy": copy_text}
    
    print("Executing Multi-File Code Modernization Pipeline natively...")
    res = run_pipeline(
        source_path="samples/main_routine.cbl",
        provider_name="mock",
        output_dir="runs/test_multi",
        dependencies_dict=deps
    )
    
    print("\n--- Pipeline Result Struct ---")
    print(f"Dependencies mapped: {len(res.logic_map.dependencies)}")
    for d in res.logic_map.dependencies:
        print(f"  - {d.reference_name} -> {d.status} ({d.resolved_filename})")
        
    print(f"Outputs Built: {res.coder_output is not None}")
    print(f"Reviewer Passed: {res.reviewer_output.passed if res.reviewer_output else False}")
    print(f"Total Iterations: {res.iterations}")
