import json
import uuid
import time
from db import crud
from ai import api as ai_api

def run_test():
    # 1. Add Candidate
    print("Creating candidate...")
    cand_data = {
        "name": "Ankush Sharma",
        "email": "ankush@example.com",
        "github_url": "https://github.com/pro-npc",
        "linkedin_text": "I am a cybersecurity student and OSINT enthusiast who loves the mechanics of hacking—understanding systems, finding their flaws, and learning how to secure them responsibly.\nI spend my free time diving into cybercrime investigation, digital forensics, and AI Red Teaming. I love the thrill of learning, whether that means analyzing a digital footprint, solving a complex CTF challenge, or exploring new security concepts.\nMy goal is to keep improving my technical skills so I can ethically support digital investigations, raise cybersecurity awareness, and help make the internet a safer place.",
        "projects": [
            {
                "name": "OSINT Tool",
                "description": "An open source intelligence gathering tool written in Python.",
                "files": [
                    {
                        "path": "scraper.py",
                        "content": "import requests\nfrom bs4 import BeautifulSoup\n\ndef scrape_footprint(url):\n    res = requests.get(url)\n    return BeautifulSoup(res.text, 'html.parser').title.text\n"
                    }
                ]
            }
        ]
    }
    
    cand = crud.create_candidate(cand_data)
    candidate_id = cand["candidate_id"]
    print(f"Candidate created: {candidate_id}")
    
    # 2. Build Graph
    print("Building knowledge graph...")
    graph_summary = ai_api.build_graph(candidate_id)
    print("Graph Summary:", json.dumps(graph_summary, indent=2))
    
    # 3. We need a Job and Task for the depth check. Let's create a Cybersecurity/Data job.
    job = crud.create_job({
        "title": "Security Engineer",
        "company": "SecureTech",
        "description": "Red teaming, digital forensics, and building OSINT tools.",
        "salary": "$120k",
        "required_skills": ["cybersecurity", "python", "osint"],
        "seniority": "mid-level"
    })
    
    task = crud.create_task({
        "job_id": job["job_id"],
        "title": "Digital Forensics Tool",
        "brief": "Build a script to analyze a digital footprint.",
        "requirements": ["Fetch URL securely", "Parse HTML for clues"],
        "language": "python",
        "starter_code": "def scrape_footprint(url):\n    pass",
        "time_limit_min": 60,
        "rubric": [{"skill": "Cybersecurity", "weight": 1.0}]
    })
    
    # 4. Create Submission
    sub = crud.create_submission({
        "candidate_id": candidate_id,
        "task_id": task["task_id"],
        "files": [
            {
                "path": "scraper.py",
                "content": "import requests\nfrom bs4 import BeautifulSoup\n\ndef scrape_footprint(url):\n    res = requests.get(url)\n    return BeautifulSoup(res.text, 'html.parser').title.text\n"
            }
        ],
        "notes": "Here is my OSINT scraper approach."
    })
    print(f"Submission created: {sub['submission_id']}")
    
    # 5. Start Depth Check Session
    print("Starting Depth Check...")
    session_data = ai_api.start_depth(sub["submission_id"])
    session_id = session_data["session_id"]
    turn = session_data["turn"]
    
    print("\n--- INTERVIEW STARTED ---")
    print(f"Interviewer: {turn['question_text']}")
    
    # 6. Answer the question
    answer = "I used requests and BeautifulSoup to fetch and parse the HTML because they are standard Python libraries and very effective for extracting simple OSINT footprint data from public webpages without needing headless browsers."
    print(f"\nCandidate: {answer}")
    
    result = ai_api.submit_answer(session_id, answer, answer_code=None)
    eval_data = result["evaluation"]
    
    print("\n--- EVALUATION RESULT ---")
    print(f"Score: {eval_data['score']}/5")
    print(f"Flags: {eval_data['flags']}")
    print(f"Reasoning: {eval_data['reasoning']}")
    print(f"Running Score (100-scale): {result['running']['score_100']}")
    
    print("\n--- NEXT QUESTION ---")
    print(f"Interviewer: {result['next']['question_text']}")

if __name__ == '__main__':
    run_test()
