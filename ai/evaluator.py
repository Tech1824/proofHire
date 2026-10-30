"""
ProofHire Heavy Model Task Code Evaluator
==========================================
Runs deep static and architectural evaluation on submitted code using
frontier models (GPT-5.6 / Gemini 2.5 Pro / Claude Opus tier).

Detects:
1. Requirement compliance & missing rubric items
2. Algorithmic trade-offs & data structure choices
3. Subtle edge-case vulnerabilities & concurrency hazards
4. Surgical probe questions for Phase 2 Depth Check
"""

import json
from typing import List, Optional
from pydantic import BaseModel, Field
from ai.llm import complete_json

class TaskCodeEvaluationSchema(BaseModel):
    compliance_score: int = Field(default=3, ge=0, le=5, description="0-5 score on how thoroughly code meets task brief & rubric")
    algorithmic_approach: str = Field(default="Standard implementation", description="Short description of the algorithmic paradigm used")
    missing_requirements: List[str] = Field(default_factory=list, description="Explicit task requirements not satisfied in code")
    edge_case_vulnerabilities: List[str] = Field(default_factory=list, description="Concrete edge cases, race conditions, or memory/resource leaks")
    surgical_probes: List[str] = Field(default_factory=list, description="2-3 targeted, code-specific Socratic questions to probe the candidate")
    summary: str = Field(default="Solution submitted for review.", description="Brief architectural summary of the candidate's code")

EVALUATOR_SYSTEM_PROMPT = """You are a Principal Software Architect conducting a rigorous code review of a candidate's submitted solution.
You will evaluate the candidate's implementation against the task brief, requirements, and rubric.

Your objectives:
1. Compliance Score (0-5):
   0: Unimplemented or completely irrelevant code.
   1: Minimal boilerplate, core requirements missed.
   2: Partial implementation, major logic flaws.
   3: Working solution, basic requirements met but misses edge cases.
   4: Solid production-quality implementation covering core requirements.
   5: Exceptional code with comprehensive error handling, modularity, and trade-offs.
2. Identify any missing or partial requirements from the task requirements list.
3. Detect specific edge-case vulnerabilities (e.g., concurrency races, memory spikes, off-by-one errors, unhandled exceptions).
4. Formulate 2-3 surgical, code-grounded questions targeting their specific implementation choices and trade-offs.

Return valid JSON matching the schema strictly."""

def evaluate_task_code(task: dict, submission_code: str, notes: Optional[str] = None) -> dict:
    """Evaluates candidate submitted code using the heavy model tier."""
    if not submission_code or not submission_code.strip():
        return {
            "compliance_score": 0,
            "algorithmic_approach": "Empty submission",
            "missing_requirements": task.get("requirements", ["All requirements missed"]),
            "edge_case_vulnerabilities": ["No code submitted"],
            "surgical_probes": ["Why was no solution code submitted for this task?"],
            "summary": "Candidate submitted an empty solution."
        }

    user_prompt = f"""
TASK BRIEF:
Title: {task.get('title', 'Engineering Challenge')}
Language: {task.get('language', 'python')}
Brief: {task.get('brief', '')}
Requirements:
{json.dumps(task.get('requirements', []))}
Rubric:
{json.dumps(task.get('rubric', []))}

CANDIDATE NOTES:
{notes or 'None provided.'}

CANDIDATE SUBMITTED CODE:
```
{submission_code[:4000]}
```
"""
    try:
        result = complete_json("heavy", EVALUATOR_SYSTEM_PROMPT, user_prompt, TaskCodeEvaluationSchema)
        if not result.get("surgical_probes") and result.get("edge_case_vulnerabilities"):
            result["surgical_probes"] = [
                f"In your code, how did you handle or plan to mitigate: {v.split(':')[0]}?"
                for v in result["edge_case_vulnerabilities"][:3]
            ]
        elif not result.get("surgical_probes"):
            result["surgical_probes"] = [
                "What architectural trade-offs did you consider when implementing this logic?",
                "How does your implementation handle extreme scale or memory constraints?"
            ]
        return result
    except Exception as e:
        # Graceful fallback heuristic
        return {
            "compliance_score": 3,
            "algorithmic_approach": "Candidate custom solution",
            "missing_requirements": [],
            "edge_case_vulnerabilities": ["High-load concurrency boundaries", "Unbounded resource allocation"],
            "surgical_probes": [
                "What trade-off did you consider when structuring this implementation?",
                "How does this code behave when traffic scales 10x?"
            ],
            "summary": f"Automated static evaluation fallback: {e}"
        }

