# DB_SCHEMA (SQLite file: `proofhire.db` in repo root, created by `db/seed.py`)

Use SQLModel. Primary keys are strings (`job_1`, `cand_1`, ...) made by a helper `new_id(prefix)`. Timestamps are ISO strings. For JSON fields, use SQLModel's native `JSON` column type (do NOT manually `json.dumps()` to avoid double encoding).

| Table | Columns |
|---|---|
| **jobs** | job_id PK, title, company, description, required_skills (json list), seniority, created_at |
| **candidates** | candidate_id PK, name, email, github_url, linkedin_text, graph_status, graph_json (json, nullable), graph_summary (json, nullable), created_at |
| **projects** | project_id PK, candidate_id FK, name, description, repo_url |
| **code_files** | file_id PK, project_id FK (nullable), submission_id FK (nullable), path, content |
| **tasks** | task_id PK, job_id FK, title, brief, requirements (json), language, starter_code, time_limit_min, rubric (json), created_at |
| **submissions** | submission_id PK, candidate_id FK, task_id FK, notes, created_at |
| **depth_sessions** | session_id PK, submission_id FK, status (`in_progress`/`done`), max_turns, state_json, created_at, finished_at |
| **qa_turns** | turn_id PK, session_id FK, turn_number, type, level, node_ref, question_text, code_snippet (json), expects, answer_text, answer_code, evaluation (json), meta (json) |
| **profiles** | session_id PK/FK, candidate_id FK, job_id FK, overall_score, confidence, recommendation, skill_profile (json), strengths (json), concerns (json), evidence (json), summary |
| **llm_cache** | cache_key PK (sha256 of alias+system+user), alias, response (json), hits, created_at |
| **settings** | key PK, value |

## Rules
- Foreign keys on. Delete order matters in `seed.reset`: profiles -> qa_turns -> depth_sessions -> submissions -> code_files -> tasks -> projects -> candidates -> jobs. (Keep `llm_cache` and `settings` on reset!)
- `seed.py` must be **idempotent**: run it 10 times, get the same clean demo data.
- No raw SQL strings with user input. Use SQLModel queries.
- Indexes: `qa_turns(session_id)`, `profiles(job_id)`, `submissions(candidate_id)`.
- **Nested Data & ORM:** When creating rows (e.g. Candidates with Projects), explicitly instantiate nested models rather than unpacking nested dicts directly (e.g. `Candidate(**data)` will fail).
- **code_files:** This table is dual-use. `project_id` is for candidate's GitHub files, `submission_id` is for active test submissions. One FK will always be null.

## Seed data (see also DEMO_SCRIPT.md)
2 jobs, 2 candidates (`cand_1` strong, `cand_2` weak), 2 tasks (one per job), 2 submissions, 0 sessions.
