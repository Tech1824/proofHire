import json
import networkx as nx
from typing import Optional
from datetime import datetime
import time

try:
    from db import crud
except ImportError:
    from ai import fake_crud as crud

from ai.llm import llm_health as llm_h, complete_json
from ai.graph import build_from_candidate, subgraph_for_node, estimate_tokens
from ai.controller import pick_next, should_stop
from ai.questioner import generate_question
from ai.judge import judge_answer
from ai.profile import compute_profile, write_summary
from pydantic import BaseModel, model_validator
import re

class TaskSchema(BaseModel):
    title: str
    brief: str
    requirements: list[str]
    language: str
    starter_code: str
    time_limit_min: int = 120
    rubric: list[dict]
    
    @model_validator(mode='before')
    @classmethod
    def parse_time_limit(cls, data: dict):
        if 'time_limit' in data and 'time_limit_min' not in data:
            val = str(data['time_limit'])
            nums = re.findall(r'\d+', val)
            if nums:
                data['time_limit_min'] = int(nums[0])
            else:
                data['time_limit_min'] = 120
        return data

def build_graph(candidate_id: str) -> dict:
    cand = crud.get_candidate(candidate_id)
    if not cand:
        return {"nodes": 0, "edges": 0, "skills": []}
    
    g = build_from_candidate(cand)
    skills = [d.get("label") for n, d in g.nodes(data=True) if d.get("type") == "skill"]
    summary = {"nodes": g.number_of_nodes(), "edges": g.number_of_edges(), "skills": skills}
    crud.save_graph(candidate_id, nx.node_link_data(g), summary)
    
    return summary

def get_graph_view(candidate_id: str) -> dict:
    data = crud.load_graph(candidate_id)
    if not data:
        return {"nodes": [], "edges": []}
    
    # NetworkX >= 3.0 uses 'edges', older versions use 'links'
    if "links" in data:
        data["edges"] = data.pop("links")
    elif "edges" not in data:
        data["edges"] = []
        
    return data

def generate_task(job: dict) -> dict:
    import ast
    # A single "smart" call to generate a task
    system = f"You are generating a software engineering task for a hackathon. Return a valid JSON object matching exactly this schema: {TaskSchema.schema_json()}"
    user = f"Job title: {job.get('title')}\nRequired skills: {', '.join(job.get('required_skills', []))}\nDescription: {job.get('description')}"
    # Force a unique cache key so it always generates a fresh task instead of returning the cached one
    res = complete_json("smart", system, user, TaskSchema, cache_key_extra=str(time.time()))
    
    # Ground truth validation: ensure Python starter code contains valid syntax
    if res.get("language", "").lower() == "python" and res.get("starter_code"):
        try:
            ast.parse(res["starter_code"])
        except SyntaxError as e:
            print(f"Warning: LLM generated invalid Python syntax for starter code: {e}")
            res["starter_code"] = (
                f"# Starter template for {job.get('title', 'Engineering')} task\n\n"
                f"def solve():\n    \"\"\"Implement your solution here.\"\"\"\n    pass\n"
            )
    return res

def add_submission_to_graph(submission_id: str) -> dict:
    sub = crud.get_submission(submission_id)
    if not sub:
        return {"graph_updated": False, "stats": {"files": 0, "functions": 0}}
        
    cand_id = sub.get("candidate_id")
    cand = crud.get_candidate(cand_id)
    if cand:
        # Load or create graph
        g_data = crud.load_graph(cand_id)
        g = nx.node_link_graph(g_data) if g_data else nx.DiGraph()
        
        # Add submission files to the candidate's graph
        from ai.graph import _parse_python_file
        for f in sub.get("files", []):
            path = f.get("path", "solution.py")
            content = f.get("content", "")
            file_node_id = f"file:submission:{path}"
            g.add_node(file_node_id, type="file", label=path, source="submission")
            _parse_python_file(g, file_node_id, content, path)
            
        skills = [d.get("label") for n, d in g.nodes(data=True) if d.get("type") == "skill"]
        summary = {"nodes": g.number_of_nodes(), "edges": g.number_of_edges(), "skills": skills}
        crud.save_graph(cand_id, nx.node_link_data(g), summary)

    # Dispatch asynchronous deep evaluation via Heavy Model tier in background
    import threading
    from ai.evaluator import evaluate_task_code
    def _async_eval():
        task = crud.get_task(sub.get("task_id")) or {}
        code = "\n\n".join(f.get("content", "") for f in sub.get("files", []))
        analysis = evaluate_task_code(task, code, sub.get("notes"))
        crud.cache_set(f"sub_eval:{submission_id}", "heavy", analysis)
        
    t = threading.Thread(target=_async_eval, daemon=True)
    t.start()
        
    return {"graph_updated": True, "stats": {"files": len(sub.get("files", [])), "functions": 4}}

def _extract_grounded_snippet(context: dict, node_ref: str) -> dict | None:
    for n in context.get("nodes", []):
        if n.get("id") == node_ref or n.get("type") in ["function", "class"]:
            code_text = n.get("code")
            if code_text and len(code_text.strip()) > 5:
                clean_path = n.get("id", "").split("::")[0].replace("func:", "").replace("class:", "").replace("file:", "")
                return {
                    "path": clean_path or "solution.py",
                    "start_line": 1,
                    "code": code_text[:600]
                }
    return None

def start_depth(submission_id: str) -> dict:
    max_turns = 6
    session = crud.create_session(submission_id, max_turns)
    
    # Initial state
    state = {
        "turn_number": 1,
        "asked_nodes": [],
        "scores": [],
        "confidences": [],
        "last_flags": [],
        "dimension_scores": {}
    }
    
    sub = crud.get_submission(submission_id)
    job_id = "job_1"
    if sub:
        task = crud.get_task(sub.get("task_id"))
        if task:
            job_id = task.get("job_id", "job_1")
    job = crud.get_job(job_id) or {}
    cand = crud.get_candidate(sub.get("candidate_id"))
    g = nx.node_link_graph(crud.load_graph(cand.get("candidate_id"))) if cand else nx.DiGraph()
    
    # Retrieve heavy model task analysis if already available
    task_eval = crud.cache_get(f"sub_eval:{submission_id}")
    
    next_action = pick_next(state, g, job, task_eval)
    node_ref = next_action["node_ref"]
    context = subgraph_for_node(g, node_ref)
    
    question = generate_question(job, next_action["level"], next_action["type"], context, "Start of interview.", next_action.get("probe_hint"))
    code_snippet = _extract_grounded_snippet(context, node_ref)
    
    turn = {
        "turn_number": 1,
        "type": next_action["type"],
        "level": next_action["level"],
        "phase": next_action.get("phase", "provenance"),
        "phase_label": next_action.get("phase_label", "PHASE 1: PROVENANCE"),
        "node_ref": node_ref,
        "question_text": question.get("text", question.get("question_text", "Fallback")),
        "text": question.get("text", question.get("question_text", "Fallback")),
        "expects": question.get("expects", "text"),
        "code_snippet": code_snippet
    }
    print(f"DEBUG: question = {question}")

    
    state["asked_nodes"].append(node_ref)
    crud.update_session_state(session["session_id"], state)
    crud.add_turn(session["session_id"], turn)
    
    return {
        "session_id": session["session_id"],
        "max_turns": max_turns,
        "turn": turn
    }

def submit_answer(session_id: str, answer_text: str, answer_code: str | None) -> dict:
    start_time = time.time()
    session = crud.get_session(session_id)
    if not session:
        return {}
        
    state_data = session.get("state_json", {})
    if isinstance(state_data, str):
        state = json.loads(state_data) if state_data else {}
    else:
        state = state_data or {}
    turn_number = state.get("turn_number", 1)
    
    turns = session.get("turns", [])
    current_turn = None
    for t in turns:
        if t.get("turn_number") == turn_number:
            current_turn = t
            break
            
    if not current_turn:
        return {}
        
    sub = crud.get_submission(session.get("submission_id"))
    job_id = "job_1" 
    if sub:
        task = crud.get_task(sub.get("task_id"))
        if task:
            job_id = task.get("job_id", "job_1")
    job = crud.get_job(job_id) or {}
    cand = crud.get_candidate(sub.get("candidate_id")) if sub else {}
    g = nx.node_link_graph(crud.load_graph(cand.get("candidate_id"))) if cand and cand.get("graph_json") else nx.DiGraph()
    
    context = subgraph_for_node(g, current_turn.get("node_ref"))
    
    evaluation = judge_answer(current_turn, answer_text, answer_code, context)
    evaluation["turn_number"] = turn_number
    
    # Update state
    state["scores"] = state.get("scores", []) + [evaluation["score"]]
    state["confidences"] = state.get("confidences", []) + [evaluation["confidence"]]
    state["last_flags"] = evaluation.get("flags", [])
    
    for d, s in evaluation.get("dimensions", {}).items():
        state.setdefault("dimension_scores", {}).setdefault(d, []).append(s)
        
    crud.update_session_state(session_id, state)
    
    # Context tokens logic
    ctx_str = json.dumps(context)
    full_ctx = nx.node_link_data(g) if g else {}
    full_ctx_str = json.dumps(full_ctx)
    meta = {
        "llm_alias": "fast",
        "cached": False,
        "latency_ms": int((time.time() - start_time) * 1000),
        "context_tokens": estimate_tokens(ctx_str),
        "full_context_tokens": estimate_tokens(full_ctx_str)
    }
    
    crud.update_turn_with_answer(session_id, turn_number, answer_text, answer_code, evaluation, meta)
    
    if should_stop(state):
        res = finish_depth(session_id)
        scores = state.get("scores", [0])
        res["evaluation"] = evaluation
        res["running"] = {
            "score_100": int(sum(scores) / max(len(scores), 1) * 20),
            "confidence": state.get("confidences", [0.8])[-1],
            "dimensions": evaluation.get("dimensions", {})
        }
        res["meta"] = meta
        return res
        
    # Generate next turn
    state["turn_number"] += 1
    
    # Retrieve heavy model task analysis for Phase 2 probing
    task_eval = crud.cache_get(f"sub_eval:{session.get('submission_id')}")
    next_action = pick_next(state, g, job, task_eval)
    node_ref = next_action["node_ref"]
    next_context = subgraph_for_node(g, node_ref)
    
    question = generate_question(job, next_action["level"], next_action["type"], next_context, f"Last score: {evaluation['score']}", next_action.get("probe_hint"))
    code_snippet = _extract_grounded_snippet(next_context, node_ref)
    
    next_turn = {
        "turn_number": state["turn_number"],
        "type": next_action["type"],
        "level": next_action["level"],
        "phase": next_action.get("phase", "task_validation"),
        "phase_label": next_action.get("phase_label", "PHASE 2: CODE VERIFICATION"),
        "node_ref": node_ref,
        "question_text": question.get("text", question.get("question_text", "Fallback")),
        "text": question.get("text", question.get("question_text", "Fallback")),
        "expects": question.get("expects", "text"),
        "code_snippet": code_snippet
    }
    print(f"DEBUG: next_turn question = {question}")
    
    state.setdefault("asked_nodes", []).append(node_ref)
    crud.update_session_state(session_id, state)
    crud.add_turn(session_id, next_turn)
    
    updated_session = crud.get_session(session_id)
    running_profile = compute_profile(updated_session) # computes off saved turns
    
    return {
        "evaluation": evaluation,
        "running": {
            "score_100": running_profile.get("overall_score", 0),
            "confidence": running_profile.get("confidence", 0.0),
            "turns_done": turn_number,
            "dimensions": running_profile.get("skill_profile", {})
        },
        "meta": meta,
        "status": "in_progress",
        "next": next_turn
    }

def finish_depth(session_id: str) -> dict:
    session = crud.get_session(session_id)
    if not session:
        return {"status": "error"}
    
    # If already exists, just return done
    existing = crud.get_profile(session_id)
    if existing:
        return {"status": "done", "next": None}
        
    crud.set_session_status(session_id, "done")
    profile = compute_profile(session)
    summary = write_summary(profile, profile.get("evidence", []))
    profile["summary"] = summary
    
    sub = crud.get_submission(session.get("submission_id"))
    job_id = "job_1" 
    if sub:
        task = crud.get_task(sub.get("task_id"))
        if task:
            job_id = task.get("job_id", "job_1")
    cand_id = sub.get("candidate_id") if sub else "cand_unknown"
    
    crud.save_profile(session_id, cand_id, job_id, profile)
    return {"status": "done", "next": None}

def get_shortlist(job_id: str) -> dict:
    profiles = crud.list_finished_profiles_for_job(job_id)
    
    # Enrich with names and sort
    cands = []
    for p in profiles:
        cand = crud.get_candidate(p.get("candidate_id"))
        p["name"] = cand.get("name") if cand else "Unknown"
        cands.append(p)
        
    cands.sort(key=lambda x: (x.get("overall_score", 0), x.get("confidence", 0)), reverse=True)
    
    for idx, c in enumerate(cands):
        c["rank"] = idx + 1
        
    return {
        "job_id": job_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "candidates": cands
    }

def llm_health() -> dict:
    return llm_h()
