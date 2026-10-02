import requests
import time

BASE_URL = "http://localhost:8000/api"

def test_flow():
    print("--- Starting End-to-End Test for Ankush Sharma ---")
    
    # 1. Verify Jobs
    print("1. Fetching jobs...")
    res = requests.get(f"{BASE_URL}/jobs")
    jobs = res.json().get("jobs", [])
    print(f"   Found {len(jobs)} jobs: {[j['title'] for j in jobs]}")
    if not jobs:
        print("   No jobs found, failing.")
        return
    job_id = jobs[0]["job_id"]
    
    # 2. Create Candidate
    print("2. Creating Candidate (Ankush Sharma)...")
    cand_payload = {
        "name": "Ankush Sharma",
        "email": "ankush@example.com",
        "github_url": "https://github.com/ankush-sharma",
        "linkedin_text": "I am a skilled software engineer experienced in Python and modern web development.",
        "projects": [
            {
                "name": "E-Commerce Backend",
                "description": "A scalable backend for an e-commerce platform.",
                "files": [
                    {
                        "path": "app.py",
                        "content": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}"
                    }
                ]
            }
        ]
    }
    res = requests.post(f"{BASE_URL}/candidates", json=cand_payload)
    cand_data = res.json()
    candidate_id = cand_data.get("candidate_id")
    print(f"   Created candidate: {candidate_id}")
    print(f"   Graph summary: {cand_data.get('graph_summary')}")
    
    # 3. Generate Task
    print(f"3. Generating Task for Job {job_id}...")
    res = requests.post(f"{BASE_URL}/tasks/generate", json={"job_id": job_id})
    task_data = res.json()
    task_id = task_data.get("task_id")
    print(f"   Generated task: {task_data.get('title')} (ID: {task_id})")
    
    # 4. Submit Solution
    print("4. Submitting Solution...")
    sub_payload = {
        "candidate_id": candidate_id,
        "task_id": task_id,
        "notes": "Here is my implementation using FastAPI.",
        "files": [
            {
                "path": "solution.py",
                "content": "def main(): print('Hello Ankush')"
            }
        ]
    }
    res = requests.post(f"{BASE_URL}/submissions", json=sub_payload)
    sub_data = res.json()
    submission_id = sub_data.get("submission_id")
    print(f"   Submitted solution: {submission_id}")
    
    # 5. Start Depth Check
    print("5. Starting Depth Check Session...")
    res = requests.post(f"{BASE_URL}/depth/start", json={"submission_id": submission_id})
    session_data = res.json()
    session_id = session_data.get("session_id")
    turn = session_data.get("turn")
    print(f"   Started session: {session_id}")
    print(f"   First Question: {turn.get('text')}")
    
    # 6. Answer Question
    print("6. Submitting Answer...")
    ans_payload = {
        "session_id": session_id,
        "answer_text": "I used FastAPI because it is very fast and asynchronous.",
        "answer_code": None
    }
    res = requests.post(f"{BASE_URL}/depth/answer", json=ans_payload)
    ans_data = res.json()
    print(f"   Answer Result Score: {ans_data.get('evaluation', {}).get('score')}/5")
    print(f"   Running Confidence: {ans_data.get('running', {}).get('confidence')}")
    
    # 7. Finish Depth Check
    print("7. Finishing Depth Check...")
    res = requests.post(f"{BASE_URL}/depth/finish", json={"session_id": session_id})
    print(f"   Finish status: {res.status_code}")
    
    # 8. Get Profile Outcome (Shortlist)
    print("8. Fetching Shortlist...")
    res = requests.get(f"{BASE_URL}/jobs/{job_id}/shortlist")
    shortlist_data = res.json()
    cands = shortlist_data.get("candidates", [])
    print(f"   Shortlist contains {len(cands)} candidates.")
    for cand in cands:
        if cand.get("name") == "Ankush Sharma":
            print("   ---> Ankush Sharma Profile Generated Successfully!")
            print(f"   Score: {cand.get('overall_score')}/100")
            print(f"   Recommendation: {cand.get('recommendation')}")
            print(f"   Summary: {cand.get('summary')}")
            print(f"   Evidence length: {len(cand.get('evidence', []))}")
            print("--- End of Test ---")
            return
    print("   Profile not found in shortlist.")

if __name__ == "__main__":
    test_flow()
