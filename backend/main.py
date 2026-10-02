import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routes import health, jobs, candidates, tasks, submissions, depth, shortlist

app = FastAPI(title="ProofHire API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    if os.getenv("USE_FAKES", "false").lower() != "true":
        try:
            from db import seed
            seed.reset_and_seed()
        except ImportError:
            pass

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = "not_found" if exc.status_code == 404 else ("bad_request" if exc.status_code == 400 else "error")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc)}}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal", "message": str(exc)}}
    )

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(tasks.router)
app.include_router(submissions.router)
app.include_router(depth.router)
app.include_router(shortlist.router)
