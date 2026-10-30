# ProofHire ⚡
### Evidence-Based Technical Hiring Platform
> *"The signal is in the explanation."*  
> Replacing LeetCode memorization and AI-generated resume inflation with practical engineering challenges, AST-grounded Socratic depth interviews, and auditable evidence trails.

---

## 📌 Problem & Motivation

Modern software hiring is broken by AI on both sides:
1. **80% of candidates use LLMs to ace LeetCode & HackerRank screens** without understanding the underlying code or architectural trade-offs.
2. **Resumes are hyper-inflated** with AI-generated buzzwords, making traditional keyword screening completely ineffective.
3. **Current AI interviewers are opaque black boxes** that hallucinate ratings and offer zero recourse or auditability.

**ProofHire solves this.** Passing unit tests proves code runs; **ProofHire proves the human wrote it and understands why it works.** Candidates solve real systems problems in an in-browser sandbox, followed by an adaptive, multi-turn Socratic AI cross-examination grounded in their exact AST (Abstract Syntax Tree) code nodes.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Candidate_Desk["Candidate Desk (:4321 - Astro 5)"]
        UI_Roles["01 / Open Roles"]
        UI_Code["02 / Technical Challenge (Editor)"]
        UI_Depth["03 / Socratic Depth Check (Chat)"]
        UI_Audit["04 / Depth Check History (Ledger)"]
        UI_Graph["05 / Knowledge Graph (Cytoscape)"]
    end

    subgraph Backend_Engine["ProofHire Backend (:8000 - FastAPI)"]
        API_Tasks["Task Generation & Pre-warmed Cache"]
        AST_Parser["AST Code Parser & Ingestion Engine"]
        Graph_Engine["NetworkX MultiDiGraph (AST + Skills)"]
        AI_Socratic["Socratic Evaluator (Gemini Flash)"]
        Scoring_Math["Deterministic Python Scoring Engine"]
        DB_WAL[("SQLite (WAL Mode)")]
    end

    subgraph Recruiter_Portal["Recruiter Portal (:8000/portal)"]
        REC_Dash["Hiring Pipeline Dashboard"]
        REC_Jobs["Role Requisition Management"]
        REC_List["Evidence-Ranked Shortlist"]
        REC_Report["AI Evaluation Report & Radar"]
        REC_Audit["1-Click Human Audit & Dispute Review"]
    end

    UI_Code -->|Submits AST Code| AST_Parser
    AST_Parser --> Graph_Engine
    Graph_Engine --> DB_WAL
    Graph_Engine -->|94% Pruned Context| AI_Socratic
    AI_Socratic --> Scoring_Math
    Scoring_Math --> DB_WAL

    DB_WAL -->|Adaptive 4s Polling| REC_Dash
    DB_WAL --> REC_List
    REC_Audit -->|Confirmed Evidence| DB_WAL
```

---

## ✨ Key Features & Capabilities

### 1. Socratic AST-Grounded Depth Check
* After writing or submitting code, candidates enter an interactive Socratic technical conversation.
* ProofHire cites specific lines and functions (`limiter.py:12` `allow_request`).
* **Instant Evasion Detection:** If a candidate answers `"dk"`, `"idk"`, or gives superficial buzzwords (`"it is standard best practice"`), ProofHire deterministically scores `0/5`, flags `evasive`, and deducts ownership marks mathematically.
* **Verbatim Substring Validation:** ProofHire extracts exact verbatim candidate quotes into an immutable evidence ledger.

### 2. Semantic Knowledge Graph (NetworkX + Cytoscape.js)
* Bridges abstract resume claims with concrete AST syntax nodes:
  $$\text{Candidate} \longrightarrow \text{Project} \longrightarrow \text{File} \longrightarrow \text{AST Function} \longrightarrow \text{Verified Skill}$$
* **94% Token Reduction:** Rather than dumping 50k tokens of entire repositories into LLM prompts, ProofHire extracts only the 1-hop and 2-hop graph neighborhood (~350–400 tokens), delivering sub-second evaluations and slashing API costs.

### 3. Complete Candidate Transparency & Dispute Rights
* Candidates can open the **Depth Check History** ledger to see exactly why marks were deducted.
* Candidates can click **🚩 Report Evaluation Issue** to contest grading, immediately routing the turn to the hiring manager for human audit.

### 4. Real-Time Recruiter Talent Portal
* **Live Synchronization:** The recruiter dashboard updates in real-time without page reloads via an adaptive 4-second background loop.
* **Evidence-Ranked Shortlists:** Candidates are ranked by verified technical quotes rather than resume formatting.
* **1-Click Human Confirmation:** Hiring managers can review contested evaluations and confirm or override evidence with a single click.

### 5. Instant Pre-Warmed Performance (<50ms)
* Pre-compiled starter challenges for distributed systems, backend APIs, and high-performance frontend data grids load instantly without judge waiting time.

---

## 🚀 Getting Started & Running Locally

### Prerequisites
* **Python 3.10+** (Python 3.11 or 3.12 recommended)
* **Node.js 18+** & **npm**

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Tech1824/proofHire.git
cd proofHire
```

---

### Step 2: Configure Environment Variables
Create a `.env` file in the project root:
```env
# Optional Gemini API key (defaults to deterministic local fixtures if omitted)
GEMINI_API_KEY=your_gemini_api_key_here
PUBLIC_USE_MOCKS=false
```

---

### Step 3: Set Up and Run the Python Backend
In your terminal:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed database with real-world demo roles and candidates (Arjun, Asha, Ravi)
python seed_db.py

# 3. Start the FastAPI backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
> The backend server will be running live at **`http://localhost:8000`**.  
> Interactive OpenAPI documentation is available at **`http://localhost:8000/docs`**.

---

### Step 4: Set Up and Run the Astro Frontend
In a **new terminal**:
```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Astro dev server
npm run dev -- --host 0.0.0.0 --port 4321
```
> The candidate desk will be running live at **`http://localhost:4321`**.

---

## 🖥️ Live Portal Endpoints

| Portal | URL | Description |
| :--- | :--- | :--- |
| **Candidate Desk** | [`http://localhost:4321`](http://localhost:4321) | Candidate assessment, live code editor, Socratic depth check, and graph. |
| **Recruiter Portal** | [`http://localhost:8000/portal/dashboard.html`](http://localhost:8000/portal/dashboard.html) | Hiring pipeline dashboard, jobs requisition desk, and candidate audit ledger. |
| **Shortlist & Evidence** | [`http://localhost:8000/portal/shortlist.html`](http://localhost:8000/portal/shortlist.html) | Evidence-ranked candidates with verified quotes and 1-click human approval. |
| **Candidate Comparison** | [`http://localhost:8000/portal/compare.html`](http://localhost:8000/portal/compare.html) | Side-by-side dimensional skill comparison (Arjun vs Ravi). |
| **Backend API Docs** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Interactive Swagger UI for all REST endpoints. |

---

## 🧪 Quick Test & Demo Scenarios

### Scenario A: Test Instant Evasion Detection (`dk`)
1. Go to `http://localhost:4321#depth`.
2. Start a session or use a pre-seeded challenge.
3. Type `"dk"` or `"idk"` in the response field and press **Enter**.
4. **Result:** ProofHire immediately awards `0/5`, flags `evasive`, logs reasoning, and adjusts the running score without hallucinating praise.

### Scenario B: Test High Technical Depth
1. Answer the question referencing AST choices:  
   *"I used a per-user deque with monotonic timestamps so we can pop expired entries from the left in O(1) time without lock contention."*
2. **Result:** ProofHire extracts the exact verbatim substring as verified evidence, updates the running score to `88/100`, and links the quote in the Recruiter Portal.

### Scenario C: 1-Click Demo Profiles (Zero Waiting for Pitch Day)
* In `http://localhost:4321#candidate`, choose from 1-click pre-seeded profiles:
  * **Arjun Mehta** (Score: 88, Rank #1, Shortlisted)
  * **Asha Rao** (Score: 72, Active Interview)
  * **Ravi Kumar** (Score: 39, Flagged/Rejected for evasive answers)

---

## 📂 Project Directory Structure

```text
proofHire/
├── backend/                  # FastAPI REST API services
│   ├── routes/               # API route handlers (jobs, depth, candidates, company, etc.)
│   ├── fakes.py              # Zero-latency deterministic fixture mocks
│   └── main.py               # Application entrypoint & CORS middleware
├── ai/                       # Core AI & Knowledge Graph engine
│   ├── graph.py              # NetworkX AST Knowledge Graph builder
│   ├── evaluator.py          # Socratic depth interviewer & deterministic scorer
│   └── api.py                # Graph queries & token-pruned context extraction
├── db/                       # Database models & persistence
│   ├── models.py             # SQLModel tables (Job, Candidate, QaTurn, Profile, etc.)
│   └── crud.py               # Concurrency-safe SQLite engine with WAL mode
├── frontend/                 # Candidate Portal (Astro 5 Island Architecture)
│   ├── src/
│   │   ├── pages/            # Astro static entry routes
│   │   ├── scripts/app.js    # Client-side router, Socratic chat, Cytoscape graph
│   │   └── lib/api.js        # Resilient API communication layer
│   └── package.json
├── proofhire-company-portal/ # Recruiter Talent Portal (ATS & Audit Ledger)
│   ├── dashboard.html        # Company pipeline overview
│   ├── shortlist.html        # Evidence-ranked candidates
│   ├── ai-report.html        # In-depth candidate radar & dispute review
│   ├── compare.html          # Head-to-head candidate evaluation
│   └── js/portal.js          # Live 4s polling sync engine
├── JUDGES_WALKTHROUGH.md     # Complete Hackathon Demo & Q&A presentation guide
└── seed_db.py                # Database seeding script for demo data
```

---

## 🛡️ License

MIT License. Designed and built with ❤️ for evidence-first software engineering.
