# ProofHire V2 Roadmap

This document outlines the sequential phases to elevate ProofHire from a prototype to an enterprise-grade technical assessment platform.

## Phase E: Job Details & Recruiter UX (Immediate)
* **Goal:** Flesh out the recruiter's workspace to handle realistic job metadata.
* **Backend Tasks:** 
  - Update `JobCreate` and `JobResponse` schemas in `backend/schemas.py`.
  - Add fields: `work_mode`, `employment_type`, `years_experience`, and `responsibilities`.
  - Update `db/models.py` to persist these fields.
  - Update `seed_db.py` to populate realistic data.
* **Frontend Tasks:** 
  - Update `app.js` to render tags for Work Mode and Employment Type.
  - Render the Responsibilities list dynamically.

## Phase F: Resume & Document Ingestion
* **Goal:** Remove the clunky "paste text" requirement and allow candidates to drop a standard resume.
* **Backend Tasks:**
  - Create a new endpoint `POST /api/upload-resume`.
  - Implement a basic text extractor (e.g., PyPDF2 or direct text reading).
  - Update `CandidateCreate` to accept raw parsed text instead of specifically `linkedin_text`.
* **Frontend Tasks:**
  - Modify the Intake form to include a `<input type="file">`.
  - Wire the upload progress to the UI.

## Phase G: AI Evidence Traceability (The "Anti-Hallucination" Update)
* **Goal:** Make every AI hiring recommendation explicitly auditable by tracing it back to source code.
* **Backend Tasks:**
  - Modify the prompt in `ai/api.py` to require the LLM to return `file_path` and `line_numbers` alongside its evidence quotes.
* **Frontend Tasks:**
  - Update the Shortlist UI. When a recruiter hovers over a "Strength" or "Evidence" claim, display a tooltip or modal showing the exact code snippet the AI based its decision on.

## Phase H: Asynchronous Ingestion Architecture
* **Goal:** Prevent the UI from locking up while fetching massive GitHub repositories.
* **Backend Tasks:**
  - Implement a background task manager (FastAPI BackgroundTasks or a lightweight thread queue).
  - Change `POST /api/candidates` to return a `202 Accepted` with a `job_id`.
  - Create a `GET /api/candidates/{id}/status` polling endpoint.
* **Frontend Tasks:**
  - Update the Intake UI to show a live progress bar ("Fetching GitHub...", "Building Graph...", "Ready").
