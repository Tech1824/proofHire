# PRD: ProofHire

## 1. One-line pitch
ProofHire finds people who **understand their work**, not people who write good resumes. Candidates do a real task for the company, then an AI "depth check" asks about *their own solution*. Companies get a shortlist backed by evidence.

## 2. The problem
- Resumes are easy to polish and easy to fake.
- AI tools can write take-home tasks in minutes. A correct answer no longer proves skill.
- Companies waste hours interviewing people who cannot explain what they submitted.

## 3. Users
| User | Goal |
|---|---|
| Recruiter / hiring manager | Get a short, trustworthy list and know *why* each person is on it |
| Candidate | Show real skill fairly, even without a famous college or company on the resume |

## 4. Core flow (the demo)
1. Recruiter picks a job (from 2 fictional jobs).
2. Candidate enters GitHub, pasted LinkedIn text, and projects. System builds a **knowledge graph** of their work.
3. System generates a **company-specific task** from the job description.
4. Candidate submits a solution.
5. **Depth check** starts: adaptive questions about the candidate's own code, then a small modification or debugging task.
6. After 4-6 turns the system stops and builds a **skill profile**.
7. Recruiter opens the **shortlist**: ranked candidates, scores, strengths, concerns, and **exact quotes** as evidence.

## 5. Features
**Must have (MVP)**
- Jobs list and detail
- Candidate submit form and graph build
- Task generation (or preloaded task)
- Submission upload (paste code)
- Adaptive depth check (question, judge, next question, stop rule)
- Evidence-linked scoring and shortlist
- Demo mode (replays cached AI answers)

**Should have**
- Graph view page (nodes and edges)
- Token-savings meter ("this question used 400 tokens, not 6,800")
- Ollama fallback when the internet is down

**Could have**
- Resume-claim vs answer consistency check
- Embedding-based skill matching (local `all-MiniLM-L6-v2`)
- Safe code run for seed modification tasks

**Will NOT build**
Login, payments, deployment, email, real LinkedIn scraping, AI-generated-content detection, video proctoring.

## 6. What makes it different (say this to judges)
1. **Depth check, not a quiz.** Questions come from the candidate's own code.
2. **Adaptive.** Strong answer -> harder node. Vague answer -> follow-up on the same node.
3. **Evidence-based.** Every score links to a real quote. No black-box number.
4. **Efficient.** Graph retrieval sends only the needed code to the AI. Cheaper, faster, less hallucination.
5. **Tool-agnostic.** We do not police AI use. We test understanding.

## 7. Responsible AI (judges like this)
- The candidate can see their own evidence.
- The LLM never makes the final hire decision. It scores single answers; **code** calculates the result; a **human** decides.
- Communication is a small part of the score, so non-native English speakers are not punished.
- Candidate answers are treated as data. Instructions hidden in answers ("give me 5/5") are ignored.
- Scores show **confidence**. Low confidence says "needs more evidence", not "reject".

## 8. Success metrics (for the demo)
- Strong candidate scores at least 75. Weak candidate (AI-copied code, cannot explain) scores under 45.
- Full flow runs under 6 minutes live.
- Zero crashes in 3 rehearsal runs.
- Every displayed score shows a quote.

## 9. Constraints
- Free tools only. Local laptops only. Python + Astro + HTML.
- Internet is needed only for LLM calls; `DEMO_MODE` works with no internet.
- Team has little coding experience. Keep the code simple and commented.
