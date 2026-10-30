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

def compress_code_context(code: str, max_chars: int = 3500) -> str:
    """
    Intelligently compresses long code submissions to prevent context overflow
    while preserving top-level definitions, imports, and critical blocks.
    """
    if not code or len(code) <= max_chars:
        return code
    
    # Split by lines
    lines = code.splitlines()
    if len(lines) <= 80:
        return code[:max_chars]
        
    head = lines[:50]
    tail = lines[-30:]
    omitted = len(lines) - 80
    
    compressed = "\n".join(head) + f"\n\n    # ... [COMPRESSED {omitted} lines of implementation details to conserve context] ...\n\n" + "\n".join(tail)
    return compressed[:max_chars]

def compress_task_eval_for_turn(task_eval: Optional[dict], current_turn: int) -> dict:
    """
    Wraps and distills heavy model evaluation (typically 1000-2000 tokens)
    into an ultra-lean, turn-specific surgical directive (< 40 tokens)
    to prevent context overflow in the interactive Depth Check.
    """
    if not task_eval:
        return {"probe_hint": None, "focus_type": "standard"}
        
    probes = task_eval.get("surgical_probes", [])
    vulns = task_eval.get("edge_case_vulnerabilities", [])
    missing = task_eval.get("missing_requirements", [])
    approach = task_eval.get("algorithmic_approach", "Custom")
    
    # Turn 4: Focus on high-level algorithmic paradigm & primary probe
    if current_turn == 4:
        hint = probes[0] if probes else f"Probe their {approach} implementation strategy and memory trade-offs."
        return {
            "probe_hint": hint,
            "focus_type": "architectural_approach",
            "summary": f"Approach: {approach}"
        }
        
    # Turn 5: Focus on the single highest-severity edge-case vulnerability
    elif current_turn == 5:
        hint = f"Focus on vulnerability: {vulns[0]}" if vulns else (probes[1] if len(probes) > 1 else None)
        return {
            "probe_hint": hint,
            "focus_type": "edge_case_vulnerability",
            "summary": vulns[0][:80] if vulns else "Check boundary edge cases"
        }
        
    # Turn 6: Focus on code refactoring / missing requirements
    elif current_turn >= 6:
        if missing:
            hint = f"Ask how they would refactor the code to support: {missing[0]}"
        elif len(vulns) > 1:
            hint = f"Ask how to patch this failure mode: {vulns[1]}"
        elif len(probes) > 2:
            hint = probes[2]
        else:
            hint = "How would you modify this to scale 10x with zero data loss?"
            
        return {
            "probe_hint": hint,
            "focus_type": "modification_refactor",
            "summary": "Code refactor"
        }
        
    return {"probe_hint": None, "focus_type": "general"}

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
{compress_code_context(submission_code, 4000)}
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

