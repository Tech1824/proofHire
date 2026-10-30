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

@router.post("/confirm")
def confirm_evidence(payload: dict):
    from db import crud
    session_id = payload.get("session_id")
    turn_number = payload.get("turn_number")
    confirmed = payload.get("confirmed", True)
    
    with crud.Session(crud.engine) as session:
        from db.models import QaTurn, Profile
        from sqlmodel import select
        if session_id and turn_number is not None:
            turn = session.exec(select(QaTurn).where(QaTurn.session_id == session_id, QaTurn.turn_number == turn_number)).first()
            if turn and turn.evaluation:
                eval_copy = dict(turn.evaluation)
                eval_copy["recruiter_confirmed"] = confirmed
                turn.evaluation = eval_copy
                session.add(turn)
                
        if session_id:
            prof = session.get(Profile, session_id)
            if prof and prof.evidence:
                ev_list = []
                for ev in prof.evidence:
                    if turn_number is None or ev.get("turn_number") == turn_number:
                        ev_copy = dict(ev)
                        ev_copy["recruiter_confirmed"] = confirmed
                        ev_list.append(ev_copy)
                    else:
                        ev_list.append(ev)
                prof.evidence = ev_list
                session.add(prof)
        session.commit()
    return {"status": "ok", "session_id": session_id, "turn_number": turn_number, "confirmed": confirmed}
