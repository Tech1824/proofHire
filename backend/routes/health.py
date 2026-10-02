from fastapi import APIRouter
from backend.schemas import HealthResponse
from backend.fakes import is_fake, fake_db, fake_ai
from pydantic import BaseModel

class DemoModeRequest(BaseModel):
    enabled: bool

router = APIRouter(prefix="/api")

@router.get("/health", response_model=HealthResponse)
def get_health():
    if is_fake():
        demo_mode_str = fake_db.get_setting("demo_mode", "false")
        llm_status = fake_ai.llm_health()
    else:
        from db import crud
        from ai import api as ai_api
        demo_mode_str = crud.get_setting("demo_mode", "false")
        llm_status = ai_api.llm_health()
    
    demo_mode = (demo_mode_str.lower() == "true") if demo_mode_str else False
    
    return {
        "status": "ok",
        "version": "0.1.0",
        "demo_mode": demo_mode,
        "llm": llm_status
    }

@router.post("/config/demo-mode")
def set_demo_mode(req: DemoModeRequest):
    val = "true" if req.enabled else "false"
    if is_fake():
        fake_db.set_setting("demo_mode", val)
    else:
        from db import crud
        crud.set_setting("demo_mode", val)
    return {"demo_mode": req.enabled}
