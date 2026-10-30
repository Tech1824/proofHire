"""
ProofHire — Perfect Demo Seeder
================================
Wipes the database and creates a clean, professional demo state:
  - 4 rich job listings
  - 1 showcase candidate (Arjun Mehta, backend engineer)
  - A rich, realistic knowledge graph with 20+ nodes
  - A completed depth-check session with 5 scored turns
  - A clean shortlist with proper ranking

Run: python demo_seed.py
"""
import json
import uuid
import datetime
import networkx as nx
from sqlmodel import Session

from db import crud, models

# ── Helpers ──────────────────────────────────────────────────────────────────

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

# ── Rich demo code (this is what the "candidate" submitted) ──────────────────

DEMO_CODE = '''import time
import collections
from typing import Dict, Deque


class SlidingWindowRateLimiter:
    """
    A thread-safe sliding-window rate limiter.
    Uses a per-user deque of request timestamps to expire old entries
    in O(k) time where k is the number of expired entries.
    """

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Deque[float]] = {}

    def allow_request(self, user_id: str) -> bool:
        """
        Returns True if the request is within quota.
        Purges timestamps older than (now - window_seconds) before checking.
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        if user_id not in self._buckets:
            self._buckets[user_id] = collections.deque()

        bucket = self._buckets[user_id]

        # Expire old entries
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) < self.limit:
            bucket.append(now)
            return True

        return False

    def remaining(self, user_id: str) -> int:
        """Returns how many requests the user can still make in the current window."""
        bucket = self._buckets.get(user_id, collections.deque())
        return max(0, self.limit - len(bucket))

    def reset_user(self, user_id: str) -> None:
        """Force-clears a user\'s bucket. Useful for admin overrides."""
        self._buckets.pop(user_id, None)


def allow_request(user_id: str, now: float, limit: int, window_seconds: int) -> bool:
    """Functional wrapper for compatibility. Creates a stateless check."""
    # NOTE: This is intentionally simplified — use SlidingWindowRateLimiter
    # for production code that needs state persistence between calls.
    return True  # Stub for backwards-compat
'''

DEMO_CODE_FILE_PATH = "rate_limiter.py"

# ── Rich graph builder ────────────────────────────────────────────────────────

def build_demo_graph(candidate_id: str) -> nx.DiGraph:
    g = nx.DiGraph()

    # Candidate root node
    g.add_node(f"cand:{candidate_id}", type="candidate", label="Arjun Mehta", weight=10)

    # --- Project ---
    g.add_node("proj:ratelimiter", type="project", label="RateLimiter", weight=8)
    g.add_edge(f"cand:{candidate_id}", "proj:ratelimiter", type="authored")

    # --- Files ---
    g.add_node("file:rate_limiter.py", type="file", label="rate_limiter.py", weight=5)
    g.add_node("file:tests/test_limiter.py", type="file", label="test_limiter.py", weight=3)
    g.add_node("file:README.md", type="file", label="README.md", weight=2)
    g.add_edge("proj:ratelimiter", "file:rate_limiter.py", type="contains")
    g.add_edge("proj:ratelimiter", "file:tests/test_limiter.py", type="contains")
    g.add_edge("proj:ratelimiter", "file:README.md", type="contains")

    # --- Classes ---
    g.add_node("class:rate_limiter.py::SlidingWindowRateLimiter", type="class",
               label="SlidingWindowRateLimiter", weight=6,
               code=DEMO_CODE.strip())
    g.add_edge("file:rate_limiter.py", "class:rate_limiter.py::SlidingWindowRateLimiter", type="contains")

    # --- Functions ---
    funcs = [
        ("allow_request", "Returns True if the request is within quota."),
        ("remaining", "Returns how many requests the user can still make."),
        ("reset_user", "Force-clears a user's bucket for admin overrides."),
    ]
    for fname, fdoc in funcs:
        nid = f"func:rate_limiter.py::{fname}"
        g.add_node(nid, type="function", label=fname, weight=4,
                   code=f"# {fdoc}", doc=fdoc)
        g.add_edge("class:rate_limiter.py::SlidingWindowRateLimiter", nid, type="contains")

    # allow_request calls
    g.add_edge("func:rate_limiter.py::allow_request", "func:rate_limiter.py::remaining", type="calls")

    # --- Test functions ---
    test_funcs = ["test_basic_allow", "test_window_expiry", "test_burst_rejection"]
    for tf in test_funcs:
        nid = f"func:tests/test_limiter.py::{tf}"
        g.add_node(nid, type="function", label=tf, weight=2)
        g.add_edge("file:tests/test_limiter.py", nid, type="contains")
        g.add_edge(nid, "func:rate_limiter.py::allow_request", type="calls")

    # --- Skills ---
    skills = [
        ("python", "Python"),
        ("system design", "System Design"),
        ("sql", "SQL"),
        ("fastapi", "REST API / FastAPI"),
        ("collections", "Data Structures"),
    ]
    for skill_id, skill_label in skills:
        nid = f"skill:{skill_id}"
        g.add_node(nid, type="skill", label=skill_label, weight=3)
        g.add_edge("file:rate_limiter.py", nid, type="uses")

    # --- LinkedIn Claims ---
    claims = [
        ("claim:api_experience", "5 years Python API development"),
        ("claim:perf_focus", "Performance optimization specialist"),
        ("claim:distributed", "Experience with distributed rate limiting"),
    ]
    for claim_id, claim_label in claims:
        g.add_node(claim_id, type="claim", label=claim_label, weight=2)
        g.add_edge(f"cand:{candidate_id}", claim_id, type="claims")

    # Connect claims to skills
    g.add_edge("claim:api_experience", "skill:python", type="supports")
    g.add_edge("claim:distributed", "skill:system design", type="supports")

    return g


# ── Pre-built Q&A turns (deterministic, no LLM required) ────────────────────

DEMO_TURNS = [
    {
        "turn_number": 1,
        "type": "understanding",
        "level": 1,
        "node_ref": "func:rate_limiter.py::allow_request",
        "question_text": "In your `allow_request` method, you expire old timestamps with a while-loop. Walk me through the complexity of that operation and why you chose a deque over a list.",
        "text": "In your `allow_request` method, you expire old timestamps with a while-loop. Walk me through the complexity of that operation and why you chose a deque over a list.",
        "expects": "explanation",
        "code_snippet": {
            "path": "rate_limiter.py",
            "start_line": 37,
            "code": "while bucket and bucket[0] < cutoff:\n    bucket.popleft()"
        },
        "answer_text": "The expiry loop is O(k) where k is the number of expired entries, not O(n) over the whole window. A list would be O(n) on every popleft because it shifts every element down. A deque gives O(1) popleft because it's a doubly-linked list internally. In practice, with a 60-second window at moderate traffic, k is always small, so the loop terminates quickly.",
        "evaluation": {
            "score": 5,
            "confidence": 0.95,
            "dimensions": {
                "understanding": 5,
                "reasoning": 5,
                "communication": 4
            },
            "evidence_quote": "deque gives O(1) popleft because it's a doubly-linked list internally",
            "source_file_path": "rate_limiter.py",
            "source_lines": "37-38",
            "reasoning": "Candidate demonstrates deep understanding of deque internals and complexity. Answer is precise, tied to their specific code, and correctly identifies the trade-off.",
            "flags": []
        },
        "meta": {
            "context_tokens": 280,
            "full_context_tokens": 1850
        }
    },
    {
        "turn_number": 2,
        "type": "reasoning",
        "level": 2,
        "node_ref": "class:rate_limiter.py::SlidingWindowRateLimiter",
        "question_text": "Your implementation is not thread-safe despite the docstring saying it is. If two threads call `allow_request` for the same user_id simultaneously, what race condition exists and how would you fix it?",
        "text": "Your implementation is not thread-safe despite the docstring saying it is. If two threads call `allow_request` for the same user_id simultaneously, what race condition exists and how would you fix it?",
        "expects": "explanation",
        "code_snippet": {
            "path": "rate_limiter.py",
            "start_line": 42,
            "code": "if len(bucket) < self.limit:\n    bucket.append(now)\n    return True"
        },
        "answer_text": "You're right, that's a bug in my docstring. The check-then-act between `len(bucket) < self.limit` and `bucket.append(now)` is a classic TOCTOU race. Two threads could both read the length as 99 out of 100, both pass the check, and both append — giving 101 entries. The fix is a threading.Lock per user bucket. I'd use a defaultdict of RLock objects and acquire the relevant user's lock before the check-then-append block.",
        "evaluation": {
            "score": 5,
            "confidence": 0.93,
            "dimensions": {
                "understanding": 4,
                "reasoning": 5,
                "debugging": 5,
                "communication": 5
            },
            "evidence_quote": "check-then-act between len(bucket) < self.limit and bucket.append is a classic TOCTOU race",
            "source_file_path": "rate_limiter.py",
            "source_lines": "42-44",
            "reasoning": "Excellent. Candidate not only identified the race condition by name (TOCTOU) but correctly proposed a per-user lock solution and demonstrated they understand why a global lock would be suboptimal.",
            "flags": []
        },
        "meta": {
            "context_tokens": 320,
            "full_context_tokens": 1850
        }
    },
    {
        "turn_number": 3,
        "type": "modification",
        "level": 2,
        "node_ref": "func:rate_limiter.py::remaining",
        "question_text": "Your `remaining` method doesn't expire old entries before counting. This means it can return a stale count. How would you fix it without duplicating the expiry logic from `allow_request`?",
        "text": "Your `remaining` method doesn't expire old entries before counting. This means it can return a stale count. How would you fix it without duplicating the expiry logic from `allow_request`?",
        "expects": "explanation",
        "code_snippet": {
            "path": "rate_limiter.py",
            "start_line": 55,
            "code": "def remaining(self, user_id: str) -> int:\n    bucket = self._buckets.get(user_id, collections.deque())\n    return max(0, self.limit - len(bucket))"
        },
        "answer_text": "I'd extract the expiry logic into a private `_expire(user_id, now)` method. Then both `allow_request` and `remaining` call `_expire` first. That way the logic stays DRY and both methods return accurate counts. The `_expire` method would take the bucket and cutoff as params and mutate it in place.",
        "evaluation": {
            "score": 4,
            "confidence": 0.9,
            "dimensions": {
                "understanding": 4,
                "reasoning": 4,
                "modification": 5,
                "communication": 4
            },
            "evidence_quote": "extract the expiry logic into a private _expire(user_id, now) method",
            "source_file_path": "rate_limiter.py",
            "source_lines": "55-58",
            "reasoning": "Solid refactoring approach. Correctly identifies DRY violation and proposes a clean private method extraction. Loses one point for not mentioning the need to pass the current timestamp to avoid different `now` values between callers.",
            "flags": []
        },
        "meta": {
            "context_tokens": 295,
            "full_context_tokens": 1850
        }
    },
    {
        "turn_number": 4,
        "type": "understanding",
        "level": 3,
        "node_ref": "skill:system design",
        "question_text": "If this rate limiter needed to scale horizontally across 10 servers, what fundamental problem arises and what are two production-grade strategies to solve it?",
        "text": "If this rate limiter needed to scale horizontally across 10 servers, what fundamental problem arises and what are two production-grade strategies to solve it?",
        "expects": "explanation",
        "code_snippet": None,
        "answer_text": "The in-memory dict is local to each process, so 10 servers have 10 independent counters. A user could hit 10x their quota by spreading requests across servers. The two standard fixes are: one, centralize state in Redis using the INCR + EXPIRE pattern or a sorted set for sliding window; two, use token bucket with consistent hashing to route each user_id to the same server, so the local counter remains accurate. Redis is simpler to deploy; consistent hashing is lower latency but harder to rebalance.",
        "evaluation": {
            "score": 5,
            "confidence": 0.92,
            "dimensions": {
                "understanding": 5,
                "reasoning": 5,
                "communication": 5
            },
            "evidence_quote": "10 servers have 10 independent counters. A user could hit 10x their quota by spreading requests",
            "source_file_path": None,
            "source_lines": None,
            "reasoning": "Exceptional systems-design answer. Correctly identifies the distributed state problem, names Redis sorted sets for the sliding window variant, and proposes consistent hashing as the alternative. No coaching needed.",
            "flags": []
        },
        "meta": {
            "context_tokens": 210,
            "full_context_tokens": 1850
        }
    },
    {
        "turn_number": 5,
        "type": "debugging",
        "level": 2,
        "node_ref": "func:tests/test_limiter.py::test_window_expiry",
        "question_text": "Your test `test_window_expiry` is likely flaky in CI environments. Why, and how would you make it deterministic?",
        "text": "Your test `test_window_expiry` is likely flaky in CI environments. Why, and how would you make it deterministic?",
        "expects": "explanation",
        "code_snippet": {
            "path": "tests/test_limiter.py",
            "start_line": 1,
            "code": "def test_window_expiry():\n    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=1)\n    limiter.allow_request('user1')  # t=0\n    limiter.allow_request('user1')  # t=0\n    time.sleep(1.1)                  # Wait for window\n    assert limiter.allow_request('user1') == True"
        },
        "answer_text": "It uses `time.sleep` which is unreliable in CI — a slow runner can make the sleep shorter than expected, or the OS scheduler can delay thread resumption. To make it deterministic I'd inject a fake clock: pass a `get_time` callable into the limiter's constructor, defaulting to `time.monotonic`. In tests, inject a mock that returns controlled timestamps. Then you can advance time programmatically without actually sleeping.",
        "evaluation": {
            "score": 4,
            "confidence": 0.88,
            "dimensions": {
                "understanding": 4,
                "reasoning": 4,
                "debugging": 5,
                "communication": 4
            },
            "evidence_quote": "inject a fake clock: pass a get_time callable into the limiter's constructor, defaulting to time.monotonic",
            "source_file_path": "tests/test_limiter.py",
            "source_lines": "1-6",
            "reasoning": "Good identification of the time.sleep flakiness and a clean dependency injection solution. Loses one point for not mentioning `unittest.mock.patch` as a simpler alternative that doesn't require refactoring the production code.",
            "flags": []
        },
        "meta": {
            "context_tokens": 310,
            "full_context_tokens": 1850
        }
    }
]


# ── Main seeder ───────────────────────────────────────────────────────────────

def seed_demo():
    print("Wiping database...")
    models.SQLModel.metadata.drop_all(crud.engine)
    models.SQLModel.metadata.create_all(crud.engine)
    print("Done.")

    # 1. Jobs
    print("Creating jobs...")
    job1 = crud.create_job({
        "job_id": "job_1",
        "title": "Backend Engineer",
        "company": "FinLeaf",
        "description": "Build high-performance, resilient APIs for a fast-growing financial infrastructure product. You will optimize database queries, construct scalable microservices, and ensure our services maintain 99.99% uptime.",
        "salary": "$120k – $150k",
        "required_skills": ["python", "fastapi", "sql", "system design", "redis"],
        "seniority": "Mid-level",
        "location": "New York, NY",
        "work_mode": "Hybrid",
        "employment_type": "Full-time",
        "years_experience": 3,
        "responsibilities": [
            "Design and own high-performance REST APIs",
            "Optimize PostgreSQL queries and schema migrations",
            "Build horizontally scalable microservices",
            "Maintain 99.99% uptime SLAs"
        ]
    })

    crud.create_job({
        "title": "Senior Frontend Developer",
        "company": "PixelNest",
        "description": "Lead the development of accessible, complex interface components for a creative collaboration suite. We value deep understanding of browser rendering, WebGL, and modern reactive frameworks.",
        "salary": "$140k – $180k",
        "required_skills": ["javascript", "react", "css architecture", "accessibility", "webgl"],
        "seniority": "Senior",
        "location": "San Francisco, CA",
        "work_mode": "Remote",
        "employment_type": "Full-time",
        "years_experience": 5,
        "responsibilities": [
            "Lead interface component architecture",
            "Own the design system",
            "Drive accessibility (WCAG 2.1 AA)",
            "Mentor junior engineers"
        ]
    })

    crud.create_job({
        "title": "Site Reliability Engineer",
        "company": "CloudForge",
        "description": "Architect and maintain our global Kubernetes clusters. Write operators in Go, tune CI/CD pipelines, and own the observability stack.",
        "salary": "$160k – $200k",
        "required_skills": ["kubernetes", "go", "terraform", "prometheus", "observability"],
        "seniority": "Senior",
        "location": "Seattle, WA",
        "work_mode": "Hybrid",
        "employment_type": "Full-time",
        "years_experience": 6,
        "responsibilities": [
            "Architect global Kubernetes clusters",
            "Write custom Go operators",
            "Own the Prometheus + Grafana observability stack",
            "Lead incident response and blameless post-mortems"
        ]
    })

    crud.create_job({
        "title": "ML Infrastructure Engineer",
        "company": "NexusAI",
        "description": "Build the training and serving infrastructure for large language models. You will work on distributed training pipelines, model quantization, and low-latency inference APIs.",
        "salary": "$150k – $200k",
        "required_skills": ["python", "pytorch", "cuda", "distributed systems", "mlops"],
        "seniority": "Senior",
        "location": "Boston, MA",
        "work_mode": "Hybrid",
        "employment_type": "Full-time",
        "years_experience": 5,
        "responsibilities": [
            "Build distributed PyTorch training pipelines",
            "Optimize inference latency for production LLMs",
            "Design MLOps tooling and experiment tracking",
            "Own GPU cluster provisioning with Terraform"
        ]
    })
    print(f"  Created 4 jobs.")

    # 2. Candidate
    print("Creating candidate...")
    cand = crud.create_candidate({
        "candidate_id": "cand_demo",
        "name": "Arjun Mehta",
        "email": "arjun.mehta@example.com",
        "github_url": "https://github.com/arjunmehta-dev",
        "linkedin_text": (
            "Backend engineer with 4 years of experience building high-performance Python APIs. "
            "Led rate-limiting infrastructure at a fintech startup processing 50M+ daily requests. "
            "Deep experience with FastAPI, PostgreSQL, Redis, and distributed system design. "
            "Strong focus on correctness, testability, and production reliability. "
            "Contributor to open-source Python tooling. "
            "Education: B.Tech Computer Science, IIT Delhi, 2020."
        ),
        "graph_status": "ready",
        "projects": []
    })
    cand_id = cand["candidate_id"]
    print(f"  Created candidate: {cand_id}")

    # 3. Build and save the knowledge graph
    print("Building knowledge graph...")
    g = build_demo_graph(cand_id)
    graph_data = nx.node_link_data(g)
    summary = {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "skills": ["Python", "System Design", "SQL", "REST API / FastAPI", "Data Structures"]
    }
    crud.save_graph(cand_id, graph_data, summary)
    print(f"  Graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")

    # 4. Task
    print("Creating task...")
    task = crud.create_task({
        "task_id": "task_demo",
        "job_id": job1["job_id"],
        "title": "Sliding Window Rate Limiter",
        "brief": (
            "FinLeaf's API gateway needs a per-user rate limiter. "
            "Implement a SlidingWindowRateLimiter class that allows at most `limit` requests "
            "per `window_seconds` for any given user_id. Your implementation should be "
            "memory-efficient and expire old entries lazily."
        ),
        "requirements": [
            "Implement `allow_request(user_id) -> bool`",
            "Expire timestamps outside the active window",
            "Implement `remaining(user_id) -> int`",
            "Add a `reset_user(user_id)` for admin overrides",
            "Include at least 3 unit tests covering expiry and burst scenarios"
        ],
        "language": "python",
        "starter_code": (
            "import time\nimport collections\nfrom typing import Dict\n\n"
            "class SlidingWindowRateLimiter:\n    def __init__(self, limit: int, window_seconds: int):\n"
            "        self.limit = limit\n        self.window_seconds = window_seconds\n"
            "        # TODO: store per-user buckets\n\n"
            "    def allow_request(self, user_id: str) -> bool:\n        pass\n\n"
            "    def remaining(self, user_id: str) -> int:\n        pass\n\n"
            "    def reset_user(self, user_id: str) -> None:\n        pass\n"
        ),
        "time_limit_min": 60,
        "rubric": [
            {"skill": "Python", "weight": 0.3},
            {"skill": "Data Structures", "weight": 0.3},
            {"skill": "System Design", "weight": 0.2},
            {"skill": "Testing", "weight": 0.2}
        ]
    })
    print(f"  Task: {task['task_id']}")

    # 5. Submission (with the demo code)
    print("Creating submission...")
    sub = crud.create_submission({
        "submission_id": "sub_demo",
        "candidate_id": cand_id,
        "task_id": task["task_id"],
        "files": [
            {"path": DEMO_CODE_FILE_PATH, "content": DEMO_CODE},
            {"path": "tests/test_limiter.py", "content": (
                "import time\nimport pytest\nfrom rate_limiter import SlidingWindowRateLimiter\n\n"
                "def test_basic_allow():\n    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60)\n"
                "    assert limiter.allow_request('user1') is True\n"
                "    assert limiter.allow_request('user1') is True\n"
                "    assert limiter.allow_request('user1') is True\n"
                "    assert limiter.allow_request('user1') is False\n\n"
                "def test_window_expiry():\n    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=1)\n"
                "    limiter.allow_request('user1')\n    limiter.allow_request('user1')\n"
                "    time.sleep(1.1)\n    assert limiter.allow_request('user1') is True\n\n"
                "def test_burst_rejection():\n    limiter = SlidingWindowRateLimiter(limit=5, window_seconds=60)\n"
                "    for _ in range(5):\n        limiter.allow_request('burst_user')\n"
                "    assert limiter.allow_request('burst_user') is False\n"
            )}
        ],
        "notes": "Used a deque for O(1) pops. Chose lazy expiry over eager (background thread) to keep the implementation simple and avoid the need for a cleanup goroutine."
    })
    print(f"  Submission: {sub['submission_id']}")

    # 6. Also add submission files to the graph
    print("Adding submission files to graph...")
    # Re-add submission code files as CodeFile rows
    with Session(crud.engine) as session:
        for f_dict in [
            {"path": DEMO_CODE_FILE_PATH, "content": DEMO_CODE},
        ]:
            cf = models.CodeFile(
                submission_id=sub["submission_id"],
                path=f_dict["path"],
                content=f_dict["content"]
            )
            session.add(cf)
        session.commit()

    # 7. Depth check session with 5 pre-scored turns
    print("Creating depth-check session...")
    sess = crud.create_session(sub["submission_id"], max_turns=6)
    session_id = sess["session_id"]
    print(f"  Session: {session_id}")

    for turn_data in DEMO_TURNS:
        evaluation = turn_data.pop("evaluation")
        answer_text = turn_data.pop("answer_text")
        meta = turn_data.pop("meta")

        # Add the question turn
        crud.add_turn(session_id, {
            "turn_number": turn_data["turn_number"],
            "type": turn_data["type"],
            "level": turn_data["level"],
            "node_ref": turn_data["node_ref"],
            "question_text": turn_data["question_text"],
            "text": turn_data["text"],
            "expects": turn_data["expects"],
            "code_snippet": turn_data.get("code_snippet"),
        })

        # Fill in the answer
        crud.update_turn_with_answer(
            session_id,
            turn_data["turn_number"],
            answer_text,
            None,
            evaluation,
            meta
        )

    # Mark session as complete
    crud.set_session_status(session_id, "done")

    # 8. Compute and save profile
    print("Computing and saving profile...")
    from ai.profile import compute_profile, write_summary

    full_session = crud.get_session(session_id)
    profile = compute_profile(full_session)

    # Write a professional summary (uses the LLM, but we'll override it)
    profile["summary"] = (
        "Arjun demonstrates strong, verified ownership of his rate limiter implementation. "
        "He correctly identified the O(1) deque advantage, self-discovered a TOCTOU concurrency bug, "
        "and proposed a production-grade distributed solution using Redis sorted sets. "
        "His testing instincts are sharp — he identified time.sleep flakiness and proposed "
        "dependency injection of a fake clock. A confident, precise engineer with real depth."
    )

    crud.save_profile(
        session_id=session_id,
        candidate_id=cand_id,
        job_id=job1["job_id"],
        profile=profile
    )

    print(f"\n{'='*60}")
    print(f"  DEMO SEED COMPLETE")
    print(f"{'='*60}")
    print(f"  Candidate:      Arjun Mehta  ({cand_id})")
    print(f"  Session:        {session_id}")
    print(f"  Overall Score:  {profile['overall_score']} / 100")
    print(f"  Confidence:     {round(profile['confidence'] * 100)}%")
    print(f"  Recommendation: {profile['recommendation']}")
    print(f"  Graph nodes:    {g.number_of_nodes()}")
    print(f"  Graph edges:    {g.number_of_edges()}")
    print(f"\nOpen http://localhost:4321 to start recording!")
    print(f"\nLocalStorage values to set in browser console:")
    print(f"  localStorage.setItem('proofhire-cand', '{cand_id}');")
    print(f"  localStorage.setItem('proofhire-sub', 'sub_demo');")
    print(f"  localStorage.setItem('proofhire-session', '{session_id}');")
    print(f"  localStorage.setItem('proofhire-job', 'job_1');")

if __name__ == "__main__":
    seed_demo()
