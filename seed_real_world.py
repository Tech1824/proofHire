"""
ProofHire Real-World Accounts & Activities Seeder
==================================================
Creates real enterprise companies, recruiter accounts, candidate portfolios,
live code submissions, multi-turn Depth Checks, and 6-point Evidence Trails.
"""

import json
from sqlmodel import Session, SQLModel, text
from db.crud import engine
from db.models import (
    Company, User, Job, Candidate, Project, CodeFile,
    Task, Submission, DepthSession, QaTurn, Profile
)

def run_seed():
    print("Creating all tables in SQLite...")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Clear existing tables in dependency order
        session.exec(text("DELETE FROM profiles"))
        session.exec(text("DELETE FROM qa_turns"))
        session.exec(text("DELETE FROM depth_sessions"))
        session.exec(text("DELETE FROM code_files"))
        session.exec(text("DELETE FROM submissions"))
        session.exec(text("DELETE FROM tasks"))
        session.exec(text("DELETE FROM projects"))
        session.exec(text("DELETE FROM candidates"))
        session.exec(text("DELETE FROM jobs"))
        session.exec(text("DELETE FROM users"))
        session.exec(text("DELETE FROM companies"))
        session.commit()
        print("Cleared old data.")

        # ── 1. COMPANIES ──────────────────────────────────────────────────────────
        co_finleaf = Company(
            company_id="co_finleaf",
            name="FinLeaf Infrastructure",
            email="hiring@finleaf.com",
            website="https://finleaf.com",
            industry="Fintech & High-Throughput Core",
            size="51–200 employees",
            location="New York, NY (Hybrid)",
            about="FinLeaf builds ultra-low-latency transaction and rate-limiting infrastructure for global fintech applications."
        )
        co_pixelnest = Company(
            company_id="co_pixelnest",
            name="PixelNest Platform",
            email="careers@pixelnest.io",
            website="https://pixelnest.io",
            industry="Creative Tools & Cloud UI",
            size="20–50 employees",
            location="San Francisco, CA (Remote)",
            about="PixelNest engineers next-generation interactive design tools powered by WebGL, Astro, and reactive DOM engines."
        )
        session.add(co_finleaf)
        session.add(co_pixelnest)
        session.commit()
        print("Created Companies: FinLeaf & PixelNest")

        # ── 2. RECRUITER & USER ACCOUNTS ──────────────────────────────────────────
        user_sarah = User(
            user_id="usr_sarah",
            email="sarah.jenkins@finleaf.com",
            name="Sarah Jenkins",
            role="recruiter",
            company_id="co_finleaf"
        )
        user_finleaf_talent = User(
            user_id="usr_finleaf_admin",
            email="hiring@finleaf.com",
            name="FinLeaf Talent Team",
            role="recruiter",
            company_id="co_finleaf"
        )
        user_marcus = User(
            user_id="usr_marcus",
            email="marcus.vance@pixelnest.io",
            name="Marcus Vance",
            role="recruiter",
            company_id="co_pixelnest"
        )
        session.add(user_sarah)
        session.add(user_finleaf_talent)
        session.add(user_marcus)
        session.commit()
        print("Created Recruiters: Sarah Jenkins, FinLeaf Talent, Marcus Vance")

        # ── 3. JOB POSTINGS ───────────────────────────────────────────────────────
        job_1 = Job(
            job_id="job_1",
            company_id="co_finleaf",
            recruiter_id="usr_sarah",
            title="Senior Distributed Systems Engineer",
            company="FinLeaf Infrastructure",
            description="Design, optimize, and maintain resilient multi-region distributed rate-limiting services, memory caches, and transaction queues.",
            salary="$165,000 – $195,000",
            location="New York, NY / Hybrid",
            work_mode="Hybrid",
            employment_type="Full-time",
            years_experience=5,
            responsibilities=[
                "Architect fault-tolerant rate limiting algorithms with zero central Redis bottlenecks.",
                "Ensure strict 99.999% SLA across 50,000 requests/sec with p99 latency < 2ms.",
                "Lead technical code reviews and defend architectural trade-offs."
            ],
            required_skills=["python", "distributed systems", "redis", "concurrency", "system design"],
            seniority="Senior",
            status="Open"
        )
        job_2 = Job(
            job_id="job_2",
            company_id="co_finleaf",
            recruiter_id="usr_sarah",
            title="Backend Intern (High-Throughput APIs)",
            company="FinLeaf Infrastructure",
            description="Build foundational backend services, automated test harnesses, and rate-limiting middleware using Python and FastAPI.",
            salary="$45 / hr",
            location="New York, NY",
            work_mode="On-site",
            employment_type="Internship",
            years_experience=1,
            responsibilities=[
                "Implement REST endpoints with strict Pydantic validation.",
                "Write robust unit and integration tests with synthetic clock mocks."
            ],
            required_skills=["python", "fastapi", "rest api", "sql"],
            seniority="Junior",
            status="Open"
        )
        job_3 = Job(
            job_id="job_3",
            company_id="co_pixelnest",
            recruiter_id="usr_marcus",
            title="Frontend Systems Architect",
            company="PixelNest Platform",
            description="Lead the architecture of our zero-overhead WebGL and Astro design workspace.",
            salary="$170,000 – $205,000",
            location="San Francisco, CA / Remote",
            work_mode="Remote",
            employment_type="Full-time",
            years_experience=6,
            responsibilities=[
                "Build reactive canvas interfaces with sub-16ms frame budgeting.",
                "Optimize Island Architecture bundle payloads to < 50kb baseline JS."
            ],
            required_skills=["typescript", "react", "astro", "webgl", "accessibility"],
            seniority="Staff",
            status="Open"
        )
        session.add(job_1)
        session.add(job_2)
        session.add(job_3)
        session.commit()
        print("Created Jobs: Distributed Systems (FinLeaf), Backend Intern (FinLeaf), Frontend Architect (PixelNest)")

        # ── 4. TECHNICAL TASKS ────────────────────────────────────────────────────
        task_1 = Task(
            task_id="task_1",
            job_id="job_1",
            title="Thread-Safe Sliding Window Rate Limiter",
            brief="Implement a thread-safe, memory-bounded sliding window rate limiter in Python that handles 1M requests per second with strict TOCTOU race condition prevention.",
            requirements=[
                "Per-user sliding window rate limiting with microsecond granularity.",
                "Thread-safe concurrency with bounded memory consumption (evict stale entries).",
                "O(1) amortized eviction using double-ended queue (deque) or ring buffer.",
                "Comprehensive tests with mock clock injection to prevent flaky sleep timers."
            ],
            language="python",
            starter_code="""import time
from collections import deque
import threading

class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_sec: float):
        self.max_requests = max_requests
        self.window_sec = window_sec
        # TODO: Implement thread-safe storage

    def is_allowed(self, user_id: str) -> bool:
        pass
""",
            time_limit_min=60,
            rubric=[
                {"criterion": "Concurrency & Thread Safety", "weight": 0.35, "description": "Proper usage of fine-grained locks; avoidance of TOCTOU races."},
                {"criterion": "Memory Efficiency & Eviction", "weight": 0.35, "description": "Amortized O(1) eviction using deque; preventing unbounded memory growth."},
                {"criterion": "Test Quality & Determinism", "weight": 0.30, "description": "No hardcoded sleep calls; injectable clock."}
            ]
        )
        session.add(task_1)
        session.commit()

        # ── 5. CANDIDATE 1: ARJUN MEHTA (STRONG HIRE / SHORTLISTED #1) ───────────
        cand_arjun = Candidate(
            candidate_id="cand_arjun",
            company_id="co_finleaf",
            name="Arjun Mehta",
            email="arjun.mehta@devmail.io",
            github_url="https://github.com/arjunmehta-dev",
            linkedin_text="Staff backend engineer with 6+ years optimizing high-load distributed caches, Redis clusters, and async Python systems.",
            status="Shortlisted",
            graph_status="ready",
            graph_summary={"nodes": 18, "edges": 32, "skills": ["python", "redis", "distributed systems", "concurrency", "fastapi"]}
        )
        session.add(cand_arjun)
        session.flush()

        proj_arjun = Project(
            project_id="proj_arjun_1",
            candidate_id="cand_arjun",
            name="distributed-rate-limiter",
            description="Distributed sliding window rate limiter backed by Redis and local memory ring buffers.",
            repo_url="https://github.com/arjunmehta-dev/distributed-rate-limiter"
        )
        session.add(proj_arjun)
        session.flush()

        code_arjun_repo = CodeFile(
            file_id="file_arjun_1",
            project_id="proj_arjun_1",
            path="storage.py",
            content="""from collections import deque
import threading
import time

class MemoryWindowStorage:
    def __init__(self, window_sec: float):
        self.window_sec = window_sec
        self.buckets = {}
        self.lock = threading.Lock()

    def record_and_check(self, user_id: str, max_allowed: int, now: float = None) -> bool:
        current_time = now if now is not None else time.time()
        with self.lock:
            if user_id not in self.buckets:
                self.buckets[user_id] = deque()
            q = self.buckets[user_id]
            # O(1) amortized popleft eviction of expired timestamps
            cutoff = current_time - self.window_sec
            while q and q[0] <= cutoff:
                q.popleft()
            if len(q) < max_allowed:
                q.append(current_time)
                return True
            return False
"""
        )
        session.add(code_arjun_repo)

        # Arjun's Task Submission
        arjun_submission_code = """from collections import deque
import threading
import time

class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_sec: float, clock=None):
        self.max_requests = max_requests
        self.window_sec = window_sec
        self.clock = clock or time.time
        self.user_queues = {}
        self.locks = {}
        self.meta_lock = threading.Lock()

    def _get_user_lock(self, user_id: str) -> threading.Lock:
        with self.meta_lock:
            if user_id not in self.locks:
                self.locks[user_id] = threading.Lock()
            return self.locks[user_id]

    def is_allowed(self, user_id: str) -> bool:
        user_lock = self._get_user_lock(user_id)
        current_time = self.clock()
        with user_lock:
            if user_id not in self.user_queues:
                self.user_queues[user_id] = deque()
            q = self.user_queues[user_id]
            cutoff = current_time - self.window_sec
            # Evict stale entries in O(1) amortized
            while q and q[0] <= cutoff:
                q.popleft()
            # Atomically check and append under user_lock
            if len(q) < self.max_requests:
                q.append(current_time)
                return True
            return False
"""
        sub_arjun = Submission(
            submission_id="sub_arjun_1",
            candidate_id="cand_arjun",
            task_id="task_1",
            notes="Implemented per-user fine-grained locking to prevent global lock contention, with injectable clock for deterministic testing."
        )
        session.add(sub_arjun)
        session.flush()

        code_arjun_sub = CodeFile(
            file_id="file_arjun_sub",
            submission_id="sub_arjun_1",
            path="solution.py",
            content=arjun_submission_code
        )
        session.add(code_arjun_sub)

        # Arjun's Depth Session & Completed Turns
        sess_arjun = DepthSession(
            session_id="sess_arjun_1",
            submission_id="sub_arjun_1",
            status="done",
            max_turns=6,
            state_json={"scores": [5, 5, 4, 5, 5, 5], "confidences": [0.95, 0.92, 0.88, 0.93, 0.95, 0.94], "turn_number": 6}
        )
        session.add(sess_arjun)
        session.flush()

        turns_data_arjun = [
            {
                "num": 1,
                "node": "func:storage.py::record_and_check",
                "q": "In storage.py line 18, why did you choose a collections.deque instead of a standard Python list for sliding window timestamps?",
                "a": "A standard list pop(0) takes O(N) because every remaining element shifts in memory. With collections.deque, popleft() is strictly O(1) amortized via doubly-linked memory blocks, so eviction overhead stays negligible under 50k RPS.",
                "score": 5,
                "ev": "collections.deque popleft() is strictly O(1) amortized via doubly-linked memory blocks",
                "reasoning": "Candidate demonstrated deep mastery of Python memory structures and computational complexity under high RPS.",
                "file": "storage.py",
                "lines": "18-22",
                "confirmed": True
            },
            {
                "num": 2,
                "node": "func:storage.py::record_and_check",
                "q": "What concurrency risk occurs if multiple threads check the length and append to the deque without synchronization?",
                "a": "It creates a classic Time-Of-Check to Time-Of-Use (TOCTOU) race condition. Two concurrent threads could both see len(q) == max_allowed - 1 simultaneously, and both append, violating the rate limit guarantee.",
                "score": 5,
                "ev": "classic Time-Of-Check to Time-Of-Use (TOCTOU) race condition",
                "reasoning": "Identified the exact race condition and explained why checking length separate from appending violates thread safety.",
                "file": "storage.py",
                "lines": "15-25",
                "confirmed": True
            },
            {
                "num": 3,
                "node": "proj_arjun_1",
                "q": "In your distributed-rate-limiter repo, what failure mode occurs if the primary Redis node drops during peak traffic?",
                "a": "Without local fallback, requests would hang or fail open. In my repo I implemented a circuit breaker: if Redis sentinel failover exceeds 200ms, the node falls back to local in-memory token buckets with bounded TTL.",
                "score": 4,
                "ev": "circuit breaker: if Redis sentinel failover exceeds 200ms, the node falls back to local in-memory token buckets",
                "reasoning": "Articulated realistic resilience trade-offs between distributed consensus and local fallback modes.",
                "file": "storage.py",
                "lines": "20-30",
                "confirmed": True
            },
            {
                "num": 4,
                "node": "func:solution.py::is_allowed",
                "q": "In your submission solution.py line 20, you used per-user locks instead of a single global lock. What trade-off does this introduce?",
                "a": "A global lock causes severe lock convoying across thousands of unrelated users. Per-user locks eliminate thread contention between different clients, but consume slightly more RAM for the locks dictionary, which I mitigate by pruning idle users.",
                "score": 5,
                "ev": "Per-user locks eliminate thread contention between different clients, but consume slightly more RAM for the locks dictionary",
                "reasoning": "Exceptional architectural understanding of lock granularity vs memory consumption trade-offs.",
                "file": "solution.py",
                "lines": "18-28",
                "confirmed": True
            },
            {
                "num": 5,
                "node": "func:solution.py::is_allowed",
                "q": "How does your implementation prevent memory exhaustion if millions of unique IP addresses send 1 request each and never return?",
                "a": "Under high cardinality attacks, retaining an empty deque per IP causes unbounded memory growth. I addressed this with an LRU cache eviction policy for idle user queues that haven't sent a request within 2 window periods.",
                "score": 5,
                "ev": "addressed this with an LRU cache eviction policy for idle user queues that haven't sent a request",
                "reasoning": "Proactively solved the memory leak vulnerability identified by the Heavy AI evaluation.",
                "file": "solution.py",
                "lines": "25-35",
                "confirmed": True
            },
            {
                "num": 6,
                "node": "func:solution.py::is_allowed",
                "q": "How would you refactor is_allowed to support distributed clustering across 10 EC2 nodes with zero central bottleneck?",
                "a": "I would use a two-tiered architecture: local sliding window limits at the Envoy/API gateway layer for coarse filtering, paired with Redis Cell or an asynchronous sliding window log replicated across an active-active Redis cluster.",
                "score": 5,
                "ev": "local sliding window limits at the Envoy/API gateway layer for coarse filtering",
                "reasoning": "Clear, practical systems architecture answer showing senior-level distributed design skills.",
                "file": "solution.py",
                "lines": "1-35",
                "confirmed": True
            }
        ]

        arjun_evidence = []
        for t in turns_data_arjun:
            q_turn = QaTurn(
                turn_id=f"turn_arjun_{t['num']}",
                session_id="sess_arjun_1",
                turn_number=t["num"],
                type="question",
                level=4 if t["num"] < 4 else 5,
                node_ref=t["node"],
                question_text=t["q"],
                expects="text",
                answer_text=t["a"],
                evaluation={
                    "score": t["score"],
                    "confidence": 0.95,
                    "reasoning": t["reasoning"],
                    "evidence_quote": t["ev"],
                    "source_file_path": t["file"],
                    "source_lines": t["lines"],
                    "dimensions": {"understanding": t["score"], "reasoning": t["score"], "debugging": 5},
                    "recruiter_confirmed": t["confirmed"]
                }
            )
            session.add(q_turn)
            arjun_evidence.append({
                "claim": f"Performance on turn {t['num']}",
                "turn_number": t["num"],
                "skill_name": "Distributed Concurrency & Memory Scaling",
                "where_identified": f"{t['file']} (lines {t['lines']})",
                "project_or_task": "Task Submission: Solution" if "solution" in t["file"] else "distributed-rate-limiter",
                "question": t["q"],
                "candidate_answer": t["a"],
                "score": t["score"],
                "reasoning": t["reasoning"],
                "quote": t["ev"],
                "evidence_quote": t["ev"],
                "source_file_path": t["file"],
                "source_lines": t["lines"],
                "recruiter_confirmed": t["confirmed"]
            })

        prof_arjun = Profile(
            session_id="sess_arjun_1",
            candidate_id="cand_arjun",
            job_id="job_1",
            overall_score=88,
            confidence=0.91,
            recommendation="strong_yes",
            skill_profile={
                "understanding": 4.9,
                "reasoning": 4.8,
                "ownership": 5.0,
                "communication": 4.6,
                "debugging": 4.8,
                "modification": 4.7
            },
            strengths=[
                "collections.deque popleft() is strictly O(1) amortized via doubly-linked memory blocks",
                "classic Time-Of-Check to Time-Of-Use (TOCTOU) race condition",
                "addressed this with an LRU cache eviction policy for idle user queues"
            ],
            concerns=[],
            evidence=arjun_evidence,
            summary="Arjun demonstrated exceptional senior-level engineering mastery across all 6 turns. Verified 100% ownership of his distributed-rate-limiter repo, articulated exact TOCTOU race condition mechanics, and defended memory bounding under high cardinality. Strongest candidate evaluated."
        )
        session.add(prof_arjun)
        print("Created Candidate 1: Arjun Mehta (Score: 88, Rank: #1, Shortlisted, All 6 Evidence Items Confirmed)")

        # ── 6. CANDIDATE 2: ASHA RAO (HIRE / INTERVIEW #2) ────────────────────────
        cand_asha = Candidate(
            candidate_id="cand_asha",
            company_id="co_finleaf",
            name="Asha Rao",
            email="asha.rao@techhub.org",
            github_url="https://github.com/asha-strong",
            linkedin_text="Backend engineer specializing in Python, PostgreSQL, and FastAPI microservices with 3 years experience.",
            status="Interview",
            graph_status="ready",
            graph_summary={"nodes": 12, "edges": 20, "skills": ["python", "sql", "fastapi", "rest api"]}
        )
        session.add(cand_asha)
        session.flush()

        sub_asha = Submission(
            submission_id="sub_asha_1",
            candidate_id="cand_asha",
            task_id="task_1",
            notes="Implemented thread-safe sliding window rate limiter with standard threading.Lock."
        )
        session.add(sub_asha)
        session.flush()

        sess_asha = DepthSession(
            session_id="sess_asha_1",
            submission_id="sub_asha_1",
            status="done",
            max_turns=6,
            state_json={"scores": [4, 4, 3, 4, 3, 4], "confidences": [0.85, 0.82, 0.80, 0.85, 0.78, 0.82], "turn_number": 6}
        )
        session.add(sess_asha)
        session.flush()

        turns_data_asha = [
            {"num": 1, "q": "Why use deque over a list for tracking timestamps?", "a": "Deque is much faster for popping from the front because list reallocates.", "s": 4, "ev": "Deque is much faster for popping from the front", "r": "Correct algorithmic intuition regarding front pop cost.", "f": "limiter.py", "lines": "10-15"},
            {"num": 2, "q": "What race condition happens without locking in is_allowed?", "a": "Two threads might both see that count is under the limit, and both add their timestamp.", "s": 4, "ev": "Two threads might both see that count is under the limit", "r": "Clear identification of the concurrent check-then-act bug.", "f": "limiter.py", "lines": "14-22"},
            {"num": 3, "q": "How would you handle clock skews in distributed servers?", "a": "We could use NTP or centralized timestamping, but for a single service time.monotonic() works.", "s": 3, "ev": "for a single service time.monotonic() works", "r": "Suggested monotonic clock correctly for local drift.", "f": "limiter.py", "lines": "8-12"},
            {"num": 4, "q": "What happens if a user makes 10,000 requests in 1 second?", "a": "The deque will grow to 10,000 items until the window expires, using memory proportional to the request spike.", "s": 4, "ev": "deque will grow to 10,000 items until the window expires", "r": "Understands direct memory footprint during burst traffic.", "f": "limiter.py", "lines": "20-25"},
            {"num": 5, "q": "How would you scale this if traffic increases 10x?", "a": "We would probably need Redis to share the counts across multiple app instances.", "s": 3, "ev": "probably need Redis to share the counts across multiple app instances", "r": "Understands need for centralized store, though light on specific Redis primitives.", "f": "limiter.py", "lines": "22-30"},
            {"num": 6, "q": "How did you structure unit tests for window expiry?", "a": "I used parameterized unit tests with small windows so tests don't have to wait a whole minute.", "s": 4, "ev": "parameterized unit tests with small windows", "r": "Good practical testing instincts.", "f": "limiter.py", "lines": "30-40"}
        ]

        asha_evidence = []
        for t in turns_data_asha:
            q_turn = QaTurn(
                turn_id=f"turn_asha_{t['num']}",
                session_id="sess_asha_1",
                turn_number=t["num"],
                type="question",
                level=3,
                node_ref="limiter.py",
                question_text=t["q"],
                expects="text",
                answer_text=t["a"],
                evaluation={"score": t["s"], "confidence": 0.82, "reasoning": t["r"], "evidence_quote": t["ev"], "source_file_path": t["f"], "source_lines": t["lines"], "dimensions": {"understanding": t["s"], "reasoning": t["s"]}, "recruiter_confirmed": True}
            )
            session.add(q_turn)
            asha_evidence.append({
                "claim": f"Performance on turn {t['num']}",
                "turn_number": t["num"],
                "skill_name": "API & Rate Limiting Architecture",
                "where_identified": f"{t['f']} (lines {t['lines']})",
                "project_or_task": "Task Submission: Rate Limiter",
                "question": t["q"],
                "candidate_answer": t["a"],
                "score": t["s"],
                "reasoning": t["r"],
                "quote": t["ev"],
                "evidence_quote": t["ev"],
                "source_file_path": t["f"],
                "source_lines": t["lines"],
                "recruiter_confirmed": True
            })

        prof_asha = Profile(
            session_id="sess_asha_1",
            candidate_id="cand_asha",
            job_id="job_1",
            overall_score=72,
            confidence=0.84,
            recommendation="yes",
            skill_profile={
                "understanding": 3.8,
                "reasoning": 3.7,
                "ownership": 4.8,
                "communication": 4.1,
                "debugging": 3.6,
                "modification": 3.5
            },
            strengths=[
                "Deque is much faster for popping from the front",
                "Two threads might both see that count is under the limit",
                "parameterized unit tests with small windows"
            ],
            concerns=[
                "probably need Redis to share the counts across multiple app instances"
            ],
            evidence=asha_evidence,
            summary="Asha is a solid mid-level backend engineer with dependable coding foundations and clear concurrency instincts. Code is clean and functional; minor gap in advanced distributed caching design."
        )
        session.add(prof_asha)
        print("Created Candidate 2: Asha Rao (Score: 72, Rank: #2, Interview Stage)")

        # ── 7. CANDIDATE 3: ROHAN VERMA (IN-PROGRESS WITH SAVED PROGRESS!) ────────
        cand_rohan = Candidate(
            candidate_id="cand_rohan",
            company_id="co_finleaf",
            name="Rohan Verma",
            email="rohan.v@campus.edu",
            github_url="https://github.com/rohan-v",
            linkedin_text="CS Senior seeking backend internship; built several Python scripts and web apps.",
            status="Reviewed",
            graph_status="ready",
            graph_summary={"nodes": 6, "edges": 8, "skills": ["python", "rest api"]}
        )
        session.add(cand_rohan)
        session.flush()

        sub_rohan = Submission(
            submission_id="sub_rohan_1",
            candidate_id="cand_rohan",
            task_id="task_1",
            notes="Initial submission for Backend Intern challenge."
        )
        session.add(sub_rohan)
        session.flush()

        # In-Progress Session on Turn 3 with active draft progress!
        sess_rohan = DepthSession(
            session_id="sess_rohan_1",
            submission_id="sub_rohan_1",
            status="in_progress",
            max_turns=6,
            state_json={
                "turn_number": 3,
                "scores": [3, 3],
                "confidences": [0.75, 0.70],
                "draft_text": "I would use a lock around the dictionary access so two requests don't write at the exact same millisecond.",
                "draft_code": "with self.lock:\n    if user_id not in self.counts:\n        self.counts[user_id] = 1"
            }
        )
        session.add(sess_rohan)
        session.flush()

        turn_rohan_1 = QaTurn(
            turn_id="turn_rohan_1",
            session_id="sess_rohan_1",
            turn_number=1,
            type="question",
            level=2,
            node_ref="limiter.py",
            question_text="What does your sliding window implementation do when an expired timestamp is found?",
            expects="text",
            answer_text="It loops through the timestamps and removes the ones that are older than the window.",
            evaluation={"score": 3, "confidence": 0.75, "reasoning": "Understands basic eviction loop.", "evidence_quote": "removes the ones that are older than the window", "dimensions": {"understanding": 3, "reasoning": 3}}
        )
        turn_rohan_2 = QaTurn(
            turn_id="turn_rohan_2",
            session_id="sess_rohan_1",
            turn_number=2,
            type="question",
            level=2,
            node_ref="limiter.py",
            question_text="Why did you use time.time() instead of time.monotonic()?",
            expects="text",
            answer_text="time.time() is standard in Python, but I know system clock changes can mess it up.",
            evaluation={"score": 3, "confidence": 0.70, "reasoning": "Aware of system clock drift.", "evidence_quote": "system clock changes can mess it up", "dimensions": {"understanding": 3, "reasoning": 3}}
        )
        # Turn 3 is currently active and waiting for candidate submission (Resumable!)
        turn_rohan_3 = QaTurn(
            turn_id="turn_rohan_3",
            session_id="sess_rohan_1",
            turn_number=3,
            type="question",
            level=2,
            node_ref="limiter.py",
            question_text="How would you protect the shared dictionary from race conditions when two requests arrive simultaneously?",
            expects="text",
            answer_text=None  # Currently active!
        )
        session.add(turn_rohan_1)
        session.add(turn_rohan_2)
        session.add(turn_rohan_3)
        print("Created Candidate 3: Rohan Verma (In-Progress Session on Turn 3 with Saved Draft Progress)")

        # ── 8. CANDIDATE 4: RAVI KUMAR (EVASIVE / LOW SCORE / REJECTED) ───────────
        cand_ravi = Candidate(
            candidate_id="cand_ravi",
            company_id="co_finleaf",
            name="Ravi Kumar",
            email="ravi.k@example.com",
            github_url="https://github.com/ravi-weak",
            linkedin_text="Full stack developer claiming 10+ years architecting enterprise Redis distributed systems and high-throughput microservices.",
            status="Rejected",
            graph_status="ready",
            graph_summary={"nodes": 8, "edges": 10, "skills": ["python", "redis"]}
        )
        session.add(cand_ravi)
        session.flush()

        sub_ravi = Submission(
            submission_id="sub_ravi_1",
            candidate_id="cand_ravi",
            task_id="task_1",
            notes="Copied template rate limiter."
        )
        session.add(sub_ravi)
        session.flush()

        sess_ravi = DepthSession(
            session_id="sess_ravi_1",
            submission_id="sub_ravi_1",
            status="done",
            max_turns=6,
            state_json={"scores": [1, 2, 1, 2, 1, 2], "confidences": [0.7, 0.65, 0.6, 0.65, 0.6, 0.65], "turn_number": 6}
        )
        session.add(sess_ravi)
        session.flush()

        turns_data_ravi = [
            {"num": 1, "q": "Why did you use pop(0) in your sliding window?", "a": "I used pop(0) because it removes the first element from the array in Python.", "s": 1, "ev": "removes the first element from the array", "r": "Failed to recognize O(N) memory shift penalty on pop(0).", "f": "limiter.py", "lines": "12-14"},
            {"num": 2, "q": "How does your code prevent two threads from exceeding the rate limit?", "a": "Python has the Global Interpreter Lock (GIL) so threads are automatically safe.", "s": 1, "ev": "GIL so threads are automatically safe", "r": "Critical misconception: GIL does not prevent application-level TOCTOU races.", "f": "limiter.py", "lines": "15-20"},
            {"num": 3, "q": "In your resume you claimed to build distributed Redis architectures. How did you handle cluster split-brain?", "a": "We just used industry standard best practices and standard cloud configurations.", "s": 1, "ev": "standard best practices and standard cloud configurations", "r": "Evasive non-answer using pure buzzwords with zero technical grounding.", "f": "limiter.py", "lines": "1-5"},
            {"num": 4, "q": "What happens if memory runs out on the server?", "a": "The garbage collector will clean it up automatically.", "s": 2, "ev": "garbage collector will clean it up automatically", "r": "Fails to grasp that global dictionary references prevent garbage collection.", "f": "limiter.py", "lines": "20-25"},
            {"num": 5, "q": "How would you write a test for a 1-minute window?", "a": "I would use time.sleep(60) to wait for 60 seconds.", "s": 1, "ev": "use time.sleep(60) to wait", "r": "Hardcoded 60s sleep creates unacceptable, flaky test suites.", "f": "limiter.py", "lines": "25-30"},
            {"num": 6, "q": "How would you refactor this code to improve performance?", "a": "I would rewrite it in another language or scale up the CPU.", "s": 2, "ev": "scale up the CPU", "r": "Avoided code refactoring in favor of throwing hardware at an O(N) algorithm.", "f": "limiter.py", "lines": "30-35"}
        ]

        ravi_evidence = []
        for t in turns_data_ravi:
            q_turn = QaTurn(
                turn_id=f"turn_ravi_{t['num']}",
                session_id="sess_ravi_1",
                turn_number=t["num"],
                type="question",
                level=2,
                node_ref="limiter.py",
                question_text=t["q"],
                expects="text",
                answer_text=t["a"],
                evaluation={"score": t["s"], "confidence": 0.65, "reasoning": t["r"], "evidence_quote": t["ev"], "source_file_path": t["f"], "source_lines": t["lines"], "dimensions": {"understanding": t["s"], "reasoning": t["s"]}, "flags": ["evasive", "unsupported_claim"], "recruiter_confirmed": False}
            )
            session.add(q_turn)
            ravi_evidence.append({
                "claim": f"Performance on turn {t['num']}",
                "turn_number": t["num"],
                "skill_name": "Distributed Concurrency & Python Memory",
                "where_identified": f"{t['f']} (lines {t['lines']})",
                "project_or_task": "Task Submission: Rate Limiter",
                "question": t["q"],
                "candidate_answer": t["a"],
                "score": t["s"],
                "reasoning": t["r"],
                "quote": t["ev"],
                "evidence_quote": t["ev"],
                "source_file_path": t["f"],
                "source_lines": t["lines"],
                "recruiter_confirmed": False
            })

        prof_ravi = Profile(
            session_id="sess_ravi_1",
            candidate_id="cand_ravi",
            job_id="job_1",
            overall_score=39,
            confidence=0.65,
            recommendation="no",
            skill_profile={
                "understanding": 1.6,
                "reasoning": 1.4,
                "ownership": 1.5,  # Penalized by -3.5 for evasive claims & GIL misconceptions!
                "communication": 2.2,
                "debugging": 1.4,
                "modification": 1.5
            },
            strengths=[],
            concerns=[
                "GIL so threads are automatically safe",
                "standard best practices and standard cloud configurations",
                "use time.sleep(60) to wait"
            ],
            evidence=ravi_evidence,
            summary="Ravi relies heavily on generic industry buzzwords and exhibited critical technical misconceptions regarding the Python GIL and concurrency safety. Significant discrepancy between claimed Redis expertise and actual Depth Check explanations. Ownership score penalized to 1.5."
        )
        session.add(prof_ravi)
        print("Created Candidate 4: Ravi Kumar (Score: 39, Rank: #3, Rejected, Ownership Penalty Applied)")

        session.commit()
        print("\nAll Real Accounts & Activities Seeded Successfully!")

if __name__ == "__main__":
    run_seed()
