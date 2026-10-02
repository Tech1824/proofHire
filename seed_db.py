import json
from db import crud, models
from sqlmodel import Session

def seed():
    # 1. Clear existing Jobs and Candidates from SQLite
    models.SQLModel.metadata.drop_all(crud.engine)
    models.SQLModel.metadata.create_all(crud.engine)

    # 2. Add realistic, rich roles
    job1 = crud.create_job({
        "job_id": "job_1",
        "title": "Backend Engineer",
        "company": "FinLeaf",
        "description": "Build high-performance, resilient APIs for a fast-growing financial infrastructure product. You will optimize database queries, construct scalable microservices, and ensure our services maintain 99.99% uptime.",
        "salary": "$120k - $150k",
        "required_skills": ["python", "sql", "fastapi", "system design"],
        "seniority": "mid-level",
        "location": "New York, NY",
        "work_mode": "Hybrid",
        "employment_type": "Full-time",
        "years_experience": 3,
        "responsibilities": ["Build high-performance APIs", "Optimize database queries", "Construct scalable microservices"]
    })
    
    job2 = crud.create_job({
        "title": "Senior Frontend Developer",
        "company": "PixelNest",
        "description": "Lead the development of accessible, complex interface components for a creative collaboration suite. We value deep understanding of browser rendering, WebGL, and modern reactive frameworks.",
        "salary": "$140k - $180k",
        "required_skills": ["javascript", "react", "css architecture", "accessibility"],
        "seniority": "senior",
        "location": "San Francisco, CA",
        "work_mode": "Remote",
        "employment_type": "Full-time",
        "years_experience": 5,
        "responsibilities": ["Lead interface components development", "Browser rendering optimization"]
    })
    
    job3 = crud.create_job({
        "title": "Site Reliability Engineer",
        "company": "CloudForge",
        "description": "Architect and maintain our global kubernetes clusters. You will write operators in Go, tune CI/CD pipelines, and be responsible for the observability stack.",
        "salary": "$160k - $200k",
        "required_skills": ["kubernetes", "go", "terraform", "observability"],
        "seniority": "senior",
        "location": "Seattle, WA",
        "work_mode": "Hybrid",
        "employment_type": "Full-time",
        "years_experience": 6,
        "responsibilities": ["Architect global kubernetes clusters", "Write Go operators", "Tune CI/CD pipelines"]
    })

    job4 = crud.create_job({
        "title": "Data Scientist",
        "company": "NexusAI",
        "description": "Train and evaluate large language models for domain-specific enterprise applications. You will be dealing with massive datasets, designing RAG architectures, and fine-tuning models.",
        "salary": "$130k - $170k",
        "required_skills": ["python", "pytorch", "nlp", "llms"],
        "seniority": "mid-level",
        "location": "Boston, MA",
        "work_mode": "On-site",
        "employment_type": "Full-time",
        "years_experience": 4,
        "responsibilities": ["Train LLMs", "Design RAG architectures", "Fine-tune models"]
    })

    # 3. Add Candidate
    cand1 = crud.create_candidate({
        "candidate_id": "cand_1",
        "name": "Asha Rao",
        "email": "asha@example.com",
        "github_url": "https://github.com/asha-demo",
        "linkedin_text": "Backend engineer focused on Python APIs and thoughtful data structures.",
        "projects": [
            {
                "name": "RateLimiter",
                "description": "A sliding-window rate limiter for an API.",
                "files": [
                    {
                        "path": "limiter.py",
                        "content": "def allow_request(user_id, now, limit, window_seconds):\n    return True"
                    }
                ]
            }
        ]
    })
    
    # 4. Create Task
    task1 = crud.create_task({
        "task_id": "task_1",
        "job_id": job1["job_id"],
        "title": "Sliding Window Rate Limiter",
        "brief": "Implement a rate limiter for our API.",
        "requirements": ["Support per-user request limits", "Expire timestamps outside the active window"],
        "language": "python",
        "starter_code": "def allow_request(user_id, now, limit, window_seconds):\n    pass",
        "time_limit_min": 45,
        "rubric": [{"skill": "Python", "weight": 1.0}]
    })

    # 5. Create Submission
    sub1 = crud.create_submission({
        "submission_id": "sub_1",
        "candidate_id": cand1["candidate_id"],
        "task_id": task1["task_id"],
        "files": [],
        "notes": "Test submission"
    })

    print("Database seeded with rich mock data successfully.")

if __name__ == "__main__":
    seed()
