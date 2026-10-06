from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
import structlog

from src.api.routes.jobs import router as jobs_router
from src.api.routes.voices import router as voices_router
from src.api.routes.qc import router as qc_router
from src.api.middleware.auth import create_access_token
from src.storage.db import get_db, User
from src.config import get_settings

settings = get_settings()
log = structlog.get_logger()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(
    title="VoxBridge API",
    description="Multilingual video dubbing for Indian content creators",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(jobs_router)
app.include_router(voices_router)
app.include_router(qc_router)


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
        password_hash=pwd.hash(req.password),
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
    if not user or not pwd.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user.id))
    return {"token": token, "user_id": str(user.id), "tier": user.tier}


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
def root():
    return {"message": "VoxBridge API", "docs": "/docs"}


# Late import to avoid circular — corrections router added after main routes
from src.api.routes.corrections import router as corrections_router
app.include_router(corrections_router)
