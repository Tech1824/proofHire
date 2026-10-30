from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
import io
import re
import pypdf
from backend.schemas import CandidateCreate, CandidateCreateResponse, CandidateResponse, GraphViewResponse
from backend.fakes import is_fake, fake_db, fake_ai
import concurrent.futures

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

@router.post("/parse-resume")
async def parse_resume_file(file: UploadFile = File(...)):
    filename = file.filename or "resume.txt"
    content_bytes = await file.read()
    text = ""
    
    if filename.lower().endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF resume: {str(e)}")
    else:
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1", errors="ignore")
            
    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file contains no readable text.")
        
    KNOWN_SKILLS = [
        "python", "fastapi", "django", "flask", "sql", "sqlite", "postgresql", "mysql", "redis",
        "docker", "kubernetes", "rest api", "graphql", "grpc", "distributed systems", "concurrency",
        "asyncio", "javascript", "typescript", "react", "next.js", "vue", "node.js", "aws", "gcp",
        "azure", "git", "ci/cd", "microservices", "kafka", "rabbitmq", "linux", "c++", "go", "rust",
        "java", "spring boot", "system design", "html/css", "tailwind", "unit testing", "pytest"
    ]
    text_lower = text.lower()
    detected_skills = []
    for s in KNOWN_SKILLS:
        pattern = rf"\b{re.escape(s)}\b" if len(s) <= 4 else re.escape(s)
        if re.search(pattern, text_lower):
            detected_skills.append(s)
            
    return {
        "status": "ok",
        "filename": filename,
        "text": text.strip(),
        "skills": detected_skills,
        "char_count": len(text)
    }


@router.get("")
@router.get("/", include_in_schema=False)
def list_all_candidates():
    from db import crud
    return crud.list_candidates()

@router.post("/{candidate_id}/status")
def update_cand_status(candidate_id: str, payload: dict):
    from db import crud
    status = payload.get("status", "Reviewed")
    crud.update_candidate_status(candidate_id, status)
    return {"status": "ok", "candidate_id": candidate_id, "new_status": status}

def process_candidate_bg(candidate_id: str, cand_dict: dict):
    from db import crud
    from ai import api as ai_api
    from ingest.github import fetch_github_profile
    from ingest.linkedin import extract_linkedin_claims
    from ai.profile_merger import merge_profile
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_gh = executor.submit(fetch_github_profile, cand_dict.get("github_url"), None, cand_dict.get("github_token"))
            future_li = executor.submit(extract_linkedin_claims, cand_dict.get("linkedin_text"))
            
            gh_data = future_gh.result()
            li_data = future_li.result()
            
        merged_cand_dict = merge_profile(cand_dict, gh_data, li_data)
        
        # Update the existing placeholder candidate with fetched data
        merged_cand_dict["candidate_id"] = candidate_id
        crud.update_candidate(candidate_id, merged_cand_dict)
        
        summary = ai_api.build_graph(candidate_id)
        
        crud.update_candidate(candidate_id, {"graph_status": "ready", "graph_summary": summary})
    except Exception as e:
        crud.update_candidate(candidate_id, {"graph_status": "failed", "error": str(e)})

@router.post("", response_model=CandidateCreateResponse, status_code=202)
@router.post("/", response_model=CandidateCreateResponse, status_code=202, include_in_schema=False)
def create_candidate(candidate: CandidateCreate, background_tasks: BackgroundTasks):
    cand_dict = candidate.model_dump()
    
    if is_fake():
        cand = fake_db.create_candidate(cand_dict)
        summary = fake_ai.build_graph(cand["candidate_id"])
        return {
            "candidate_id": cand["candidate_id"],
            "graph_status": "ready",
            "graph_summary": summary
        }
    else:
        from db import crud
        # Create a placeholder candidate
        cand_dict["graph_status"] = "processing"
        cand = crud.create_candidate(cand_dict)
        
        background_tasks.add_task(process_candidate_bg, cand["candidate_id"], cand_dict)
        
        return {
            "candidate_id": cand["candidate_id"],
            "graph_status": "processing",
            "graph_summary": None
        }

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: str):
    if is_fake():
        cand = fake_db.get_candidate(candidate_id)
    else:
        from db import crud
        cand = crud.get_candidate(candidate_id)
        
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} does not exist")
        
    return cand

@router.get("/{candidate_id}/graph", response_model=GraphViewResponse)
def get_graph_view(candidate_id: str):
    if is_fake():
        view = fake_ai.get_graph_view(candidate_id)
    else:
        from ai import api as ai_api
        view = ai_api.get_graph_view(candidate_id)
    
    if not view:
        raise HTTPException(status_code=404, detail=f"Graph for {candidate_id} not found")
        
    return view


@router.put("/{candidate_id}")
def update_candidate_details(candidate_id: str, payload: dict):
    from db import crud
    cand = crud.get_candidate(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    crud.update_candidate(candidate_id, payload)
    return crud.get_candidate(candidate_id)

@router.post("/{candidate_id}/resync")
def resync_candidate_github(candidate_id: str, background_tasks: BackgroundTasks, payload: dict = None):
    from db import crud
    cand = crud.get_candidate(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    cand_dict = dict(cand)
    if payload:
        if payload.get("github_token"):
            cand_dict["github_token"] = payload.get("github_token")
        if payload.get("github_url"):
            cand_dict["github_url"] = payload.get("github_url")
            crud.update_candidate(candidate_id, {"github_url": payload.get("github_url")})
            
    crud.update_candidate(candidate_id, {"graph_status": "processing"})
    background_tasks.add_task(process_candidate_bg, candidate_id, cand_dict)
    return {
        "status": "processing",
        "candidate_id": candidate_id,
        "message": "Re-fetching repositories from GitHub and rebuilding knowledge graph."
    }

@router.get("/{candidate_id}/evaluation")
def get_candidate_evaluation(candidate_id: str, job_id: str = "job_1"):
    from db.crud import engine, Session, select, Candidate, Profile, Submission, DepthSession, QaTurn
    with Session(engine) as session:
        cand = session.get(Candidate, candidate_id)
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        profile = session.exec(select(Profile).where(
            Profile.candidate_id == candidate_id,
            Profile.job_id == job_id
        )).first()
        
        sub = session.exec(select(Submission).where(
            Submission.candidate_id == candidate_id
        ).order_by(Submission.created_at.desc())).first()
        
        sess_data = None
        turns_data = []
        if sub:
            ds = session.exec(select(DepthSession).where(
                DepthSession.submission_id == sub.submission_id
            )).first()
            if ds:
                sess_data = ds.model_dump()
                turns = session.exec(select(QaTurn).where(
                    QaTurn.session_id == ds.session_id
                ).order_by(QaTurn.turn_number)).all()
                turns_data = [t.model_dump() for t in turns]
                sess_data["turns"] = turns_data
                
        prof_dict = profile.model_dump() if profile else None
        
        # Calculate rank across job
        rank = None
        if prof_dict:
            all_profs = session.exec(select(Profile).where(Profile.job_id == job_id).order_by(Profile.overall_score.desc())).all()
            for i, p in enumerate(all_profs):
                if p.candidate_id == candidate_id:
                    rank = i + 1
                    break
                    
        return {
            "candidate": cand.model_dump(),
            "profile": prof_dict,
            "rank": rank,
            "submission": sub.model_dump() if sub else None,
            "session": sess_data
        }
