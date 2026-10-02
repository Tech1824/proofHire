from fastapi import APIRouter, HTTPException
from backend.schemas import JobCreate, JobResponse, JobListResponse
from backend.fakes import is_fake, fake_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse, status_code=201)
@router.post("/", response_model=JobResponse, status_code=201, include_in_schema=False)
def create_job(job: JobCreate):
    if is_fake():
        result = fake_db.create_job(job.model_dump())
    else:
        from db import crud
        result = crud.create_job(job.model_dump())
    return result

@router.get("", response_model=JobListResponse)
@router.get("/", response_model=JobListResponse, include_in_schema=False)
def list_jobs():
    if is_fake():
        jobs = fake_db.list_jobs()
    else:
        from db import crud
        jobs = crud.list_jobs()
    return {"jobs": jobs}

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    if is_fake():
        job = fake_db.get_job(job_id)
    else:
        from db import crud
        job = crud.get_job(job_id)
        
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} does not exist")
    return job
