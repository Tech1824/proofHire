import os

def is_fake():
    return os.getenv("USE_FAKES", "false").lower() == "true"

class FakeDB:
    def __init__(self):
        self.jobs = {
            "job_1": {
                "job_id": "job_1",
                "title": "Backend Intern",
                "company": "FinLeaf",
                "description": "text...",
                "required_skills": ["python", "rest api", "sql"],
                "seniority": "junior",
                "location": "San Francisco, CA",
                "work_mode": "Hybrid",
                "employment_type": "Full-time",
                "years_experience": 1,
                "responsibilities": ["Develop REST APIs", "Write unit tests", "Optimize SQL queries"]
            }
        }
        self.job_counter = 1
        
        self.candidates = {
            "cand_1": {
                "candidate_id": "cand_1",
                "name": "Asha Rao",
                "email": "asha@example.com",
                "github_url": "https://github.com/asha-demo",
                "linkedin_text": "pasted profile text...",
                "graph_status": "ready",
                "graph_summary": {"nodes": 42, "edges": 61, "skills": ["python", "fastapi", "sql"]},
                "projects": [
                    {
                        "name": "TaskTracker", "description": "REST API for tasks",
                        "repo_url": None,
                        "files": [ { "path": "app/main.py", "content": "code..." } ]
                    }
                ]
            }
        }
        self.cand_counter = 1

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        if key == "demo_mode":
            return "false"
        return default

    def create_job(self, data: dict) -> dict:
        self.job_counter += 1
        job_id = f"job_{self.job_counter}"
        job = {**data, "job_id": job_id}
        self.jobs[job_id] = job
        return job

    def list_jobs(self) -> list[dict]:
        return list(self.jobs.values())

    def get_job(self, job_id: str) -> dict | None:
        return self.jobs.get(job_id)

    def create_candidate(self, data: dict) -> dict:
        self.cand_counter += 1
        cand_id = f"cand_{self.cand_counter}"
        # For fakes, just act as if it is already ready
        cand = {**data, "candidate_id": cand_id, "graph_status": "ready", "graph_summary": {"nodes": 42, "edges": 61, "skills": ["python", "fastapi", "sql"]}}
        self.candidates[cand_id] = cand
        return cand

    def get_candidate(self, candidate_id: str) -> dict | None:
        return self.candidates.get(candidate_id)

class FakeAI:
    def llm_health(self) -> dict:
        return {"fast": "ok", "smart": "ok", "local": "down"}
        
    def build_graph(self, candidate_id: str) -> dict:
        return {"nodes": 42, "edges": 61, "skills": ["python", "fastapi", "sql"]}

    def get_graph_view(self, candidate_id: str) -> dict:
        return {
            "nodes": [ { "id": "func:app/main.py::create_task", "type": "function", "label": "create_task", "weight": 0.8 } ],
            "edges": [ { "source": "file:app/main.py", "target": "func:app/main.py::create_task", "type": "contains" } ]
        }

    def generate_task(self, job: dict) -> dict:
        return {
            "title": "Rate Limiter Task",
            "brief": "Fake task brief.",
            "requirements": ["Req 1", "Req 2"],
            "language": "python",
            "starter_code": "def run():\n    pass",
            "time_limit_min": 30,
            "rubric": [{"skill": "python", "weight": 1.0}]
        }

fake_db = FakeDB()
fake_ai = FakeAI()
