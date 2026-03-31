import time
from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_phase7_lineage_and_diff():
    # 1. Create a parent job
    response = client.post(
        "/api/v1/jobs",
        files={"file": ("test.cbl", b"IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.")}
    )
    assert response.status_code == 200
    job_1_id = response.json()["job_id"]
    
    # Wait for completion (background tasks run concurrently in tests depending on runner, 
    # but Starlette TestClient might process them synchronously or requires polling)
    # Using real polling to be safe
    for _ in range(10):
        s1 = client.get(f"/api/v1/jobs/{job_1_id}").json()
        if s1["status"] in ["completed", "failed"]:
            break
        time.sleep(1)
        
    assert s1["status"] == "completed", f"Job 1 did not complete: {s1}"
    assert s1["run_version"] == 1
    
    # 3. Create a rerun job
    response2 = client.post(f"/api/v1/jobs/{job_1_id}/rerun")
    assert response2.status_code == 200
    job_2_id = response2.json()["job_id"]
    
    # 4. Poller for job 2
    for _ in range(10):
        s2 = client.get(f"/api/v1/jobs/{job_2_id}").json()
        if s2["status"] in ["completed", "failed"]:
            break
        time.sleep(1)
        
    assert s2["status"] == "completed", f"Job 2 did not complete: {s2}"
    assert s2["run_version"] == 2
    assert s2["parent_job_id"] == job_1_id
    
    # 5. History logic
    h_resp = client.get(f"/api/v1/jobs/{job_1_id}/history")
    assert h_resp.status_code == 200
    history = h_resp.json()["history"]
    assert len(history) == 2
    
    versions = [h["run_version"] for h in history]
    assert 1 in versions
    assert 2 in versions
    
    # 6. Diff response
    diff_resp = client.get(f"/api/v1/jobs/{job_1_id}/diff/{job_2_id}")
    assert diff_resp.status_code == 200
    diff = diff_resp.json()
    
    assert diff["code_delta"]["changed"] is True
    assert diff["code_delta"]["lines_after"] > diff["code_delta"]["lines_before"]
