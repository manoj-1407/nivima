"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgvector"')

    op.execute("""
        CREATE TYPE job_status AS ENUM (
            'queued','extracting','transcribing','translating',
            'synthesizing','aligning','reanimating','assembling',
            'qc_review','completed','failed','cancelled'
        )
    """)
    op.execute("""
        CREATE TYPE chunk_status AS ENUM (
            'pending','processing','completed','failed','skipped'
        )
    """)
    op.execute("""
        CREATE TYPE reviewer_decision AS ENUM ('approve','reject','reprocess')
    """)

    op.create_table("users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("tier", sa.String(50), server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("minutes_processed_this_month", sa.Integer, server_default="0"),
        sa.Column("monthly_limit_minutes", sa.Integer, server_default="10"),
    )

    op.create_table("voice_clones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("reference_audio_path", sa.String(500), nullable=False),
        sa.Column("supported_languages", ARRAY(sa.String(10))),
        sa.Column("consent_recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean, server_default="true"),
    )

    op.create_table("jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("status", sa.Text, server_default="queued"),
        sa.Column("source_language", sa.String(10), nullable=False),
        sa.Column("target_languages", ARRAY(sa.String(10)), nullable=False),
        sa.Column("voice_clone_id", UUID(as_uuid=True),
                  sa.ForeignKey("voice_clones.id"), nullable=True),
        sa.Column("processing_tier", sa.String(20), server_default="speed"),
        sa.Column("source_file_path", sa.String(500), nullable=False),
        sa.Column("source_duration_seconds", sa.Integer, nullable=True),
        sa.Column("source_resolution", sa.String(20), nullable=True),
        sa.Column("source_fps", sa.String(10), nullable=True),
        sa.Column("output_paths", JSONB, server_default="{}"),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("progress_pct", sa.Integer, server_default="0"),
        sa.Column("chunks_total", sa.Integer, nullable=True),
        sa.Column("chunks_completed", sa.Integer, server_default="0"),
        sa.Column("compute_cost_credits", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
    )

    op.create_table("chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("job_id", UUID(as_uuid=True),
                  sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("start_ms", sa.Integer, nullable=False),
        sa.Column("end_ms", sa.Integer, nullable=False),
        sa.Column("source_text", sa.Text, nullable=True),
        sa.Column("source_language", sa.String(10), nullable=True),
        sa.Column("word_timestamps", JSONB, nullable=True),
        sa.Column("translations", JSONB, server_default="{}"),
        sa.Column("source_audio_path", sa.String(500), nullable=True),
        sa.Column("speech_audio_path", sa.String(500), nullable=True),
        sa.Column("background_audio_path", sa.String(500), nullable=True),
        sa.Column("dubbed_audio_paths", JSONB, server_default="{}"),
        sa.Column("scene_classification", JSONB, nullable=True),
        sa.Column("qc_scores", JSONB, nullable=True),
        sa.Column("reanimation_applied", sa.Boolean, server_default="false"),
        sa.Column("status", sa.Text, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    op.create_table("qc_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("jobs.id")),
        sa.Column("chunk_id", UUID(as_uuid=True), sa.ForeignKey("chunks.id")),
        sa.Column("target_language", sa.String(10), nullable=False),
        sa.Column("flag_reason", sa.String(255), nullable=False),
        sa.Column("flag_details", JSONB, nullable=True),
        sa.Column("original_frame_path", sa.String(500), nullable=True),
        sa.Column("reanimated_frame_path", sa.String(500), nullable=True),
        sa.Column("flagged_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewer_decision", sa.Text, nullable=True),
        sa.Column("reviewer_notes", sa.Text, nullable=True),
    )

    op.create_index("idx_jobs_user_id", "jobs", ["user_id"])
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_created_at", "jobs", ["created_at"])
    op.create_index("idx_chunks_job_id", "chunks", ["job_id"])
    op.create_index("idx_chunks_status", "chunks", ["status"])
    op.create_index("idx_qc_job_id", "qc_queue", ["job_id"])


def downgrade():
    op.drop_table("qc_queue")
    op.drop_table("chunks")
    op.drop_table("jobs")
    op.drop_table("voice_clones")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS reviewer_decision")
    op.execute("DROP TYPE IF EXISTS chunk_status")
    op.execute("DROP TYPE IF EXISTS job_status")
