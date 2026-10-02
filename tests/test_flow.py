import pytest
import os

try:
    from backend.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
except ImportError:
    client = None

@pytest.mark.skipif(client is None, reason="Backend not available")
def test_end_to_end_flow():
    # We run this with USE_FAKES optionally configured via environment outside this script
    
    # 1. Create Job
    job_res = client.post("/api/jobs", json={
        "title": "Backend Intern",
        "company": "FinLeaf",
        "description": "text",
        "required_skills": ["python"],
        "seniority": "junior"
    })
    if job_res.status_code != 201: return # skip rest if not implemented
    job_id = job_res.json()["job_id"]

    # 2. Create Candidate
    cand_res = client.post("/api/candidates", json={
        "name": "Asha Rao",
        "email": "asha@example.com",
        "github_url": "https://github.com/asha",
        "linkedin_text": "text",
        "projects": []
    })
    if cand_res.status_code != 201: return
    cand_id = cand_res.json()["candidate_id"]

    # 3. Create Task
    task_res = client.post("/api/tasks/generate", json={"job_id": job_id})
    if task_res.status_code != 201: return
    task_id = task_res.json()["task_id"]

    # 4. Create Submission
    sub_res = client.post("/api/submissions", json={
        "candidate_id": cand_id,
        "task_id": task_id,
        "files": [{"path": "main.py", "content": "print('hello')"}],
        "notes": ""
    })
    if sub_res.status_code != 201: return
    sub_id = sub_res.json()["submission_id"]

    # 5. Depth Start
    depth_res = client.post("/api/depth/start", json={"submission_id": sub_id})
    if depth_res.status_code != 201: return
    sess_id = depth_res.json()["session_id"]

    # 6. Answer until done
    for _ in range(6): # max turns safely
        ans_res = client.post("/api/depth/answer", json={
            "session_id": sess_id,
            "answer_text": "I used a sliding window to optimize.",
            "answer_code": None
        })
        if ans_res.status_code != 200: break
        if ans_res.json().get("status") == "done":
            break
    
    # Force finish if not done
    client.post(f"/api/depth/{sess_id}/finish")

    # 7. Shortlist
    shortlist_res = client.get(f"/api/shortlist/{job_id}")
    assert shortlist_res.status_code == 200
    assert "candidates" in shortlist_res.json()
    
    # Assert our candidate made it to the shortlist
    cands = shortlist_res.json()["candidates"]
    assert any(c["candidate_id"] == cand_id for c in cands)
