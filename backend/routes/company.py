from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from db import crud

router = APIRouter(prefix="/api/company", tags=["company"])

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None

class CandidateStatusUpdate(BaseModel):
    status: str

@router.get("")
@router.get("/")
def get_company_profile():
    return crud.get_or_create_default_company()

@router.put("")
@router.put("/")
def update_company_profile(data: CompanyUpdate):
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    co = crud.get_or_create_default_company()
    updated = crud.update_company(co["company_id"], update_dict)
    return updated or co

@router.get("/dashboard")
def get_recruiter_dashboard():
    co = crud.get_or_create_default_company()
    jobs = crud.list_jobs(co["company_id"]) or crud.list_jobs()
    candidates = crud.list_candidates()
    
    assessed = [c for c in candidates if c.get("overall_score", 0) > 0]
    avg_score = round(sum(c["overall_score"] for c in assessed) / max(len(assessed), 1))
    shortlisted = [c for c in candidates if c.get("status") == "Shortlisted"]
    
    return {
        "company": co,
        "metrics": {
            "total_jobs": len(jobs),
            "open_jobs": len([j for j in jobs if j.get("status", "Open") == "Open"]),
            "total_applicants": len(candidates),
            "assessed_count": len(assessed),
            "avg_score": avg_score,
            "shortlisted_count": len(shortlisted)
        },
        "jobs": jobs,
        "applicants": candidates,
        "recent_applicants": candidates[-5:]
    }

@router.post("/candidates/{candidate_id}/status")
def set_candidate_status(candidate_id: str, payload: CandidateStatusUpdate):
    success = crud.update_candidate_status(candidate_id, payload.status)
    if not success:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"status": "ok", "candidate_id": candidate_id, "new_status": payload.status}
