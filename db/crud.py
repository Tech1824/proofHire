import json
from typing import Optional
from sqlmodel import Session, create_engine, select
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import event
from sqlalchemy.engine import Engine

from db.models import (
    Job, Candidate, Project, CodeFile, Task, Submission,
    DepthSession, QaTurn, Profile, LlmCache, Setting
)

sqlite_file_name = "proofhire.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

engine = create_engine(sqlite_url)

# Jobs
def create_job(data: dict) -> dict:
    with Session(engine) as session:
        job = Job(**data)
        session.add(job)
        session.commit()
        session.refresh(job)
        return job.model_dump()

def list_jobs() -> list[dict]:
    with Session(engine) as session:
        jobs = session.exec(select(Job)).all()
        return [j.model_dump() for j in jobs]

def get_job(job_id: str) -> dict | None:
    with Session(engine) as session:
        job = session.get(Job, job_id)
        return job.model_dump() if job else None

# Candidates, projects, files
def create_candidate(data: dict) -> dict:
    with Session(engine) as session:
        projects_data = data.pop("projects", [])
        candidate = Candidate(**data)
        session.add(candidate)
        session.flush()
        
        for p_data in projects_data:
            files_data = p_data.pop("files", [])
            project = Project(**p_data, candidate_id=candidate.candidate_id)
            session.add(project)
            session.flush()
            for f_data in files_data:
                file_obj = CodeFile(**f_data, project_id=project.project_id)
                session.add(file_obj)
        session.commit()
        session.refresh(candidate)
        
        # reconstruct the nested dict to return
        cand_dict = candidate.model_dump()
        cand_dict["projects"] = []
        projs = session.exec(select(Project).where(Project.candidate_id == candidate.candidate_id)).all()
        for p in projs:
            p_dict = p.model_dump()
            files = session.exec(select(CodeFile).where(CodeFile.project_id == p.project_id)).all()
            p_dict["files"] = [f.model_dump() for f in files]
            cand_dict["projects"].append(p_dict)
            
        return cand_dict

def get_candidate(candidate_id: str) -> dict | None:
    with Session(engine) as session:
        candidate = session.get(Candidate, candidate_id)
        if not candidate:
            return None
        cand_dict = candidate.model_dump()
        cand_dict["projects"] = []
        projs = session.exec(select(Project).where(Project.candidate_id == candidate_id)).all()
        for p in projs:
            p_dict = p.model_dump()
            files = session.exec(select(CodeFile).where(CodeFile.project_id == p.project_id)).all()
            p_dict["files"] = [f.model_dump() for f in files]
            cand_dict["projects"].append(p_dict)
        return cand_dict

def save_graph(candidate_id: str, graph_json: dict, graph_summary: dict, status: str = "ready") -> None:
    with Session(engine) as session:
        candidate = session.get(Candidate, candidate_id)
        if candidate:
            candidate.graph_json = graph_json
            candidate.graph_summary = graph_summary
            candidate.graph_status = status
            session.add(candidate)
            session.commit()

def load_graph(candidate_id: str) -> dict | None:
    with Session(engine) as session:
        candidate = session.get(Candidate, candidate_id)
        if candidate and candidate.graph_json:
            return candidate.graph_json
        return None

# Tasks and submissions
def create_task(data: dict) -> dict:
    with Session(engine) as session:
        task = Task(**data)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task.model_dump()

def get_task(task_id: str) -> dict | None:
    with Session(engine) as session:
        task = session.get(Task, task_id)
        return task.model_dump() if task else None

def create_submission(data: dict) -> dict:
    with Session(engine) as session:
        files_data = data.pop("files", [])
        submission = Submission(**data)
        session.add(submission)
        session.flush()
        
        for f_data in files_data:
            file_obj = CodeFile(**f_data, submission_id=submission.submission_id)
            session.add(file_obj)
        session.commit()
        session.refresh(submission)
        
        sub_dict = submission.model_dump()
        files = session.exec(select(CodeFile).where(CodeFile.submission_id == submission.submission_id)).all()
        sub_dict["files"] = [f.model_dump() for f in files]
        return sub_dict

def get_submission(submission_id: str) -> dict | None:
    with Session(engine) as session:
        submission = session.get(Submission, submission_id)
        if not submission:
            return None
        sub_dict = submission.model_dump()
        files = session.exec(select(CodeFile).where(CodeFile.submission_id == submission_id)).all()
        sub_dict["files"] = [f.model_dump() for f in files]
        return sub_dict

# Depth check
def create_session(submission_id: str, max_turns: int) -> dict:
    with Session(engine) as session:
        sess = DepthSession(submission_id=submission_id, max_turns=max_turns)
        session.add(sess)
        session.commit()
        session.refresh(sess)
        return sess.model_dump()

def get_session(session_id: str) -> dict | None:
    with Session(engine) as session:
        sess = session.get(DepthSession, session_id)
        if not sess:
            return None
        sess_dict = sess.model_dump()
        turns = session.exec(select(QaTurn).where(QaTurn.session_id == session_id).order_by(QaTurn.turn_number)).all()
        sess_dict["turns"] = [t.model_dump() for t in turns]
        return sess_dict

def add_turn(session_id: str, turn: dict) -> dict:
    with Session(engine) as session:
        qa_turn = QaTurn(session_id=session_id, **turn)
        session.add(qa_turn)
        session.commit()
        session.refresh(qa_turn)
        return qa_turn.model_dump()

def update_turn_with_answer(session_id: str, turn_number: int, answer_text: str, answer_code: str | None, evaluation: dict, meta: dict) -> dict:
    with Session(engine) as session:
        turn = session.exec(select(QaTurn).where(QaTurn.session_id == session_id, QaTurn.turn_number == turn_number)).first()
        if turn:
            turn.answer_text = answer_text
            turn.answer_code = answer_code
            turn.evaluation = evaluation
            turn.meta = meta
            session.add(turn)
            session.commit()
            session.refresh(turn)
            return turn.model_dump()
        return {}

def update_session_state(session_id: str, state_json: dict) -> None:
    with Session(engine) as session:
        sess = session.get(DepthSession, session_id)
        if sess:
            sess.state_json = state_json
            session.add(sess)
            session.commit()

def set_session_status(session_id: str, status: str) -> None:
    with Session(engine) as session:
        sess = session.get(DepthSession, session_id)
        if sess:
            sess.status = status
            session.add(sess)
            session.commit()

def save_profile(session_id: str, candidate_id: str, job_id: str, profile: dict) -> None:
    with Session(engine) as session:
        p = Profile(
            session_id=session_id,
            candidate_id=candidate_id,
            job_id=job_id,
            **profile
        )
        session.add(p)
        session.commit()

def get_profile(session_id: str) -> dict | None:
    with Session(engine) as session:
        p = session.get(Profile, session_id)
        return p.model_dump() if p else None

def list_finished_profiles_for_job(job_id: str) -> list[dict]:
    with Session(engine) as session:
        results = session.exec(
            select(Profile, Candidate)
            .join(Candidate, Profile.candidate_id == Candidate.candidate_id)
            .where(Profile.job_id == job_id)
        ).all()
        
        profiles = []
        for profile, candidate in results:
            p_dict = profile.model_dump()
            p_dict["name"] = candidate.name
            profiles.append(p_dict)
        return profiles

# Cache and config
def cache_get(key: str) -> dict | None:
    with Session(engine) as session:
        c = session.get(LlmCache, key)
        if c:
            c.hits += 1
            session.add(c)
            session.commit()
            return c.response
        return None

def cache_set(key: str, alias: str, response: dict) -> None:
    with Session(engine) as session:
        c = session.get(LlmCache, key)
        if not c:
            c = LlmCache(cache_key=key, alias=alias, response=response)
        else:
            c.alias = alias
            c.response = response
        session.add(c)
        session.commit()

def get_setting(key: str, default: str | None = None) -> str | None:
    with Session(engine) as session:
        s = session.get(Setting, key)
        return s.value if s else default

def set_setting(key: str, value: str) -> None:
    with Session(engine) as session:
        s = session.get(Setting, key)
        if not s:
            s = Setting(key=key, value=value)
        else:
            s.value = value
        session.add(s)
        session.commit()
