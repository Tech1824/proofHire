import json
import uuid

# In-memory stores
_cache = {}
_settings = {"demo_mode": "false"}
_jobs = {}
_candidates = {}
_tasks = {}
_submissions = {}
_sessions = {}
_turns = {}
_profiles = {}

def reset():
    _cache.clear()
    _settings.clear()
    _settings["demo_mode"] = "false"
    _jobs.clear()
    _candidates.clear()
    _tasks.clear()
    _submissions.clear()
    _sessions.clear()
    _turns.clear()
    _profiles.clear()

def cache_get(key: str) -> dict | None:
    hit = _cache.get(key)
    if hit:
        hit["hits"] += 1
        return hit["response"]
    return None

def cache_set(key: str, alias: str, response: dict) -> None:
    _cache[key] = {"alias": alias, "response": response, "hits": 0}

def get_setting(key: str, default: str | None = None) -> str | None:
    return _settings.get(key, default)

def set_setting(key: str, value: str) -> None:
    _settings[key] = value

def create_candidate(data: dict) -> dict:
    cid = f"cand_{uuid.uuid4().hex[:8]}"
    _candidates[cid] = data.copy()
    _candidates[cid]["candidate_id"] = cid
    return _candidates[cid]

def get_candidate(candidate_id: str) -> dict | None:
    return _candidates.get(candidate_id)

def save_graph(candidate_id: str, graph_json: dict, graph_summary: dict, status: str = "ready") -> None:
    if candidate_id in _candidates:
        _candidates[candidate_id]["graph_json"] = json.dumps(graph_json)
        _candidates[candidate_id]["graph_summary"] = json.dumps(graph_summary)
        _candidates[candidate_id]["graph_status"] = status

def load_graph(candidate_id: str) -> dict | None:
    cand = _candidates.get(candidate_id)
    if cand and cand.get("graph_json"):
        return json.loads(cand["graph_json"])
    return None

def create_session(submission_id: str, max_turns: int) -> dict:
    sid = f"sess_{uuid.uuid4().hex[:8]}"
    _sessions[sid] = {
        "session_id": sid,
        "submission_id": submission_id,
        "max_turns": max_turns,
        "state_json": "{}",
        "status": "in_progress",
        "turns": []
    }
    return _sessions[sid]

def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)

def add_turn(session_id: str, turn: dict) -> dict:
    if session_id not in _sessions:
        return {}
    _turns.setdefault(session_id, []).append(turn)
    _sessions[session_id]["turns"] = _turns[session_id]
    return turn

def update_turn_with_answer(session_id: str, turn_number: int, answer_text: str, answer_code: str | None, evaluation: dict, meta: dict) -> dict:
    if session_id in _turns:
        for t in _turns[session_id]:
            if t.get("turn_number") == turn_number:
                t["answer_text"] = answer_text
                t["answer_code"] = answer_code
                t["evaluation"] = evaluation
                t["meta"] = meta
                return t
    return {}

def update_session_state(session_id: str, state_json: dict) -> None:
    if session_id in _sessions:
        _sessions[session_id]["state_json"] = json.dumps(state_json)

def set_session_status(session_id: str, status: str) -> None:
    if session_id in _sessions:
        _sessions[session_id]["status"] = status

def save_profile(session_id: str, candidate_id: str, job_id: str, profile: dict) -> None:
    _profiles[session_id] = {
        "session_id": session_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        **profile
    }

def get_profile(session_id: str) -> dict | None:
    return _profiles.get(session_id)

def list_finished_profiles_for_job(job_id: str) -> list[dict]:
    # Mock behavior
    return [p for p in _profiles.values() if p["job_id"] == job_id]

# Dummy wrappers to simulate the rest of the endpoints when db is available
def create_job(data: dict) -> dict:
    jid = "job_1"
    _jobs[jid] = {**data, "job_id": jid}
    return _jobs[jid]

def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)

def create_task(data: dict) -> dict:
    tid = "task_1"
    _tasks[tid] = {**data, "task_id": tid}
    return _tasks[tid]

def get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)

def create_submission(data: dict) -> dict:
    subid = "sub_1"
    _submissions[subid] = {**data, "submission_id": subid}
    return _submissions[subid]

def get_submission(submission_id: str) -> dict | None:
    return _submissions.get(submission_id)
