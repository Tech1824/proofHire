from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.fakes import is_fake, fake_db, fake_ai

router = APIRouter(prefix="/api/submissions", tags=["submissions"])

class FileInput(BaseModel):
    path: str
    content: str

class SubmissionCreateRequest(BaseModel):
    candidate_id: str
    task_id: str
    files: List[FileInput]
    notes: Optional[str] = None

@router.post("", status_code=201)
@router.post("/", status_code=201, include_in_schema=False)
def create_submission(req: SubmissionCreateRequest):
    if is_fake():
        sub = fake_db.create_submission(req.model_dump())
        stats = {"files": len(req.files), "functions": 4}
        return {"submission_id": sub["submission_id"], "graph_updated": True, "stats": stats}
    else:
        from db import crud
        from ai import api as ai_api
        sub = crud.create_submission(req.model_dump())
        result = ai_api.add_submission_to_graph(sub["submission_id"])
        return {"submission_id": sub["submission_id"], **result}
