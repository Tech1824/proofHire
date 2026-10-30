import json
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.main import app
    client = TestClient(app)
except Exception as e:
    print(f"Error loading app: {e}")
    sys.exit(1)

client.post("/api/config/demo-mode", json={"enabled": False})

print("1. Creating Job")
job_res = client.post("/api/jobs", json={
    "title": "Cybersecurity / OSINT Analyst",
    "company": "SecureHire",
    "description": "Looking for someone to investigate digital footprints and find flaws.",
    "required_skills": ["osint", "cybersecurity", "penetration testing"],
    "seniority": "junior"
})
if job_res.status_code != 201:
    print("Job Failed:", job_res.text)
    sys.exit(1)
job_id = job_res.json()["job_id"]
print(f"Job created: {job_id}")

print("2. Creating Candidate")
cand_res = client.post("/api/candidates", json={
    "name": "pro-npc",
    "email": "pro@example.com",
    "github_url": "https://github.com/pro-npc",
    "linkedin_text": """I am a cybersecurity student and OSINT enthusiast who loves the mechanics of hacking—understanding systems, finding their flaws, and learning how to secure them responsibly.
I spend my free time diving into cybercrime investigation, digital forensics, and AI Red Teaming. I love the thrill of learning, whether that means analyzing a digital footprint, solving a complex CTF challenge, or exploring new security concepts.
My goal is to keep improving my technical skills so I can ethically support digital investigations, raise cybersecurity awareness, and help make the internet a safer place.

Top skills
Source Intelligence
Experience
[OSINT InvestigatorFreelanceJul 2026 - Present · 4 mosRemote]
[Penetration TesterFreelanceJan 2026 - Present · 10 mos]
[Bug Bounty LearnerFreelance · FreelanceSep 2025 - Present · 1 yr 2 mos]""",
    "projects": []
})
if cand_res.status_code != 201:
    print("Candidate Failed:", cand_res.text)
    sys.exit(1)
cand_id = cand_res.json()["candidate_id"]
print("Candidate graph summary:")
print(json.dumps(cand_res.json().get("graph_summary", {}), indent=2))

print("3. Generating Task")
task_res = client.post("/api/tasks/generate", json={"job_id": job_id})
if task_res.status_code != 201:
    print("Task generation failed:", task_res.text)
    sys.exit(1)
task = task_res.json()
print("Generated Task:")
print(f"Title: {task.get('title')}")
print(f"Brief: {task.get('brief')}")
print(f"Requirements: {task.get('requirements')}")
