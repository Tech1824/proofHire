import json
from pydantic import BaseModel
from typing import Optional
from ai.llm import complete_json

class QuestionSchema(BaseModel):
    text: str
    expects: str
    hint: Optional[str] = None

QUESTIONER_SYSTEM_PROMPT = """You are a friendly senior engineer running a short technical conversation. Ask ONE question about the candidate's own code. Use real names from the context. No yes/no questions. Do not reveal answers. Match the requested level and type. For level 4, make a change doable in 3 minutes. For level 5, show a small broken snippet. Return JSON: {"text": str, "expects": "text"|"code", "hint": str|null}"""

def generate_question(job: dict, level: int, q_type: str, context: dict, history_summary: str) -> dict:
    user_prompt = f"""
Job: {job.get('title')}
Required Skills: {', '.join(job.get('required_skills', []))}
Requested Level: {level}
Requested Type: {q_type}

Node Context:
{json.dumps(context)}

Summary of last 2 turns:
{history_summary}
"""
    return complete_json("fast", QUESTIONER_SYSTEM_PROMPT, user_prompt, QuestionSchema)
