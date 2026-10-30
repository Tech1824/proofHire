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

### 4. Proposed API Changes for GitHub OAuth (To bypass rate limits)
The PRD states "Will NOT build: Login", but since anonymous GitHub API calls are heavily rate-limited, we need a way to authenticate ingestion. I propose adding a lightweight GitHub OAuth flow strictly for fetching repo data, NOT for user sessions.

**New Endpoints:**
- `GET /api/auth/github/login`: Redirects to GitHub OAuth authorize URL.
- `GET /api/auth/github/callback`: Receives `code`, exchanges for `access_token`, and returns it securely to the frontend (or stores it in the backend session).

**Modifications to `CandidateCreate`:**
```python
class CandidateCreate(BaseModel):
    # ... existing fields
    github_token: Optional[str] = None # Token obtained from OAuth flow
```
**Frontend Changes (`frontend/src/scripts/app.js`):**
- Add a "Connect GitHub" button to the new investigation form.
- Upon successful OAuth, populate the `github_token` field and include it in the `POST /api/candidates` request.
