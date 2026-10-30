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
    user = crud.get_user_by_email(req.email)
    if not user:
        # Auto-provision user for seamless demo / test access
        company = crud.get_or_create_default_company()
        user = crud.create_user({
            "email": req.email,
            "name": req.email.split("@")[0].capitalize(),
            "role": req.role or "recruiter",
            "company_id": company["company_id"] if (req.role or "recruiter") == "recruiter" else None
        })
    else:
        company = crud.get_company(user.get("company_id") or "co_finleaf") or crud.get_or_create_default_company()
        
    return {
        "status": "ok",
        "user": user,
        "company": company,
        "token": f"token_{user['user_id']}"
    }

@router.get("/me")
def get_current_user():
    from db import crud
    company = crud.get_or_create_default_company()
    return {
        "user": {
            "user_id": "usr_demo",
            "name": "Alex Mercer",
            "email": "hiring@finleaf.com",
            "role": "recruiter"
        },
        "company": company
    }
