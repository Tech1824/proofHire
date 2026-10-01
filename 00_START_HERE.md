# ProofHire: Team Playbook (v2)

Read this first. Then give the files in `docs/` to every IDE.

## What changed from v1 (honest corrections)
1. **"Offline" is really "local-first".** Everything runs on your laptops. Only LLM calls go to the internet (Gemini). A small local model (Ollama) is the safety net if Wi-Fi dies.
2. **Advanced only where judges can see it.** Advanced: graph retrieval, adaptive questioning, evidence-linked scoring, prompt-injection defense, token-savings meter. Everything else stays boring (SQLite, plain HTML).
3. **We do NOT claim "AI detection".** Our claim: *we test real understanding, no matter what tools were used.*
4. **New file `INTERFACES.md`.** Python function signatures between folders. Most vibe-coding teams fail because two IDEs guess the same function differently. This file stops that.
5. **Scoring is now real math, not vibes.** The LLM judges one answer at a time. Python code does the averaging and the ranking.
6. **LinkedIn is pasted text, not scraped.** Scraping LinkedIn breaks its rules and breaks often.
7. **Running candidate code is unsafe.** Modification tasks are judged by the LLM. Only seed tasks may run in a subprocess with a timeout (stretch goal).

## Team and owners
| Person | Owns folder | Also responsible for |
|---|---|---|
| Backend builder (**Integrator**) | `backend/`, `run.py` | Owns `API_CONTRACT.md`. Merges all PRs. |
| Frontend builder | `frontend/` | Demo look and feel. Mocks in `frontend/src/mocks/`. |
| AI/ML person | `ai/` | Graph, questioner, judge, scoring, LLM router. |
| Database person | `db/`, `data/seed/` | Schema, CRUD, seed data, cache table. |
| Tester | `tests/` | Demo rehearsal, demo script, bug reports. |

Rule: **you only edit your own folder.** Need a change elsewhere? Tell the owner in the team chat.

## Setup (everyone, once)
```
git clone <repo> && cd proofhire
python -m venv .venv
# Windows: .venv\Scripts\activate    Mac/Linux: source .venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic sqlmodel litellm networkx httpx pytest python-dotenv
cd frontend && npm install && cd ..
```
Optional local fallback model: install Ollama, then `ollama pull qwen2.5:3b`.

Create `.env` in the repo root (never commit it; add to `.gitignore`):
```
GEMINI_API_KEY=your_key_from_aistudio
OLLAMA_BASE=http://localhost:11434
DEMO_MODE=false
```
Get a free key at Google AI Studio. Free limits change and are low, so **caching (in the DB) is mandatory**.

## `run.py` (backend builder writes this; one command starts everything)
```python
import subprocess, sys, os
procs = [
    subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--reload"]),
    subprocess.Popen(["npm", "run", "dev", "--", "--port", "4321"], cwd="frontend", shell=(os.name == "nt")),
]
try:
    for p in procs: p.wait()
except KeyboardInterrupt:
    for p in procs: p.terminate()
```

## Timeline (example for 24h; scale the percentages)
| Phase | Time | What happens | Exit check |
|---|---|---|---|
| 0. Freeze | 0-2h | Everyone reads docs. Fix problems together. **Freeze the contract.** | Contract signed off in chat |
| 1. Parallel build | 2-10h | Frontend uses mocks. Backend returns fake data. AI works from seed. DB builds schema + seed. | Each folder passes its own checks |
| 2. Integrate | 10-16h | Replace fakes with real calls, one endpoint at a time (order below). | Full flow works with `DEMO_MODE=true` |
| 3. Harden | 16-20h | Tester breaks things. Fix bugs. Cache all demo LLM answers. | 3 clean demo runs in a row |
| 4. Rehearse | 20-24h | No new features. Practice the demo 5 times. | Everyone knows their part |

**Integration order:** health -> jobs -> candidates (graph) -> tasks -> submissions -> depth start -> depth answer -> shortlist.

## Git rules
- Branches: `frontend`, `backend`, `ai`, `db`, `tests`. Merge to `main` via pull request. Integrator merges.
- Commit small and often. Pull `main` every hour.
- Never commit `.env`, `proofhire.db`, `.venv`, `node_modules`.
- Tag `demo-ready` when a build passes 3 clean runs. Demo from that tag only.

## How to use your IDE (simple)
1. Open the repo folder in your IDE.
2. Paste your prompt from `PROMPTS.md`.
3. Tell the IDE: "Also read every file in `docs/`." Most IDEs let you attach files or use `@docs`.
4. Ask for **one small piece at a time** and run it before asking for the next.
5. When it breaks, paste the **full error** into the IDE. Do not describe it.
6. Never accept a change to `docs/` from your IDE. Docs change only by team decision.

## If time runs out: cut list (cut from the bottom first)
Keep: jobs, candidate submit, depth check, shortlist, demo mode.
Cut 1st: graph visualization page. Cut 2nd: task generation (use a pre-written task). Cut 3rd: Ollama fallback. Cut 4th: modification/debug turns (keep questions).
