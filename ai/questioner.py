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
5. If a surgical probe hint or vulnerability is provided, incorporate it directly into your question to test their comprehension of that specific edge case.
Return valid JSON only matching schema: {"text": str, "expects": "text"|"code", "hint": str|null}"""

def generate_question(job: dict, level: int, q_type: str, context: dict, history_summary: str, probe_hint: Optional[str] = None) -> dict:
    probe_section = f"\nSurgical Probe Hint from Static Analysis:\n{probe_hint}\n" if probe_hint else ""
    user_prompt = f"""
Job: {job.get('title')}
Required Skills: {', '.join(job.get('required_skills', []))}
Requested Level: {level}
Requested Type: {q_type}
{probe_section}
Node Context:
{json.dumps(context)}

Summary of last 2 turns:
{history_summary}
"""
    return complete_json("fast", QUESTIONER_SYSTEM_PROMPT, user_prompt, QuestionSchema)
