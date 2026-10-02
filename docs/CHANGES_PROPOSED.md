# Proposed API Changes for Phase C (JOB DETAILS)

## Targets: `backend/schemas.py`, `backend/fakes.py`, `frontend/src/scripts/app.js`

### 1. New Fields in `JobCreate` (and DB Schema)
Jobs currently lack standard details that both candidates and recruiters need (like work mode, experience, employment type). I propose adding the following fields to `JobCreate` in `backend/schemas.py`:

```python
class JobCreate(BaseModel):
    title: str
    company: str
    description: str
    required_skills: List[str]
    seniority: str
    salary: Optional[str] = None
    location: Optional[str] = None
    
    # NEW FIELDS:
    work_mode: Optional[str] = "Hybrid" # e.g., Remote, On-site, Hybrid
    employment_type: Optional[str] = "Full-time" # e.g., Full-time, Contract, Part-time
    years_experience: Optional[int] = None
    responsibilities: List[str] = []
```

### 2. Update Fake Data (`backend/fakes.py`)
Update the default `job_1` and `job_2` to populate these new fields so they appear dynamically in the UI.

### 3. Update Frontend (`frontend/src/scripts/app.js`)
Modify `renderJobs` to display these new details:
- Add a tag for `work_mode` and `employment_type` next to the location/salary.
- Show `years_experience` (e.g., "5+ Yrs Exp").
- If `responsibilities` exist, add a small section rendering them.
