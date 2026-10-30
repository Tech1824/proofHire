# API_CONTRACT (FROZEN after hour 2)

Base URL: `http://localhost:8000`. All paths start with `/api`. JSON only. Field names are `snake_case`. IDs are strings like `job_1`, `cand_1`, `task_1`, `sub_1`, `sess_1`.

**Changing this file:** propose in team chat -> Integrator agrees -> edit -> add a line to the Changelog at the bottom -> tell everyone to re-read it.

## Standard error shape (all errors)
```json
{ "error": { "code": "not_found", "message": "Job job_9 does not exist" } }
```
Codes: `bad_request` (400), `not_found` (404), `validation_error` (422), `llm_unavailable` (503), `internal` (500).

## Health and config
**GET /api/health**
```json
{ "status": "ok", "version": "0.1.0", "demo_mode": false,
  "llm": { "fast": "ok", "smart": "ok", "local": "down" } }
```
**POST /api/config/demo-mode** body `{ "enabled": true }` -> `{ "demo_mode": true }`

## Jobs
**POST /api/jobs** -> 201
```json
{ "title": "Backend Intern", "company": "FinLeaf", "description": "text...",
  "required_skills": ["python", "rest api", "sql"], "seniority": "junior" }
```
Response: same fields plus `"job_id": "job_1"`.

**GET /api/jobs** -> `{ "jobs": [ { job object }, ... ] }`
**GET /api/jobs/{job_id}** -> job object

## Candidates and the graph
**POST /api/candidates** -> 201
```json
{ "name": "Asha Rao", "email": "asha@example.com",
  "github_url": "https://github.com/asha-demo",
  "github_token": "gho_optional_token",
  "linkedin_text": "pasted profile text...",
  "projects": [ { "name": "TaskTracker", "description": "REST API for tasks",
                  "repo_url": null,
                  "files": [ { "path": "app/main.py", "content": "code..." } ] } ] }
```
Response:
```json
{ "candidate_id": "cand_1", "graph_status": "ready",
  "graph_summary": { "nodes": 42, "edges": 61, "skills": ["python", "fastapi", "sql"] } }
```
**GET /api/candidates/{candidate_id}** -> candidate fields + `graph_summary`
**GET /api/candidates/{candidate_id}/graph**
```json
{ "nodes": [ { "id": "func:app/main.py::create_task", "type": "function", "label": "create_task", "weight": 0.8 } ],
  "edges": [ { "source": "file:app/main.py", "target": "func:app/main.py::create_task", "type": "contains" } ] }
```
Node types: `candidate`, `project`, `file`, `function`, `class`, `skill`, `claim`. Edge types: `contains`, `uses`, `claims`, `calls`.

## Tasks
**POST /api/tasks/generate** body `{ "job_id": "job_1" }` -> 201
```json
{ "task_id": "task_1", "job_id": "job_1", "title": "Build a rate limiter",
  "brief": "Markdown text...", "requirements": ["...", "..."],
  "language": "python", "starter_code": "def limit(...): ...",
  "time_limit_min": 45,
  "rubric": [ { "skill": "python", "what_good_looks_like": "..." } ] }
```
**GET /api/tasks/{task_id}** -> task object

## Submissions
**POST /api/submissions** -> 201
```json
{ "candidate_id": "cand_1", "task_id": "task_1",
  "files": [ { "path": "limiter.py", "content": "code..." } ], "notes": "optional text" }
```
Response: `{ "submission_id": "sub_1", "graph_updated": true, "stats": { "files": 1, "functions": 4 } }`

## Depth check
A **turn object** is used in several responses:
```json
{ "turn_number": 1, "type": "question", "level": 2,
  "node_ref": "func:limiter.py::allow_request",
  "question_text": "Why did you store timestamps in a list instead of a counter?",
  "code_snippet": { "path": "limiter.py", "start_line": 12, "code": "def allow_request(...): ..." },
  "expects": "text" }
```
`type`: `question`, `modify`, `debug`. `expects`: `text` or `code`. `level`: 1 (what) to 5 (debug a broken version). `code_snippet` may be `null`.

**POST /api/depth/start** body `{ "submission_id": "sub_1" }` -> 201
```json
{ "session_id": "sess_1", "max_turns": 6, "turn": { turn object } }
```
**POST /api/depth/answer** body `{ "session_id": "sess_1", "answer_text": "text", "answer_code": null }` -> 200
```json
{ "evaluation": {
    "turn_number": 1, "score": 3, "confidence": 0.7,
    "dimensions": { "understanding": 3, "reasoning": 2, "communication": 4 },
    "evidence_quote": "exact words from the candidate's answer",
    "reasoning": "one or two sentences",
    "flags": ["vague"] },
  "running": { "score_100": 58, "confidence": 0.45, "turns_done": 1,
               "dimensions": { "understanding": 3.0, "reasoning": 2.0, "communication": 4.0 } },
  "meta": { "llm_alias": "fast", "cached": false, "latency_ms": 1300,
            "context_tokens": 412, "full_context_tokens": 6800 },
  "status": "in_progress",
  "next": { turn object } }
```
When finished: `"status": "done"` and `"next": null`.
Possible `flags`: `vague`, `off_topic`, `contradicts_claim`, `copied_phrasing`, `injection_attempt`, `empty`.

**GET /api/depth/{session_id}** -> `{ session_id, submission_id, status, turns: [ { turn, answer, evaluation } ] }`
**POST /api/depth/{session_id}/finish** -> forces the end, returns `{ "status": "done" }`

## Shortlist
**GET /api/shortlist/{job_id}**
```json
{ "job_id": "job_1", "generated_at": "2026-10-01T10:00:00Z",
  "candidates": [ {
    "rank": 1, "candidate_id": "cand_1", "name": "Asha Rao",
    "overall_score": 82, "confidence": 0.78,
    "recommendation": "strong_yes",
    "skill_profile": { "understanding": 4.2, "reasoning": 3.8, "debugging": 4.0,
                       "modification": 4.5, "ownership": 4.0, "communication": 3.9 },
    "strengths": ["Explained why a sliding window beats a fixed counter"],
    "concerns": ["Did not mention thread safety"],
    "evidence": [ { "claim": "Understands their own algorithm", "quote": "exact words",
                    "turn_number": 1, "score": 4 } ],
    "summary": "3-4 sentence plain-English summary" } ] }
```
`recommendation`: `strong_yes`, `yes`, `maybe`, `no`, `needs_more_evidence`.
Candidates without a finished depth check are not included.

## OAuth
**GET /api/auth/github/login** -> Redirects to GitHub
**GET /api/auth/github/callback** -> Returns `{ "access_token": "..." }`

## Rules for everyone
- No endpoint may be added without a Changelog line.
- Extra fields in responses are allowed. Missing or renamed fields are not.
- The frontend mocks in `frontend/src/mocks/` must match these examples exactly.

## Changelog
- v0.1: first frozen version.
- v0.2: added github_token to candidates and OAuth endpoints.
