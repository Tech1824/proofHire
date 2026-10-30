import uuid
import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, JSON, UniqueConstraint

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

class Company(SQLModel, table=True):
    __tablename__ = "companies"
    company_id: str = Field(default_factory=lambda: new_id("co"), primary_key=True)
    name: str = "FinLeaf"
    email: Optional[str] = "hiring@finleaf.com"
    website: Optional[str] = "https://finleaf.com"
    industry: Optional[str] = "Fintech"
    size: Optional[str] = "51–200"
    location: Optional[str] = "New York, NY"
    about: Optional[str] = "We build reliable infrastructure for modern financial products."
    created_at: str = Field(default_factory=now_iso)

class User(SQLModel, table=True):
    __tablename__ = "users"
    user_id: str = Field(default_factory=lambda: new_id("usr"), primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    password_hash: Optional[str] = "demo_password"
    role: str = "recruiter"  # "recruiter" or "candidate"
    company_id: Optional[str] = Field(default=None, foreign_key="companies.company_id")
    candidate_id: Optional[str] = Field(default=None, foreign_key="candidates.candidate_id")
    created_at: str = Field(default_factory=now_iso)

class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    job_id: str = Field(default_factory=lambda: new_id("job"), primary_key=True)
    company_id: Optional[str] = Field(default=None, foreign_key="companies.company_id")
    recruiter_id: Optional[str] = Field(default=None, foreign_key="users.user_id")
    title: str
    company: str
    description: str
    salary: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = "Hybrid"
    employment_type: Optional[str] = "Full-time"
    years_experience: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    required_skills: List[str] = Field(sa_column=Column(JSON))
    seniority: str
    status: str = "Open"
    created_at: str = Field(default_factory=now_iso)

class Candidate(SQLModel, table=True):
    __tablename__ = "candidates"
    candidate_id: str = Field(default_factory=lambda: new_id("cand"), primary_key=True)
    company_id: Optional[str] = Field(default=None, foreign_key="companies.company_id")
    name: str
    email: str
    github_url: Optional[str] = None
    linkedin_text: Optional[str] = None
    status: str = "New"  # New, Reviewed, Interview, Shortlisted, Rejected
    graph_status: str = "pending"
    graph_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    graph_summary: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: str = Field(default_factory=now_iso)

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    project_id: str = Field(default_factory=lambda: new_id("proj"), primary_key=True)
    candidate_id: str = Field(foreign_key="candidates.candidate_id")
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None

class CodeFile(SQLModel, table=True):
    __tablename__ = "code_files"
    file_id: str = Field(default_factory=lambda: new_id("file"), primary_key=True)
    project_id: Optional[str] = Field(default=None, foreign_key="projects.project_id")
    submission_id: Optional[str] = Field(default=None, foreign_key="submissions.submission_id")
    path: str
    content: str

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    task_id: str = Field(default_factory=lambda: new_id("task"), primary_key=True)
    job_id: str = Field(foreign_key="jobs.job_id")
    title: str
    brief: str
    requirements: List[str] = Field(sa_column=Column(JSON))
    language: str
    starter_code: str
    time_limit_min: int
    rubric: List[dict] = Field(sa_column=Column(JSON))
    created_at: str = Field(default_factory=now_iso)

class Submission(SQLModel, table=True):
    __tablename__ = "submissions"
    submission_id: str = Field(default_factory=lambda: new_id("sub"), primary_key=True)
    candidate_id: str = Field(foreign_key="candidates.candidate_id")
    task_id: str = Field(foreign_key="tasks.task_id")
    notes: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)

class DepthSession(SQLModel, table=True):
    __tablename__ = "depth_sessions"
    session_id: str = Field(default_factory=lambda: new_id("sess"), primary_key=True)
    submission_id: str = Field(foreign_key="submissions.submission_id")
    status: str = "in_progress"
    max_turns: int
    state_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None

class QaTurn(SQLModel, table=True):
    __tablename__ = "qa_turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_number"),)
    turn_id: str = Field(default_factory=lambda: new_id("turn"), primary_key=True)
    session_id: str = Field(foreign_key="depth_sessions.session_id")
    turn_number: int
    type: str
    level: int
    node_ref: str
    question_text: str
    code_snippet: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    expects: str
    answer_text: Optional[str] = None
    answer_code: Optional[str] = None
    evaluation: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))

class Profile(SQLModel, table=True):
    __tablename__ = "profiles"
    session_id: str = Field(primary_key=True, foreign_key="depth_sessions.session_id")
    candidate_id: str = Field(foreign_key="candidates.candidate_id")
    job_id: str = Field(foreign_key="jobs.job_id")
    overall_score: int
    confidence: float
    recommendation: str
    skill_profile: dict = Field(sa_column=Column(JSON))
    strengths: List[str] = Field(sa_column=Column(JSON))
    concerns: List[str] = Field(sa_column=Column(JSON))
    evidence: List[dict] = Field(sa_column=Column(JSON))
    summary: str

class LlmCache(SQLModel, table=True):
    __tablename__ = "llm_cache"
    cache_key: str = Field(primary_key=True)
    alias: str
    response: dict = Field(sa_column=Column(JSON))
    hits: int = 0
    created_at: str = Field(default_factory=now_iso)

class Setting(SQLModel, table=True):
    __tablename__ = "settings"
    key: str = Field(primary_key=True)
    value: str
