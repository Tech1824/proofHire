import json
from pydantic import BaseModel
from typing import Optional
from ai.llm import complete_json

class QuestionSchema(BaseModel):
    text: str
    expects: str
    hint: Optional[str] = None

QUESTIONER_SYSTEM_PROMPT = """You are a friendly senior engineer running a short technical conversation. Ask ONE question about the candidate's own code.
CRITICAL ANTI-HALLUCINATION RULES:
1. Refer ONLY to functions, files, classes, or claims explicitly present in the provided Node Context. NEVER invent code or assume external modules not shown.
2. Use the exact identifier names as they appear in the context.
3. No yes/no questions. Do not reveal or suggest answers.
4. Match the requested level and type. For level 4, propose a realistic change doable in 3 minutes. For level 5, reference a realistic edge case or failure mode from their code.
Return valid JSON only matching schema: {"text": str, "expects": "text"|"code", "hint": str|null}"""

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
