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
