"""
Test script to exercise the FastAPI server endpoints.
"""
from fastapi.testclient import TestClient
import time

from backend.server import app

client = TestClient(app)

def test_api_e2e():
    # Load sample COBOL file
    with open("samples/sample.cbl", "rb") as f:
        file_content = f.read()

    # Submit job (POST /api/v1/jobs)
    response = client.post(
        "/api/v1/jobs",
        files={"file": ("sample.cbl", file_content, "text/plain")}
    )
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "processing"
    
    job_id = data["job_id"]
    print(f"\nSpawned Job ID: {job_id}")
    
    # Poll job status (GET /api/v1/jobs/{job_id})
    max_polls = 10
    attempts = 0
    final_result = None
    
    while attempts < max_polls:
        res = client.get(f"/api/v1/jobs/{job_id}")
        assert res.status_code == 200, res.text
        
        status_data = res.json()
        print(f"Poll {attempts+1}: status={status_data['status']}, node={status_data.get('current_node')}, iterative={status_data.get('iteration')}")
        
        if status_data["status"] == "completed":
            final_result = status_data["result"]
            break
        elif status_data["status"] == "failed":
            raise RuntimeError(f"Job failed: {status_data.get('error')}")
            
        # Give the background task time to run (in a real TestClient loop, background tasks fire inline or instantly depending on runner, but time.sleep allows yielding if any real threads are used)
        # Note: TestClient runs BackgroundTasks immediately by default upon response return.
        time.sleep(0.1) 
        attempts += 1
        
    assert final_result is not None, "Pipeline did not complete."
    assert "logic_map" in final_result
    assert "coder_output" in final_result
    assert "reviewer_output" in final_result
    assert final_result["reviewer_output"]["passed"] is True
    print("\nAPI Test PASSED. Pipeline result accurately returned via endpoint.")

if __name__ == "__main__":
    test_api_e2e()
