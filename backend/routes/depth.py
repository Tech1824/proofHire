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

class ReportIssueRequest(BaseModel):
    session_id: str
    turn_number: int
    reason: str

@router.post("/report-issue")
def report_evaluation_issue(req: ReportIssueRequest):
    if is_fake():
        sess = fake_db.get_session(req.session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "ok", "session_id": req.session_id, "turn_number": req.turn_number, "disputed": True, "dispute_reason": req.reason}

    from db import crud
    from db.models import QaTurn, Profile, now_iso
    from sqlmodel import select

    with crud.Session(crud.engine) as session:
        turn = session.exec(
            select(QaTurn).where(
                QaTurn.session_id == req.session_id,
                QaTurn.turn_number == req.turn_number
            )
        ).first()
        if not turn:
            raise HTTPException(status_code=404, detail="Turn not found")

        eval_copy = dict(turn.evaluation or {})
        eval_copy["disputed"] = True
        eval_copy["dispute_reason"] = req.reason
        eval_copy["disputed_at"] = now_iso()
        flags = list(eval_copy.get("flags", []))
        if "candidate_disputed" not in flags:
            flags.append("candidate_disputed")
        eval_copy["flags"] = flags
        turn.evaluation = eval_copy
        session.add(turn)

        prof = session.get(Profile, req.session_id)
        if prof and prof.evidence:
            ev_list = []
            for ev in prof.evidence:
                if ev.get("turn_number") == req.turn_number:
                    ev_copy = dict(ev)
                    ev_copy["disputed"] = True
                    ev_copy["dispute_reason"] = req.reason
                    ev_copy["disputed_at"] = now_iso()
                    ev_flags = list(ev_copy.get("flags", []))
                    if "candidate_disputed" not in ev_flags:
                        ev_flags.append("candidate_disputed")
                    ev_copy["flags"] = ev_flags
                    ev_list.append(ev_copy)
                else:
                    ev_list.append(ev)
            prof.evidence = ev_list
            session.add(prof)

        session.commit()

    return {
        "status": "ok",
        "session_id": req.session_id,
        "turn_number": req.turn_number,
        "disputed": True,
        "dispute_reason": req.reason
    }


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

class ModelAnswerRequest(BaseModel):
    question_text: str
    code_snippet: Optional[str] = None
    expects: Optional[str] = None
    level: Optional[int] = 1

@router.post("/model-answer")
def get_model_answer_endpoint(req: ModelAnswerRequest):
    """
    Generates an educational model answer and learning guide for candidates
    so they can understand what was expected, why, and how to improve.
    """
    from ai.llm import complete_json
    
    class ModelAnswerSchema(BaseModel):
        model_answer: str
        key_concepts: list[str]
        pitfalls_to_avoid: list[str]
        reference_tip: str
        
    system = "You are an elite principal engineer and mentor helping a candidate learn and improve after a technical assessment interview. Provide a clear, educational, best-in-class explanation."
    user = f"""Question asked: {req.question_text}
Code snippet referenced: {req.code_snippet or 'None'}
Interview criterion / expects: {req.expects or 'Technical implementation reasoning and trade-offs'}

Provide:
1. model_answer: The ideal senior-level response explaining the architecture, algorithms, and trade-offs.
2. key_concepts: List of 3-4 foundational computer science or software engineering principles tested here.
3. pitfalls_to_avoid: List of 2-3 common mistakes candidates make on this type of question.
4. reference_tip: A memorable 1-sentence engineering tip for interviews and production code.
"""
    try:
        ans = complete_json("fast", system, user, ModelAnswerSchema)
        return {"status": "ok", **ans}
    except Exception as e:
        return {
            "status": "ok",
            "model_answer": f"In a production system, you should articulate the precise data contracts, error boundaries, and concurrency locks. For '{req.expects or req.question_text}', explicitly state your trade-offs (e.g. latency vs consistency, memory overhead of sliding window counters, and atomic Redis operations).",
            "key_concepts": ["Concurrency & Race Conditions", "Data Validation & Invariants", "Idempotency & Retries", "Performance Trade-offs"],
            "pitfalls_to_avoid": ["Giving broad buzzwords without referencing the exact lines of code", "Ignoring concurrency edge cases (e.g. two threads decrementing the counter simultaneously)", "Failing to validate payloads before mutating internal state"],
            "reference_tip": "Always anchor your explanation in the specific data structures and operational constraints of your code."
        }

