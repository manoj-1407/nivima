import enum
import uuid

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

from src.config import get_settings

settings = get_settings()

# Dialect-agnostic types for SQLite & PostgreSQL compatibility
CompatArray = JSON().with_variant(ARRAY(String(10)), "postgresql")
CompatJson = JSON().with_variant(JSONB, "postgresql")

_is_sqlite = settings.database_url.startswith("sqlite")
_engine_kwargs = {"pool_pre_ping": True} if not _is_sqlite else {"connect_args": {"check_same_thread": False}}
if not _is_sqlite:
    _engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_engine(
    settings.database_url,
    **_engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JobStatus(str, enum.Enum):
    queued = "queued"
    extracting = "extracting"
    transcribing = "transcribing"
    translating = "translating"
    synthesizing = "synthesizing"
    aligning = "aligning"
    reanimating = "reanimating"
    assembling = "assembling"
    qc_review = "qc_review"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ChunkStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class ReviewerDecision(str, enum.Enum):
    approve = "approve"
    reject = "reject"
    reprocess = "reprocess"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tier = Column(String(50), default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    minutes_processed_this_month = Column(Integer, default=0)
    monthly_limit_minutes = Column(Integer, default=10)

    jobs = relationship("Job", back_populates="user")
    voice_clones = relationship("VoiceClone", back_populates="user")


class VoiceClone(Base):
    __tablename__ = "voice_clones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    display_name = Column(String(255), nullable=False)
    reference_audio_path = Column(String(500), nullable=False)
    supported_languages = Column(CompatArray)
    consent_recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="voice_clones")
    jobs = relationship("Job", back_populates="voice_clone")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(SAEnum(JobStatus), default=JobStatus.queued)
    source_language = Column(String(10), nullable=False)
    target_languages = Column(CompatArray, nullable=False)
    voice_clone_id = Column(UUID(as_uuid=True), ForeignKey("voice_clones.id"), nullable=True)
    processing_tier = Column(String(20), default="speed")

    source_file_path = Column(String(500), nullable=False)
    source_duration_seconds = Column(Integer, nullable=True)
    source_resolution = Column(String(20), nullable=True)
    source_fps = Column(String(10), nullable=True)

    output_paths = Column(CompatJson, default={})

    current_stage = Column(String(50), nullable=True)
    progress_pct = Column(Integer, default=0)
    chunks_total = Column(Integer, nullable=True)
    chunks_completed = Column(Integer, default=0)

    compute_cost_credits = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    user = relationship("User", back_populates="jobs")
    voice_clone = relationship("VoiceClone", back_populates="jobs")
    chunks = relationship("Chunk", back_populates="job")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)

    start_ms = Column(Integer, nullable=False)
    end_ms = Column(Integer, nullable=False)

    source_text = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=True)
    word_timestamps = Column(JSONB, nullable=True)

    translations = Column(JSONB, default={})

    source_audio_path = Column(String(500), nullable=True)
    speech_audio_path = Column(String(500), nullable=True)
    background_audio_path = Column(String(500), nullable=True)
    dubbed_audio_paths = Column(JSONB, default={})

    scene_classification = Column(JSONB, nullable=True)
    qc_scores = Column(JSONB, nullable=True)
    reanimation_applied = Column(Boolean, default=False)

    status = Column(SAEnum(ChunkStatus), default=ChunkStatus.pending)
    error_message = Column(Text, nullable=True)

    job = relationship("Job", back_populates="chunks")


class QCQueue(Base):
    __tablename__ = "qc_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"))
    target_language = Column(String(10), nullable=False)

    flag_reason = Column(String(255), nullable=False)
    flag_details = Column(JSONB, nullable=True)

    original_frame_path = Column(String(500), nullable=True)
    reanimated_frame_path = Column(String(500), nullable=True)

    flagged_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewer_decision = Column(SAEnum(ReviewerDecision), nullable=True)
    reviewer_notes = Column(Text, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
