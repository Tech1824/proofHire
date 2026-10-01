# GOALS: Requirements and "Definition of Done"

## Product goals (ranked)
1. **The demo never fails.** (demo mode, cache, fallback model)
2. **The adaptive depth check is visibly smart.** Judges see the next question change because of the last answer.
3. **Every score has evidence.** A quote is shown next to each number.
4. **Looks like a real product.** Terminal theme, animations, clean layout.
5. **Simple code.** A teammate can read any file in 5 minutes.

## Requirements by role

### Backend (FastAPI)
- [ ] All endpoints in `API_CONTRACT.md` exist and return the exact JSON shapes
- [ ] Routes are thin: validate input, call `ai/` or `db/`, return output
- [ ] CORS allows `http://localhost:4321`
- [ ] Every error returns the standard error shape
- [ ] `GET /api/health` reports which LLM aliases are reachable
- [ ] Demo mode switch works at runtime
- [ ] `/docs` (auto Swagger page) works, because the tester and frontend use it

### Frontend (Astro)
- [ ] 6 pages: Jobs, Candidate, Task, Depth Check, Shortlist, Graph
- [ ] Runs on mocks first, then the real API (one switch: `PUBLIC_USE_MOCKS`)
- [ ] AI messages type out character by character
- [ ] Live score bar and evidence panel update after each answer
- [ ] Loading, empty and error states on every page
- [ ] Works at 1366x768 (typical projector/laptop)

### AI/ML
- [ ] `graph.py`: builds graph from code and text, returns small subgraphs
- [ ] `questioner.py`: makes the next turn from graph + state
- [ ] `judge.py`: strict JSON score, evidence quote must exist in the answer
- [ ] `controller.py`: chooses next node and level, decides when to stop
- [ ] `profile.py`: pure-Python math, then one LLM call for the written summary
- [ ] `llm.py`: LiteLLM router with `fast` / `smart` / `local` and fallbacks
- [ ] Cache all LLM calls by prompt hash
- [ ] Injection defense and JSON retry (one retry)

### Database
- [ ] `DB_SCHEMA.md` finished in hour 1
- [ ] Models and CRUD helpers exactly as in `INTERFACES.md`
- [ ] `seed.py` is safe to run many times and resets the demo data
- [ ] `llm_cache` table with hit counter

### Tester
- [ ] One pytest per endpoint (happy path + bad input)
- [ ] One end-to-end test on seed data
- [ ] Tests for: empty answer, huge answer, injection text, LLM timeout, unknown ID
- [ ] Demo checklist and demo script rehearsed 5 times
- [ ] Bug reports sent to the folder owner with: steps, expected, actual, error text

## Numbers we care about
| Metric | Target |
|---|---|
| Time from answer to next question (cached) | < 1 s |
| Time from answer to next question (live `fast`) | < 6 s |
| Depth check length | 4-6 turns |
| Tokens per question with graph vs. full code | at least 60% fewer |
| Strong seed candidate score | >= 75 |
| Weak seed candidate score | <= 45 |
