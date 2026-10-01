# AGENTS.md: rules every IDE/AI agent must follow

You are helping a beginner team build ProofHire in a short hackathon.

## Always
1. Read every file in `docs/` before writing code. They are the source of truth.
2. Edit **only** your owner's folder (given in your prompt). If you need a change elsewhere, stop and tell the human which teammate to ask.
3. **Never edit `docs/`.** If the contract seems wrong, tell the human and explain why.
4. Use the exact endpoint paths, JSON field names, function names and signatures from `API_CONTRACT.md` and `INTERFACES.md`.
5. Keep code simple. Small functions. Clear names. A short comment on every function saying what it does in plain English.
6. Build one small piece at a time. After each piece, tell the human the exact command to run and what they should see.
7. Handle errors. Never let one bad input crash the server. Return the standard error shape.
8. Free tools only. No paid services, no accounts that need a credit card.
9. Do not add new libraries without asking the human. Prefer the ones listed in `00_START_HERE.md`.
10. Never hardcode secrets. Read them from `.env`.

## Never
- No login, no deployment, no Docker (unless asked).
- No scraping LinkedIn or any site that forbids it.
- No running candidate code with `exec` or `eval`. (Only seed tasks may run in a subprocess with a timeout, and only if the human asks.)
- No claims that we "detect AI-written code".
- No giant rewrites. If a file needs a rewrite, explain first.

## Style
- Python 3.11+, type hints on public functions, `snake_case`.
- Frontend: plain HTML/CSS/JS inside Astro components. No React/Vue/Tailwind unless told.
- Every module has a `if __name__ == "__main__":` demo or a test so it can be checked alone.

## When you finish a task, reply with
1. What you built (3 lines max)
2. Files changed
3. Command to test it
4. What is still fake or missing
