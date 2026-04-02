import pytest
import sys
from pathlib import Path

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

def test_auth_flow():
    # 1. Register works
    resp1 = client.post("/api/v1/auth/register", json={"username": "flow_user", "password": "flow_password"})
    assert resp1.status_code == 200, resp1.text

    # 2. Login works and returns HttpOnly cookie
    resp2 = client.post("/api/v1/auth/login", data={"username": "flow_user", "password": "flow_password"})
    assert resp2.status_code == 200, resp2.text
    
    # Verify Cookie behavior
    cookie_header = resp2.headers.get("set-cookie", "")
    assert "access_token=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
    
    # 3. /me works
    # TestClient persists cookies automatically for subsequent requests
    resp3 = client.get("/api/v1/auth/me")
    assert resp3.status_code == 200, resp3.text
    assert resp3.json()["username"] == "flow_user"

    # 4. protected routes reject unauthenticated
    client.cookies.clear() # Simulate logout / no cookie
    resp4 = client.get("/api/v1/auth/me")
    assert resp4.status_code == 401

    # check jobs route
    resp5 = client.get("/api/v1/jobs")
    assert resp5.status_code == 401
    
    # 5. Logout works
    client.post("/api/v1/auth/login", data={"username": "flow_user", "password": "flow_password"}) # re-login
    resp6 = client.post("/api/v1/auth/logout")
    assert resp6.status_code == 200
    # Cookie should be cleared by having Max-Age=0 or something similar
    logout_cookie = resp6.headers.get("set-cookie", "")
    assert 'access_token=""' in logout_cookie or "Max-Age=0" in logout_cookie or "expires" in logout_cookie


def test_multi_user_isolation():
    # Register Alice and Bob
    client.post("/api/v1/auth/register", json={"username": "alice", "password": "pwd"})
    client.post("/api/v1/auth/register", json={"username": "bob", "password": "pwd"})

    # Login Alice
    client.post("/api/v1/auth/login", data={"username": "alice", "password": "pwd"})
    
    import pathlib
    # Have Alice submit a job
    sample_path = pathlib.Path(__file__).parent.parent / "samples" / "sample.cbl"
    with open(sample_path, "rb") as f:
        resp_a = client.post(
            "/api/v1/jobs",
            files={"file": ("sample.cbl", f.read(), "text/plain")},
        )
    assert resp_a.status_code == 200
    alice_job_id = resp_a.json()["job_id"]
    
    # Alice can see it
    resp_b = client.get(f"/api/v1/jobs/{alice_job_id}")
    assert resp_b.status_code == 200

    # Bob logs in
    client.cookies.clear()
    client.post("/api/v1/auth/login", data={"username": "bob", "password": "pwd"})

    # Bob cannot see Alice's job
    resp_c = client.get(f"/api/v1/jobs/{alice_job_id}")
    assert resp_c.status_code == 404 # Enforced by db.py returning None!

    # Bob lists jobs, should be empty
    resp_d = client.get("/api/v1/jobs")
    assert resp_d.status_code == 200
    assert len(resp_d.json()["jobs"]) == 0

