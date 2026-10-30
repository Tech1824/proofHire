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
    Persists all generated answers to SQLite storage to eliminate redundant AI calls.
    """
    import hashlib
    from db import crud
    from ai.llm import complete_json
    
    # 1. Check persistent SQLite storage first
    raw_key = f"model_ans:{req.question_text.strip()}:{req.code_snippet or ''}:{req.expects or ''}"
    cache_key = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    
    cached = crud.cache_get(cache_key)
    if cached is not None and isinstance(cached, dict) and cached.get("model_answer") and "demo string" not in cached.get("model_answer", ""):
        return {"status": "ok", **cached, "from_storage": True}

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
        if not ans.get("model_answer") or "demo string" in ans.get("model_answer", ""):
            # Fallback to high-quality domain explanation
            q_lower = req.question_text.lower()
            if "monotonic" in q_lower or "token" in q_lower or "limit" in q_lower:
                ans = {
                    "model_answer": "In production systems, state mutations on shared rate-limiting buckets must be strictly atomic and time measurements must utilize monotonic clocks. Using time.monotonic() prevents time-inversion anomalies caused by NTP backward clock adjustments. Concurrency under async coroutines must be safeguarded with an asyncio.Lock or executed atomically via a Redis Lua script to prevent race conditions during token decrement.",
                    "key_concepts": [
                        "Monotonic vs Wall-Clock Time (NTP Skew Immunity)",
                        "Atomic Check-and-Set (CAS) and Mutex Synchronization",
                        "Sliding Window & Token Bucket Invariant Preservation",
                        "Non-blocking Concurrency & Event Loop Optimization"
                    ],
                    "pitfalls_to_avoid": [
                        "Using time.time(), which can jump backwards during system NTP sync",
                        "Awaiting asynchronous network I/O while holding a CPU mutex",
                        "Relying on multi-step GET-THEN-SET without an atomic transaction"
                    ],
                    "reference_tip": "Always measure time intervals with monotonic clocks and push mutation logic to atomic data store scripts rather than distributed locks."
                }
            elif "distributed" in q_lower or "redis" in q_lower:
                ans = {
                    "model_answer": "To scale a token bucket limiter horizontally across multiple Kubernetes pods without Redis lock contention, replace distributed locks with an atomic Redis Lua script. The script executes on Redis's single-threaded event loop, computing token refills lazily from the Redis TIME command and checking allowances in a single network round-trip (O(1)). This eliminates distributed locking overhead, race conditions, and network round-trip amplification.",
                    "key_concepts": [
                        "Atomic Lua Script Execution on Redis Single-Threaded Event Loop",
                        "Centralized vs Local State Token Batching Trade-offs",
                        "Sub-millisecond API Gateway Rate Limiting Patterns"
                    ],
                    "pitfalls_to_avoid": [
                        "Executing separate GET, calculate, and SET operations without an atomic transaction",
                        "Implementing distributed locks (Redlock) for high-frequency sub-millisecond API endpoints"
                    ],
                    "reference_tip": "Push computation to the data store via atomic Lua scripts rather than pulling state across network boundaries."
                }
        # Persist to SQLite storage so users never regenerate
        crud.cache_set(cache_key, "model_answer", ans)
        return {"status": "ok", **ans, "from_storage": False}
    except Exception as e:
        ans = {
            "model_answer": f"In a production system, you should articulate the precise data contracts, error boundaries, and concurrency locks. For '{req.expects or req.question_text}', explicitly state your trade-offs (e.g. latency vs consistency, memory overhead of sliding window counters, and atomic Redis operations).",
            "key_concepts": ["Concurrency & Race Conditions", "Data Validation & Invariants", "Idempotency & Retries", "Performance Trade-offs"],
            "pitfalls_to_avoid": ["Giving broad buzzwords without referencing the exact lines of code", "Ignoring concurrency edge cases (e.g. two threads decrementing the counter simultaneously)", "Failing to validate payloads before mutating internal state"],
            "reference_tip": "Always anchor your explanation in the specific data structures and operational constraints of your code."
        }
        crud.cache_set(cache_key, "model_answer", ans)
        return {"status": "ok", **ans, "from_storage": False}

