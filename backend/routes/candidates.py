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
        li_text = cand_dict.get("resume_text") or cand_dict.get("linkedin_text") or ""
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_gh = executor.submit(fetch_github_profile, cand_dict.get("github_url"), None, cand_dict.get("github_token"))
            future_li = executor.submit(extract_linkedin_claims, li_text)
            
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
    import ast
    from db.crud import engine, Session, select, Submission, DepthSession, QaTurn, Candidate, Profile
    
    if is_fake():
        view = fake_ai.get_graph_view(candidate_id)
    else:
        from ai import api as ai_api
        view = ai_api.get_graph_view(candidate_id)
    
    if not view:
        view = {"nodes": [], "edges": []}

    nodes = list(view.get("nodes", []))
    edges = list(view.get("edges", []))
    
    # Load candidate submission & depth sessions to enrich AST provenance
    with Session(engine) as session:
        cand = session.get(Candidate, candidate_id)
        sub = session.exec(select(Submission).where(
            Submission.candidate_id == candidate_id
        ).order_by(Submission.created_at.desc())).first()
        
        sub_dict = None
        if sub:
            from db import crud
            sub_dict = crud.get_submission(sub.submission_id)

        turns = []
        if sub:
            ds = session.exec(select(DepthSession).where(
                DepthSession.submission_id == sub.submission_id
            ).order_by(DepthSession.created_at.desc())).first()
            if ds:
                turns = session.exec(select(QaTurn).where(
                    QaTurn.session_id == ds.session_id
                ).order_by(QaTurn.turn_number)).all()

        profile = session.exec(select(Profile).where(
            Profile.candidate_id == candidate_id
        ).order_by(Profile.overall_score.desc())).first()

        overall_score = profile.overall_score if profile else 60.0
        
        # If graph has no function nodes, extract AST directly from candidate submission
        has_functions = any(n.get("type") in ("function", "method") for n in nodes)
        if not has_functions and sub_dict and sub_dict.get("files"):
            files = sub_dict.get("files", [])
            file_node_id = f"file:submission:{files[0].get('path', 'solution.py')}"
            if not any(n.get("id") == file_node_id for n in nodes):
                nodes.append({
                    "id": file_node_id,
                    "type": "file",
                    "label": files[0].get("path", "solution.py"),
                    "weight": 1.0,
                    "status": "verified"
                })
            
            for file_entry in files:
                path = file_entry.get("path", "solution.py")
                code_text = file_entry.get("content", "")
                f_id = f"file:submission:{path}"
                try:
                    tree = ast.parse(code_text)
                    for item in ast.iter_child_nodes(tree):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            fn_id = f"func:{path}::{item.name}"
                            code_lines = code_text.split('\n')[item.lineno - 1 : item.end_lineno]
                            nodes.append({
                                "id": fn_id,
                                "type": "function",
                                "label": item.name,
                                "weight": 1.0,
                                "code": "\n".join(code_lines),
                                "line_range": f"L{item.lineno}-L{item.end_lineno}"
                            })
                            edges.append({"source": f_id, "target": fn_id, "type": "contains"})
                        elif isinstance(item, ast.ClassDef):
                            cl_id = f"class:{path}::{item.name}"
                            code_lines = code_text.split('\n')[item.lineno - 1 : item.end_lineno]
                            nodes.append({
                                "id": cl_id,
                                "type": "class",
                                "label": item.name,
                                "weight": 1.0,
                                "code": "\n".join(code_lines),
                                "line_range": f"L{item.lineno}-L{item.end_lineno}"
                            })
                            edges.append({"source": f_id, "target": cl_id, "type": "contains"})
                            for method in ast.iter_child_nodes(item):
                                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    m_id = f"func:{path}::{item.name}.{method.name}"
                                    m_lines = code_text.split('\n')[method.lineno - 1 : method.end_lineno]
                                    nodes.append({
                                        "id": m_id,
                                        "type": "function",
                                        "label": f"{item.name}.{method.name}",
                                        "weight": 1.0,
                                        "code": "\n".join(m_lines),
                                        "line_range": f"L{method.lineno}-L{method.end_lineno}"
                                    })
                                    edges.append({"source": cl_id, "target": m_id, "type": "contains"})
                except Exception:
                    pass

    # Enrich nodes with depth check evaluations and statuses
    cleaned_nodes = []
    seen_ids = set()
    for n in nodes:
        nid = str(n.get("id"))
        if nid in seen_ids:
            continue
        seen_ids.add(nid)

        ntype = str(n.get("type", "concept"))
        nlabel = str(n.get("label", nid))
        code_snip = n.get("code")
        status = n.get("status")
        evidence = n.get("evidence")
        line_range = n.get("line_range")

        # Correlate with depth turns if available
        matched_turn = None
        for t in turns:
            if t.node_ref and t.node_ref in (nid, nlabel):
                matched_turn = t
                break
            if nlabel.lower() in (t.question_text or "").lower():
                matched_turn = t
                break
        
        if matched_turn:
            ev = matched_turn.evaluation or {}
            eval_score = float(ev.get("score") if ev.get("score") is not None else 3.0)
            flags = ev.get("flags") or []
            if eval_score >= 4.0:
                status = "verified"
            elif eval_score <= 2.0 or any(f in ("evasive", "inaccurate", "surface_level") for f in flags):
                status = "flagged"
            else:
                status = "pending"
            reason = ev.get("reasoning") or "Evaluated in depth check."
            quote = ev.get("evidence_quote") or matched_turn.answer_text or "N/A"
            evidence = f"Turn {matched_turn.turn_number} ({eval_score}/5): {reason} Candidate quote: “{quote}”"
        elif not status:
            if ntype in ("file", "candidate"):
                status = "verified"
            elif ntype in ("function", "class"):
                # Inherit from overall candidate score
                if overall_score >= 70:
                    status = "verified"
                elif overall_score < 40:
                    status = "flagged"
                else:
                    status = "pending"
            else:
                status = "verified"

        cleaned_nodes.append({
            "id": nid,
            "type": ntype,
            "label": nlabel,
            "weight": float(n.get("weight") or 1.0),
            "code": code_snip,
            "status": status,
            "evidence": evidence,
            "line_range": line_range
        })

    cleaned_edges = []
    seen_edges = set()
    for e in edges:
        src = str(e.get("source"))
        tgt = str(e.get("target"))
        etype = str(e.get("type", "relates"))
        key = (src, tgt, etype)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        cleaned_edges.append({
            "source": src,
            "target": tgt,
            "type": etype
        })
        
    return {"nodes": cleaned_nodes, "edges": cleaned_edges}


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
            
        profile = session.exec(
            select(Profile)
            .where(Profile.candidate_id == candidate_id)
            .order_by(Profile.overall_score.desc(), Profile.session_id.desc())
        ).first()
        
        target_job = profile.job_id if profile and profile.job_id else job_id
        
        sub = session.exec(select(Submission).where(
            Submission.candidate_id == candidate_id
        ).order_by(Submission.created_at.desc())).first()
        
        sess_data = None
        turns_data = []
        if sub:
            ds = session.exec(select(DepthSession).where(
                DepthSession.submission_id == sub.submission_id
            ).order_by(DepthSession.created_at.desc())).first()
            if ds:
                sess_data = ds.model_dump()
                turns = session.exec(select(QaTurn).where(
                    QaTurn.session_id == ds.session_id
                ).order_by(QaTurn.turn_number)).all()
                turns_data = [t.model_dump() for t in turns]
                sess_data["turns"] = turns_data
                
        prof_dict = profile.model_dump() if profile else None
        
        # Calculate rank across target job pipeline
        rank = None
        if prof_dict:
            all_profs = session.exec(
                select(Profile)
                .where(Profile.job_id == target_job)
                .order_by(Profile.overall_score.desc())
            ).all()
            for i, p in enumerate(all_profs):
                if p.candidate_id == candidate_id:
                    rank = i + 1
                    break
            if rank is None:
                rank = 1
                    
        return {
            "candidate": cand.model_dump(),
            "profile": prof_dict,
            "rank": rank,
            "submission": sub.model_dump() if sub else None,
            "session": sess_data
        }
