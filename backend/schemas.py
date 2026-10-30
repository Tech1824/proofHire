from typing import List, Optional
from pydantic import BaseModel

class LLMHealth(BaseModel):
    fast: str
    smart: str
    local: str

class HealthResponse(BaseModel):
    status: str
    version: str
    demo_mode: bool
    llm: LLMHealth

class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    required_skills: List[str]
    seniority: str
    salary: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = "Hybrid"
    employment_type: Optional[str] = "Full-time"
    years_experience: Optional[int] = None
    responsibilities: List[str] = []

class JobResponse(JobCreate):
    job_id: str

class JobListResponse(BaseModel):
    jobs: List[JobResponse]

class CodeFileCreate(BaseModel):
    path: str
    content: str

class ProjectCreate(BaseModel):
    name: str
    description: str
    repo_url: Optional[str] = None
    files: List[CodeFileCreate]

class CandidateCreate(BaseModel):
    name: str
    email: str
    job_id: Optional[str] = "job_1"
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    linkedin_text: str = ""
    projects: List[ProjectCreate] = []

class GraphSummary(BaseModel):
    nodes: int
    edges: int
    skills: List[str]

class CandidateCreateResponse(BaseModel):
    candidate_id: str
    graph_status: str
    graph_summary: Optional[GraphSummary] = None

class CandidateResponse(CandidateCreate):
    candidate_id: str
    status: str = "New"
    graph_status: str = "ready"
    graph_summary: Optional[GraphSummary] = None

class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    weight: float

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str

class GraphViewResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
