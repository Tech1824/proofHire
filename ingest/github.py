import os
import re
import time
import requests
from urllib.parse import urlparse

GITHUB_API_URL = "https://api.github.com"
# Simple in-memory cache for MVP: { "username": {"timestamp": time, "data": ...} }
_CACHE = {}
CACHE_TTL = 24 * 3600 # 24 hours

def parse_github_username(url: str) -> str | None:
    if not url:
        return None
    url = url.strip().rstrip('/')
    # handle simple cases like https://github.com/pro-npc
    # handle /tab/ paths
    match = re.search(r"github\.com/([^/?#]+)", url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def _get_headers():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    return {"Accept": "application/vnd.github.v3+json"}

def _fetch_file_content(repo_full_name, file_path):
    url = f"{GITHUB_API_URL}/repos/{repo_full_name}/contents/{file_path}"
    resp = requests.get(url, headers=_get_headers(), timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        if "content" in data and data.get("encoding") == "base64":
            import base64
            try:
                return base64.b64decode(data["content"]).decode('utf-8')
            except Exception:
                return None
        elif "download_url" in data and data["download_url"]:
            dl_resp = requests.get(data["download_url"], timeout=10)
            if dl_resp.status_code == 200:
                return dl_resp.text
    return None

def fetch_github_profile(github_url: str, required_skills: list[str] = None) -> dict:
    username = parse_github_username(github_url)
    if not username:
        return {"warnings": ["Invalid GitHub URL"], "projects": []}
        
    if username in _CACHE:
        if time.time() - _CACHE[username]["timestamp"] < CACHE_TTL:
            return _CACHE[username]["data"]
            
    headers = _get_headers()
    warnings = []
    projects = []
    
    try:
        user_resp = requests.get(f"{GITHUB_API_URL}/users/{username}", headers=headers, timeout=10)
        if user_resp.status_code == 404:
            return {"warnings": ["GitHub user not found"], "projects": []}
            
        rate_limit_remaining = user_resp.headers.get("X-RateLimit-Remaining")
        if rate_limit_remaining and int(rate_limit_remaining) == 0:
            return {"warnings": ["GitHub rate limit reached"], "projects": []}
            
        user_resp.raise_for_status()
    except Exception as e:
        return {"warnings": [f"Error fetching user: {str(e)}"], "projects": []}

    try:
        repos_resp = requests.get(f"{GITHUB_API_URL}/users/{username}/repos?sort=updated&per_page=100", headers=headers, timeout=10)
        repos_resp.raise_for_status()
        repos = repos_resp.json()
    except Exception as e:
        return {"warnings": [f"Error fetching repos: {str(e)}"], "projects": []}
        
    # Filter and rank repos
    valid_repos = [r for r in repos if not r.get("fork") and r.get("size", 0) > 0]
    
    # Simple ranking: just use updated time (which it's already sorted by) and required skills if language matches
    def repo_score(repo):
        score = 0
        lang = (repo.get("language") or "").lower()
        if required_skills and lang in [s.lower() for s in required_skills]:
            score += 10
        return score
        
    valid_repos.sort(key=repo_score, reverse=True)
    top_repos = valid_repos[:5]
    
    allowlist = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".go", ".rs"}
    
    for repo in top_repos:
        repo_name = repo["name"]
        repo_full_name = repo["full_name"]
        
        proj = {
            "name": repo_name,
            "description": repo.get("description") or "",
            "repo_url": repo.get("html_url"),
            "source": "github",
            "files": []
        }
        
        # Try fetching file tree
        try:
            tree_url = f"{GITHUB_API_URL}/repos/{repo_full_name}/git/trees/{repo.get('default_branch', 'main')}?recursive=1"
            tree_resp = requests.get(tree_url, headers=headers, timeout=10)
            if tree_resp.status_code == 200:
                tree_data = tree_resp.json()
                tree_files = tree_data.get("tree", [])
                
                # Fetch README first if exists
                readme_file = next((f for f in tree_files if f["path"].lower() == "readme.md"), None)
                if readme_file and readme_file.get("size", 0) < 50000:
                    content = _fetch_file_content(repo_full_name, readme_file["path"])
                    if content:
                        proj["files"].append({"path": readme_file["path"], "content": content})
                
                # Fetch up to 8 code files
                code_files = []
                for f in tree_files:
                    if f["type"] != "blob": continue
                    if f.get("size", 0) > 50000: continue
                    path = f["path"]
                    if any(ignored in path for ignored in ["node_modules/", "dist/", "tests/", "lock"]): continue
                    ext = os.path.splitext(path)[1].lower()
                    if ext in allowlist:
                        code_files.append(f)
                        
                # Prioritize root files or specific files
                code_files = code_files[:8]
                for cf in code_files:
                    if len(proj["files"]) >= 8: break
                    content = _fetch_file_content(repo_full_name, cf["path"])
                    if content:
                        proj["files"].append({"path": cf["path"], "content": content})
        except Exception as e:
            warnings.append(f"Error fetching files for {repo_name}: {str(e)}")
            
        projects.append(proj)
        
    result = {"warnings": warnings, "projects": projects}
    _CACHE[username] = {"timestamp": time.time(), "data": result}
    return result
