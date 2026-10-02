from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.fakes import is_fake, fake_db, fake_ai

router = APIRouter(prefix="/api/depth", tags=["depth"])

class StartDepthRequest(BaseModel):
    submission_id: str

class AnswerDepthRequest(BaseModel):
    session_id: str
    answer_text: str
    answer_code: Optional[str] = None

@router.post("/start", status_code=201)
def start_depth(req: StartDepthRequest):
    if is_fake():
        # Minimal fake response for testing
        return {"session_id": "sess_1", "max_turns": 6, "turn": {}}
    else:
        from ai import api as ai_api
        return ai_api.start_depth(req.submission_id)

@router.post("/answer")
def answer_depth(req: AnswerDepthRequest):
    if is_fake():
        sess = fake_db.get_session(req.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        if sess.get("status") == "done":
            raise HTTPException(status_code=400, detail="Session is already done")
        return {"evaluation": {}, "status": "in_progress"}
    else:
        from db import crud
        sess = crud.get_session(req.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        if sess.get("status") == "done":
            raise HTTPException(status_code=400, detail="Session is already done")
            
        from ai import api as ai_api
        res = ai_api.submit_answer(req.session_id, req.answer_text, req.answer_code)
        if not res:
            raise HTTPException(status_code=400, detail="Could not process answer")
        return res

@router.get("/{session_id}")
def get_session(session_id: str):
    if is_fake():
        sess = fake_db.get_session(session_id)
    else:
        from db import crud
        sess = crud.get_session(session_id)
        
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess

@router.post("/{session_id}/finish")
def finish_depth(session_id: str):
    if is_fake():
        sess = fake_db.get_session(session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        fake_db.set_session_status(session_id, "done")
        return {"status": "done"}
    else:
        from db import crud
        sess = crud.get_session(session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
            
        from ai import api as ai_api
        return ai_api.finish_depth(session_id)
