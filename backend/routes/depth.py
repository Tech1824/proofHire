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
            return {
                "evaluation": {
                    "turn_number": 6,
                    "score": 0,
                    "confidence": 1.0,
                    "dimensions": {},
                    "evidence_quote": "Session already completed.",
                    "reasoning": "This depth check has reached its conclusion.",
                    "flags": ["already_done"]
                },
                "running": {
                    "score_100": 0,
                    "confidence": 1.0,
                    "dimensions": {}
                },
                "status": "done",
                "next": None
            }
        return {"evaluation": {}, "status": "in_progress"}
    else:
        from db import crud
        sess = crud.get_session(req.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        if sess.get("status") == "done":
            return {
                "evaluation": {
                    "turn_number": len(sess.get("turns", [])),
                    "score": 0,
                    "confidence": 1.0,
                    "dimensions": {},
                    "evidence_quote": "Session already completed.",
                    "reasoning": "This depth check has reached its conclusion.",
                    "flags": ["already_done"]
                },
                "running": {
                    "score_100": 0,
                    "confidence": 1.0,
                    "dimensions": {}
                },
                "status": "done",
                "next": None
            }
            
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

class FinishDepthRequest(BaseModel):
    session_id: str

@router.post("/finish")
def finish_depth_body(req: FinishDepthRequest):
    return finish_depth(req.session_id)


class SaveDraftRequest(BaseModel):
    draft_text: Optional[str] = None
    draft_code: Optional[str] = None

@router.post("/{session_id}/draft")
def save_session_draft(session_id: str, req: SaveDraftRequest):
    from db import crud
    sess = crud.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    state = sess.get("state_json") or {}
    state["draft_text"] = req.draft_text
    state["draft_code"] = req.draft_code
    crud.update_session_state(session_id, state)
    return {"status": "ok", "saved_at": crud.now_iso()}

@router.get("/{session_id}/resume")
def resume_session(session_id: str):
    from db import crud
    sess = crud.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    
    turns = sess.get("turns", [])
    completed_turns = [t for t in turns if t.get("answer_text") is not None]
    active_turn = next((t for t in turns if t.get("answer_text") is None), None)
    state = sess.get("state_json") or {}
    
    return {
        "session_id": session_id,
        "status": sess.get("status", "in_progress"),
        "max_turns": sess.get("max_turns", 6),
        "current_turn_number": len(completed_turns) + 1,
        "active_turn": active_turn,
        "completed_turns": completed_turns,
        "draft": {
            "draft_text": state.get("draft_text"),
            "draft_code": state.get("draft_code")
        }
    }
