from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.fakes import is_fake, fake_db, fake_ai

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

class TaskGenerateRequest(BaseModel):
    job_id: str

@router.post("/generate", status_code=201)
def generate_task(req: TaskGenerateRequest):
    if is_fake():
        job = fake_db.get_job(req.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        task_data = fake_ai.generate_task(job)
        # Note: fake_ai doesn't have generate_task. But fake_crud has create_task
        task = fake_db.create_task({"job_id": req.job_id, **task_data})
    else:
        from db import crud
        from ai import api as ai_api
        job = crud.get_job(req.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        task_data = ai_api.generate_task(job)
        task = crud.create_task({"job_id": req.job_id, **task_data})
    return task

@router.get("/for-job/{job_id}")
def get_task_for_job(job_id: str):
    if is_fake():
        job = fake_db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job_id": job_id, "task_id": "task_1", "title": "Practical Assessment", "brief": "Challenge task", "requirements": ["Requirement 1"], "starter_code": "def solve():\n    pass", "rubric": []}
    else:
        from db import crud
        from sqlmodel import select
        from db.models import Task
        with crud.Session(crud.engine) as session:
            task = session.exec(select(Task).where(Task.job_id == job_id)).first()
            if task:
                return task.model_dump()
                
        job = crud.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        from ai import api as ai_api
        task_data = ai_api.generate_task(job)
        return crud.create_task({"job_id": job_id, **task_data})

@router.get("/{task_id}")
def get_task(task_id: str):
    if is_fake():
        task = fake_db.get_task(task_id)
    else:
        from db import crud
        task = crud.get_task(task_id)
        
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
