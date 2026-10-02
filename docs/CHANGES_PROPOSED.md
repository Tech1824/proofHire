# Proposed API Changes for Phase B

## Target: `backend/routes/candidates.py`

### Changes:
1. Import `ThreadPoolExecutor` from `concurrent.futures`.
2. Import `fetch_github_profile` from `ingest.github`.
3. Import `extract_linkedin_claims` from `ingest.linkedin`.
4. Import `merge_profile` from `ai.profile_merger`.
5. Modify `create_candidate` to run GitHub and LinkedIn extraction in parallel.
6. Merge the results before saving the candidate to the DB.

### Exact Code Replacement:

```python
from fastapi import APIRouter, HTTPException
from backend.schemas import CandidateCreate, CandidateCreateResponse, CandidateResponse, GraphViewResponse
from backend.fakes import is_fake, fake_db, fake_ai
import concurrent.futures

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

@router.post("", response_model=CandidateCreateResponse, status_code=201)
@router.post("/", response_model=CandidateCreateResponse, status_code=201, include_in_schema=False)
def create_candidate(candidate: CandidateCreate):
    cand_dict = candidate.model_dump()
    
    if is_fake():
        cand = fake_db.create_candidate(cand_dict)
        summary = fake_ai.build_graph(cand["candidate_id"])
    else:
        from db import crud
        from ai import api as ai_api
        from ingest.github import fetch_github_profile
        from ingest.linkedin import extract_linkedin_claims
        from ai.profile_merger import merge_profile
        
        # Parallel fetch for GitHub and LinkedIn to save time
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_gh = executor.submit(fetch_github_profile, cand_dict.get("github_url"))
            future_li = executor.submit(extract_linkedin_claims, cand_dict.get("linkedin_text"))
            
            gh_data = future_gh.result()
            li_data = future_li.result()
            
        # Merge fetched data into the incoming candidate dict
        merged_cand_dict = merge_profile(cand_dict, gh_data, li_data)
        
        # Save the fully enriched profile
        cand = crud.create_candidate(merged_cand_dict)
        summary = ai_api.build_graph(cand["candidate_id"])
    
    return {
        "candidate_id": cand["candidate_id"],
        "graph_status": "ready",
        "graph_summary": summary
    }
```
