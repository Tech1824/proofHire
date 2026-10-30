import os
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import urllib.parse
import requests

router = APIRouter(prefix="/api/auth", tags=["auth"])

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
# Determine if we should redirect back to localhost frontend
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:4321")

@router.get("/github/login")
def github_login():
    if not GITHUB_CLIENT_ID:
        # If no client ID is configured, redirect back with a fake token or error
        # In a real app this would be an error, but for local testing:
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=no_client_id#candidate")
        
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": f"http://localhost:8000/api/auth/github/callback",
        "scope": "",
        "prompt": "consent"
    }
    url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)

@router.get("/github/callback")
def github_callback(code: str = None):
    if not code or not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return RedirectResponse(url=f"{FRONTEND_URL}/?error=oauth_failed#candidate")
        
    # Exchange code for access token
    resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code
        },
        timeout=10
    )
    
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("access_token")
        if token:
            return RedirectResponse(url=f"{FRONTEND_URL}/?github_token={token}#candidate")
            
    return RedirectResponse(url=f"{FRONTEND_URL}/?error=oauth_failed#candidate")


from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = "demo"
    role: Optional[str] = "recruiter"

@router.post("/login")
def login(req: LoginRequest):
    from db import crud
    from db.crud import engine, Session, select, Candidate, Submission, DepthSession
    
    identifier = req.email.strip()
    
    # Check if this identifier corresponds to a candidate
    with Session(engine) as session:
        cand = session.exec(select(Candidate).where(
            (Candidate.email == identifier) | (Candidate.candidate_id == identifier)
        )).first()
        
        if cand or (req.role and req.role.lower() == "candidate"):
            if not cand:
                cand = Candidate(
                    candidate_id=f"cand_{identifier.split('@')[0]}",
                    name=identifier.split('@')[0].capitalize(),
                    email=identifier,
                    graph_status="ready"
                )
                session.add(cand)
                session.commit()
                session.refresh(cand)
                
            cand_dict = cand.model_dump()
            sub = session.exec(select(Submission).where(Submission.candidate_id == cand.candidate_id).order_by(Submission.created_at.desc())).first()
            sess = None
            if sub:
                sess = session.exec(select(DepthSession).where(DepthSession.submission_id == sub.submission_id)).first()
                
            return {
                "status": "ok",
                "role": "candidate",
                "candidate": cand_dict,
                "submission_id": sub.submission_id if sub else None,
                "session_id": sess.session_id if sess else None,
                "user": {
                    "user_id": cand.candidate_id,
                    "name": cand.name,
                    "email": cand.email,
                    "role": "candidate"
                },
                "token": f"token_{cand.candidate_id}"
            }
            
    # Recruiter / Employer Login
    user = crud.get_user_by_email(identifier)
    if not user:
        company = crud.get_or_create_default_company()
        user = crud.create_user({
            "email": identifier,
            "name": identifier.split("@")[0].capitalize(),
            "role": req.role or "recruiter",
            "company_id": company["company_id"] if (req.role or "recruiter") == "recruiter" else None
        })
    else:
        company = crud.get_company(user.get("company_id") or "co_finleaf") or crud.get_or_create_default_company()
        
    return {
        "status": "ok",
        "role": "recruiter",
        "user": user,
        "company": company,
        "token": f"token_{user['user_id']}"
    }

@router.get("/demo-accounts")
def get_demo_accounts():
    from db.crud import engine, Session, select, Candidate, User, Company, Submission, DepthSession, Profile
    with Session(engine) as session:
        candidates = session.exec(select(Candidate)).all()
        recruiters = session.exec(select(User).where(User.role == "recruiter")).all()
        companies = {c.company_id: c.name for c in session.exec(select(Company)).all()}
        
        cand_list = []
        for c in candidates:
            sub = session.exec(select(Submission).where(Submission.candidate_id == c.candidate_id)).first()
            sess = None
            if sub:
                sess = session.exec(select(DepthSession).where(DepthSession.submission_id == sub.submission_id)).first()
            prof = session.exec(select(Profile).where(Profile.candidate_id == c.candidate_id)).first()
            
            c_dict = c.model_dump()
            c_dict["submission_id"] = sub.submission_id if sub else None
            c_dict["session_id"] = sess.session_id if sess else None
            c_dict["overall_score"] = prof.overall_score if prof else None
            c_dict["recommendation"] = prof.recommendation if prof else "in_progress"
            c_dict["evidence_count"] = len(prof.evidence or []) if prof else 0
            cand_list.append(c_dict)
            
        rec_list = []
        for r in recruiters:
            r_dict = r.model_dump()
            r_dict["company_name"] = companies.get(r.company_id, "FinLeaf Capital")
            rec_list.append(r_dict)
            
        return {
            "candidates": cand_list,
            "recruiters": rec_list
        }

@router.get("/me")
def get_current_user():
    from db import crud
    company = crud.get_or_create_default_company()
    return {
        "user": {
            "user_id": "usr_demo",
            "name": "Sarah Jenkins",
            "email": "sarah.jenkins@finleaf.com",
            "role": "recruiter"
        },
        "company": company
    }
