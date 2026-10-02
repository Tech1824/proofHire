import os
import json
from sqlmodel import Session, SQLModel, text
from db.crud import engine
from db.models import (
    Job, Candidate, Project, CodeFile, Task,
    Submission, DepthSession, QaTurn, Profile
)

def reset_and_seed():
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Delete order: profiles -> qa_turns -> depth_sessions -> code_files -> submissions -> tasks -> projects -> candidates -> jobs
        session.exec(text("DELETE FROM profiles"))
        session.exec(text("DELETE FROM qa_turns"))
        session.exec(text("DELETE FROM depth_sessions"))
        session.exec(text("DELETE FROM code_files"))
        session.exec(text("DELETE FROM submissions"))
        session.exec(text("DELETE FROM tasks"))
        session.exec(text("DELETE FROM projects"))
        session.exec(text("DELETE FROM candidates"))
        session.exec(text("DELETE FROM jobs"))
        session.commit()

        # Seed Jobs
        job_1 = Job(
            job_id="job_1",
            title="Backend Intern",
            company="FinLeaf",
            description="Build scalable APIs.",
            required_skills=["python", "rest api", "sql"],
            seniority="junior"
        )
        job_2 = Job(
            job_id="job_2",
            title="Frontend Developer",
            company="PixelNest",
            description="Build accessible UIs.",
            required_skills=["javascript", "html/css", "accessibility"],
            seniority="junior"
        )
        session.add(job_1)
        session.add(job_2)

        # Seed Candidates
        cand_1 = Candidate(
            candidate_id="cand_1",
            name="Asha Rao",
            email="asha@example.com",
            github_url="https://github.com/asha-strong",
            linkedin_text="Backend engineer who builds robust systems.",
            graph_status="ready",
            graph_summary={"nodes": 10, "edges": 15, "skills": ["python", "sql"]}
        )
        cand_2 = Candidate(
            candidate_id="cand_2",
            name="Ravi Kumar",
            email="ravi@example.com",
            github_url="https://github.com/ravi-weak",
            linkedin_text="Expert in concurrency and everything.",
            graph_status="ready",
            graph_summary={"nodes": 3, "edges": 2, "skills": ["python"]}
        )
        session.add(cand_1)
        session.add(cand_2)
        session.commit()

        # Seed Projects and Candidate Files
        proj_1 = Project(project_id="proj_1", candidate_id="cand_1", name="Limiter Service")
        session.add(proj_1)
        session.commit()
        
        file_1 = CodeFile(
            file_id="file_1",
            project_id="proj_1",
            path="main.py",
            content="def allow_request(user_id): pass",
            language="python"
        )
        session.add(file_1)

        # Seed Tasks
        task_1 = Task(
            task_id="task_1",
            job_id="job_1",
            title="Build a rate limiter",
            brief="Implement a sliding window rate limiter.",
            requirements=["python", "no race conditions"],
            language="python",
            starter_code="def limit(): pass",
            time_limit_min=45,
            rubric=[{"skill": "python", "what_good_looks_like": "uses sliding window"}]
        )
        task_2 = Task(
            task_id="task_2",
            job_id="job_2",
            title="Accessible Dropdown",
            brief="Build a dropdown menu that is fully keyboard accessible.",
            requirements=["javascript", "aria labels"],
            language="javascript",
            starter_code="function Dropdown() {}",
            time_limit_min=45,
            rubric=[{"skill": "accessibility", "what_good_looks_like": "supports arrow keys"}]
        )
        session.add(task_1)
        session.add(task_2)
        session.commit()

        # Seed Submissions
        sub_1 = Submission(submission_id="sub_1", candidate_id="cand_1", task_id="task_1", notes="Sliding window approach")
        sub_2 = Submission(submission_id="sub_2", candidate_id="cand_2", task_id="task_2", notes="Generated using AI")
        session.add(sub_1)
        session.add(sub_2)
        session.commit()

        # Code files for submissions
        sub_file_1 = CodeFile(
            file_id="file_2",
            submission_id="sub_1",
            path="limiter.py",
            content="class Limiter: ...",
            language="python"
        )
        sub_file_2 = CodeFile(
            file_id="file_3",
            submission_id="sub_2",
            path="dropdown.js",
            content="const dropdown = () => {};",
            language="javascript"
        )
        session.add(sub_file_1)
        session.add(sub_file_2)
        
        session.commit()
        print("Seed data loaded successfully.")

if __name__ == "__main__":
    reset_and_seed()
