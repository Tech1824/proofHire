# INTERFACES: Python functions between folders (FROZEN after hour 2)

Why this file exists: `backend/` calls `ai/` and `db/`; `ai/` calls `db/`. If two IDEs guess these names differently, nothing connects. **Use these exact names, arguments and return shapes.** All returns are plain `dict`/`list` (JSON-friendly), never ORM objects.

Import style: `from db import crud` and `from ai import api as ai_api`.

## db/crud.py (Database person)
```python
# Jobs
def create_job(data: dict) -> dict                      # returns job dict with job_id
def list_jobs() -> list[dict]
def get_job(job_id: str) -> dict | None

# Candidates, projects, files
def create_candidate(data: dict) -> dict                # saves candidate + projects + files
def get_candidate(candidate_id: str) -> dict | None     # includes projects and files
def save_graph(candidate_id: str, graph_json: dict) -> None
def load_graph(candidate_id: str) -> dict | None        # NetworkX node_link_data format

# Tasks and submissions
def create_task(data: dict) -> dict
def get_task(task_id: str) -> dict | None
def create_submission(data: dict) -> dict
def get_submission(submission_id: str) -> dict | None   # includes files

# Depth check
def create_session(submission_id: str, max_turns: int) -> dict
def get_session(session_id: str) -> dict | None         # includes turns list
def add_turn(session_id: str, turn: dict) -> dict       # question side
def add_answer(session_id: str, turn_number: int, answer: str, code: str | None, evaluation: dict, meta: dict) -> dict
def set_session_status(session_id: str, status: str) -> None
def save_profile(session_id: str, profile: dict) -> None
def get_profile(session_id: str) -> dict | None
def list_finished_profiles_for_job(job_id: str) -> list[dict]

# Cache and config
def cache_get(key: str) -> dict | None                  # increments hit counter
def cache_set(key: str, alias: str, response: dict) -> None
def get_setting(key: str, default: str | None = None) -> str | None
def set_setting(key: str, value: str) -> None           # used for demo_mode
```
`db/seed.py` exposes `def reset_and_seed() -> None`.

## ai/api.py (AI/ML person). The ONLY file backend imports from `ai/`
```python
def build_graph(candidate_id: str) -> dict
    # reads candidate via crud, builds + saves graph. Returns {"nodes": int, "edges": int, "skills": [str]}

def get_graph_view(candidate_id: str) -> dict
    # returns {"nodes": [...], "edges": [...]} exactly as in API_CONTRACT

def generate_task(job: dict) -> dict
    # returns task dict as in API_CONTRACT (without task_id; db assigns it)

def add_submission_to_graph(submission_id: str) -> dict
    # returns {"graph_updated": True, "stats": {"files": int, "functions": int}}

def start_depth(submission_id: str) -> dict
    # creates session (via crud), returns {"session_id", "max_turns", "turn"}

def submit_answer(session_id: str, answer: str, code: str | None) -> dict
    # returns the full /api/depth/answer response body

def finish_depth(session_id: str) -> dict
    # builds profile, sets status done, returns {"status": "done"}

def get_shortlist(job_id: str) -> dict
    # returns the full /api/shortlist body, ranked

def llm_health() -> dict
    # returns {"fast": "ok"|"down", "smart": ..., "local": ...}
```

## Internal AI modules (AI/ML person only)
```python
# llm.py
def complete_json(alias: str, system: str, user: str, schema: type, cache_key_extra: str = "") -> dict
    # calls LiteLLM, validates with Pydantic, retries once, caches, respects demo_mode

# graph.py
def build_from_candidate(candidate: dict) -> "networkx.MultiDiGraph"
def subgraph_for_node(g, node_id: str, depth: int = 1) -> dict   # small context for one question
def estimate_tokens(text: str) -> int                            # len(text) // 4 is fine

# controller.py
def pick_next(state: dict, g, job: dict) -> dict     # {"node_id", "level", "type", "reason"}
def should_stop(state: dict) -> bool

# judge.py
def judge_answer(turn: dict, answer: str, code: str | None, context: dict) -> dict  # evaluation dict

# profile.py
def compute_profile(session: dict) -> dict            # pure math, no LLM
def write_summary(profile: dict, evidence: list) -> str   # one LLM call
```

## Session `state` dict (shared idea between controller and api)
```python
{ "turn_number": 3, "level": 2, "node_id": "func:...", "asked_nodes": ["..."],
  "scores": [3, 4], "confidences": [0.7, 0.8], "last_flags": ["vague"],
  "dimension_scores": {"understanding": [3, 4], "reasoning": [2]} }
```
