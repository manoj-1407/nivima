import os
import shutil
import uuid

import bcrypt as _bcrypt
import structlog
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.middleware.auth import create_access_token
from src.api.routes.corrections import router as corrections_router
from src.api.routes.jobs import router as jobs_router
from src.api.routes.qc import router as qc_router
from src.api.routes.voices import router as voices_router
from src.config import get_settings
from src.storage.db import User, get_db

settings = get_settings()
log = structlog.get_logger()


def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


app = FastAPI(
    title="Nivima API",
    description="Nivima — Neural Indian Video Interface & Multilingual Animation Platform",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(jobs_router)
app.include_router(voices_router)
app.include_router(qc_router)
app.include_router(corrections_router)


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/v1/auth/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        id=uuid.uuid4(),
        email=req.email,
        password_hash=_hash_password(req.password),
        tier="free",
        monthly_limit_minutes=10,
        minutes_processed_this_month=0
    )
    db.add(user)
    db.commit()
    token = create_access_token(str(user.id))
    log.info("user_registered", user_id=str(user.id))
    return {"token": token, "user_id": str(user.id), "tier": "free"}


@app.post("/api/v1/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not _verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user.id))
    return {"token": token, "user_id": str(user.id), "tier": user.tier}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0", "service": "Nivima API"}


@app.get("/api/v1/system/info")
def system_info():
    """Returns GPU, CUDA, and system capabilities for frontend HUD."""
    cuda_available = False
    gpu_name = "CPU Only"
    vram_total_gb = 0.0
    cuda_version = None

    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            vram_total_gb = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
            cuda_version = torch.version.cuda
    except Exception:
        pass

    ffmpeg_available = shutil.which("ffmpeg") is not None

    return {
        "status": "online",
        "service": "Nivima Neural Engine",
        "version": "0.1.0",
        "environment": settings.environment,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "vram_total_gb": vram_total_gb,
        "cuda_version": cuda_version,
        "ffmpeg_available": ffmpeg_available,
        "supported_languages": ["hi", "te", "ta", "kn", "ml", "bn", "mr", "gu", "pa", "or"],
        "max_video_duration_minutes": 10
    }


# Mount frontend production build if available
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(frontend_dist) and os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Nivima API", "docs": "/docs", "frontend_status": "Run `npm run build` in frontend/ to serve UI"}
