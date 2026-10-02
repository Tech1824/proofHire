from pydantic import BaseModel
from ai.llm import complete_json

class Claim(BaseModel):
    text: str
    skills: list[str]

class LinkedInClaimsSchema(BaseModel):
    claims: list[Claim]

def extract_linkedin_claims(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {"claims": []}
        
    system = """You are an expert technical recruiter. Extract technical claims, projects, and achievements from the provided LinkedIn profile text.
For each distinct claim, extract a short summary (text) and list the relevant technical skills (languages, tools, frameworks) explicitly mentioned or strongly implied.
Ignore non-technical fluff. Output ONLY a single valid JSON object with NO markdown formatting or extra text."""

    user = f"Extract claims from this profile text:\n\n{raw_text}"
    
    try:
        res = complete_json("fast", system, user, LinkedInClaimsSchema)
        return res
    except Exception as e:
        return {"claims": [{"text": "Error extracting claims", "skills": []}], "error": str(e)}
