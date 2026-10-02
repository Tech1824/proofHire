from fastapi import APIRouter
from backend.fakes import is_fake

router = APIRouter(prefix="/api/shortlist", tags=["shortlist"])

@router.get("/{job_id}")
def get_shortlist(job_id: str):
    if is_fake():
        # minimal mock
        return {"job_id": job_id, "candidates": [{"rank": 1, "overall_score": 100}]}
    else:
        from ai import api as ai_api
        return ai_api.get_shortlist(job_id)
