import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def run_tests():
    print("--- 1. Testing Jobs API ---")
    jobs_resp = requests.get(f"{BASE_URL}/jobs")
    if jobs_resp.status_code == 200:
        jobs_data = jobs_resp.json()
        jobs = jobs_data.get("jobs", [])
        print(f"Success: Fetched {len(jobs)} jobs.")
        if jobs:
            print(f"   Sample Job Title: {jobs[0].get('title')}")
            print(f"   New Fields: work_mode={jobs[0].get('work_mode')}, responsibilities={len(jobs[0].get('responsibilities', []))} items")
    else:
        print(f"Failed to fetch jobs: {jobs_resp.text}")
        sys.exit(1)

    print("\n--- 2. Testing Candidate Async Ingestion (Phase H) ---")
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "github_url": "https://github.com/pro-npc",
        "linkedin_text": "Experienced software engineer with a passion for web development and AI.",
        "projects": []
    }
    
    cand_resp = requests.post(f"{BASE_URL}/candidates", json=payload)
    if cand_resp.status_code == 202:
        cand_data = cand_resp.json()
        cand_id = cand_data.get("candidate_id")
        status = cand_data.get("graph_status")
        print(f"Success: Candidate created with ID {cand_id}, Initial Status: {status}")
        
        print("   Polling for completion...")
        max_attempts = 15
        for i in range(max_attempts):
            poll_resp = requests.get(f"{BASE_URL}/candidates/{cand_id}")
            if poll_resp.status_code == 200:
                poll_data = poll_resp.json()
                current_status = poll_data.get("graph_status")
                print(f"   [Attempt {i+1}] Status: {current_status}")
                if current_status == "ready":
                    print(f"Success: Graph built asynchronously!")
                    print(f"   Projects ingested: {len(poll_data.get('projects', []))}")
                    if poll_data.get('projects'):
                        print(f"   First project: {poll_data['projects'][0].get('name')}")
                        print(f"   Files in project: {len(poll_data['projects'][0].get('files', []))}")
                    break
                elif current_status == "failed":
                    print(f"Async task failed: {poll_data}")
                    break
            else:
                print(f"Polling failed: {poll_resp.text}")
                break
            time.sleep(2)
        else:
            print("Timed out waiting for async task.")
    else:
        print(f"Failed to create candidate: {cand_resp.status_code} {cand_resp.text}")
        
if __name__ == "__main__":
    run_tests()
