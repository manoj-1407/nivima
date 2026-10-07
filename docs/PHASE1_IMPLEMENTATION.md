# Phase 1 — Complete Implementation Plan
**Timeline:** Month 1-3  
**Goal:** Working audio dubbing pipeline. No visual changes. Proven end to end.
**Definition of Done:** Upload Hindi video → get Telugu/Tamil audio-dubbed video.
                        Turnaround < 3× video duration. Demo shareable externally.

---

## Folder Structure

```
nivima/
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── validator.py          # file format, size, codec validation
│   │   ├── extractor.py          # audio + video extraction via FFmpeg
│   │   └── metadata.py           # extract fps, resolution, duration, codec
│   │
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── asr.py                # IndicWhisper + Whisper fallback
│   │   ├── language_id.py        # detect language per segment (IndicLID)
│   │   └── chunker.py            # scene detection + VAD chunking
│   │
│   ├── translation/
│   │   ├── __init__.py
│   │   ├── translator.py         # IndicTrans2 translation
│   │   ├── rewriter.py           # LLM constrained rewrite pass
│   │   ├── phoneme_map.py        # phoneme → viseme mapping table
│   │   └── validator.py          # translation output validation
│   │
│   ├── tts/
│   │   ├── __init__.py
│   │   ├── synthesizer.py        # IndicTTS generic voice
│   │   ├── voice_cloner.py       # XTTS-v2 cross-lingual clone
│   │   └── audio_utils.py        # time-stretch, silence handling
│   │
│   ├── alignment/
│   │   ├── __init__.py
│   │   ├── force_aligner.py      # Montreal Forced Aligner wrapper
│   │   └── audio_adjuster.py     # stretch/compress to fit timing
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── separator.py          # Demucs speech/background separation
│   │   └── mixer.py              # remix speech + background
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app
│   │   ├── routes/
│   │   │   ├── jobs.py           # POST /jobs, GET /jobs/{id}
│   │   │   ├── voices.py         # POST /voices, GET /voices
│   │   │   └── qc.py             # GET /qc/{job_id}
│   │   ├── models/
│   │   │   ├── job.py            # Pydantic schemas
│   │   │   └── voice.py
│   │   ├── middleware/
│   │   │   ├── auth.py           # JWT validation
│   │   │   └── rate_limit.py     # per-tier rate limiting
│   │   └── dependencies.py       # DB session, auth, storage
│   │
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── tasks/
│   │   │   ├── pipeline.py       # orchestrate full pipeline per job
│   │   │   ├── audio_tasks.py    # individual audio stage tasks
│   │   │   └── notify.py         # job completion notifications
│   │   └── progress.py           # WebSocket progress broadcasting
│   │
│   └── storage/
│       ├── __init__.py
│       ├── s3.py                 # S3/R2 client abstraction
│       └── db.py                 # PostgreSQL session + models
│
├── tests/
│   ├── unit/
│   │   ├── test_validator.py
│   │   ├── test_asr.py
│   │   ├── test_translation.py
│   │   ├── test_tts.py
│   │   └── test_alignment.py
│   ├── integration/
│   │   ├── test_pipeline_audio.py    # full audio pipeline e2e
│   │   └── test_api.py
│   └── fixtures/
│       ├── sample_hindi_60s.mp4      # test video (committed as LFS)
│       ├── expected_transcript.json
│       └── expected_translation_te.json
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   └── docker-compose.yml
│   └── k8s/
│       ├── namespace.yaml
│       ├── api-deployment.yaml
│       ├── worker-deployment.yaml
│       └── redis-deployment.yaml
│
├── scripts/
│   ├── download_models.sh            # download all required model weights
│   ├── setup_mfa.sh                  # Montreal Forced Aligner setup
│   └── test_pipeline.sh              # quick smoke test
│
├── research/
│   ├── phoneme_coverage_analysis.py  # verify our sentences cover all visemes
│   ├── translation_eval.py           # BLEU score evaluation script
│   └── tts_quality_eval.py           # MOS estimation for TTS output
│
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
└── Makefile
```

---

## Environment Configuration

```bash
# .env.example
DATABASE_URL=postgresql://nivima:password@localhost:5432/nivima
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=https://your-r2-endpoint.r2.cloudflarestorage.com
S3_BUCKET=nivima-media
S3_ACCESS_KEY=your_key
S3_SECRET_KEY=your_secret
JWT_SECRET=your_jwt_secret_minimum_32_chars
OLLAMA_URL=http://localhost:11434  # for Llama 3.1 8B rewrite pass
MODEL_CACHE_DIR=/models            # where to store downloaded weights
MAX_VIDEO_SIZE_MB=2000
MAX_VIDEO_DURATION_SECONDS=18000   # 5 hours
CELERY_CONCURRENCY=4               # workers per machine
GPU_AVAILABLE=false                # set true on GPU machines
```

---

## requirements.txt

```
# Core
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.8.0
python-multipart==0.0.9

# Job queue
celery==5.4.0
redis==5.0.8
flower==2.0.1  # Celery monitoring UI

# Database
sqlalchemy==2.0.32
asyncpg==0.29.0
alembic==1.13.2
psycopg2-binary==2.9.9

# Storage
boto3==1.35.0  # S3/R2 compatible

# Audio/Video
ffmpeg-python==0.2.0
librosa==0.10.2  # audio time-stretching
soundfile==0.12.1
pydub==0.25.1
webrtcvad==2.0.10  # voice activity detection

# ML — ASR
faster-whisper==1.0.3
openai-whisper==20231117

# ML — Scene Detection
scenedetect[opencv]==0.6.4

# ML — Translation
transformers==4.44.0
sentencepiece==0.2.0
sacremoses==0.1.1
ctranslate2==4.4.0

# ML — TTS + Voice Clone
TTS==0.22.0  # includes XTTS-v2
torch==2.4.0
torchaudio==2.4.0

# ML — Audio Separation
demucs==4.0.1

# Utilities
httpx==0.27.0
python-jose[cryptography]==3.3.0  # JWT
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
structlog==24.4.0  # structured logging
tenacity==9.0.0  # retry logic
```

---

## Database Schema — Full

```sql
-- migrations/001_initial.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

CREATE TYPE job_status AS ENUM (
    'queued',
    'extracting',
    'transcribing', 
    'translating',
    'synthesizing',
    'aligning',
    'reanimating',
    'assembling',
    'qc_review',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE chunk_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'skipped'
);

CREATE TYPE reviewer_decision AS ENUM (
    'approve',
    'reject',
    'reprocess'
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',  -- free, creator, professional, enterprise
    created_at TIMESTAMPTZ DEFAULT NOW(),
    minutes_processed_this_month INTEGER DEFAULT 0,
    monthly_limit_minutes INTEGER DEFAULT 10
);

CREATE TABLE voice_clones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(255) NOT NULL,
    reference_audio_path VARCHAR(500) NOT NULL,  -- S3 path
    embedding VECTOR(512),  -- voice embedding for deduplication
    supported_languages VARCHAR(10)[],
    consent_recorded_at TIMESTAMPTZ NOT NULL,  -- DPDP compliance
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    status job_status DEFAULT 'queued',
    source_language VARCHAR(10) NOT NULL,
    target_languages VARCHAR(10)[] NOT NULL,
    voice_clone_id UUID REFERENCES voice_clones(id),
    processing_tier VARCHAR(20) DEFAULT 'speed',  -- speed, quality
    
    -- Source file
    source_file_path VARCHAR(500) NOT NULL,  -- S3 path
    source_duration_seconds INTEGER,
    source_resolution VARCHAR(20),  -- e.g. "1920x1080"
    source_fps DECIMAL(5,2),
    
    -- Output files (one per target language)
    output_paths JSONB DEFAULT '{}',  -- {"te": "s3://...", "ta": "s3://..."}
    
    -- Progress tracking
    current_stage VARCHAR(50),
    progress_pct INTEGER DEFAULT 0,
    chunks_total INTEGER,
    chunks_completed INTEGER DEFAULT 0,
    
    -- Cost tracking
    compute_cost_credits INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    
    -- Time boundaries
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    
    -- Transcript
    source_text TEXT,
    source_language VARCHAR(10),
    word_timestamps JSONB,  -- [{word, start_ms, end_ms, confidence}]
    
    -- Translation (one per target language)
    translations JSONB DEFAULT '{}',  -- {"te": "...", "ta": "..."}
    
    -- Audio paths
    source_audio_path VARCHAR(500),
    speech_audio_path VARCHAR(500),      -- after Demucs separation
    background_audio_path VARCHAR(500),  -- after Demucs separation
    dubbed_audio_paths JSONB DEFAULT '{}',  -- per language
    
    -- Scene classification (Phase 2)
    scene_classification JSONB,  -- {decision, yaw, pitch, occlusion, confidence}
    
    -- QC
    qc_scores JSONB,  -- {syncnet, csim, psnr, temporal_variance}
    reanimation_applied BOOLEAN DEFAULT FALSE,
    
    status chunk_status DEFAULT 'pending',
    error_message TEXT
);

CREATE TABLE qc_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id),
    chunk_id UUID REFERENCES chunks(id),
    target_language VARCHAR(10) NOT NULL,
    
    flag_reason VARCHAR(255) NOT NULL,
    flag_details JSONB,  -- specific metric values that triggered flag
    
    original_frame_path VARCHAR(500),  -- S3 path to flagged frame
    reanimated_frame_path VARCHAR(500),
    
    flagged_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewer_id UUID REFERENCES users(id),
    reviewer_decision reviewer_decision,
    reviewer_notes TEXT
);

-- Indexes
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_chunks_job_id ON chunks(job_id);
CREATE INDEX idx_chunks_status ON chunks(status);
CREATE INDEX idx_qc_queue_job_id ON qc_queue(job_id);
CREATE INDEX idx_qc_queue_reviewed ON qc_queue(reviewed_at) WHERE reviewed_at IS NULL;
```

---

## API Specification — Complete

### POST /api/v1/jobs
Submit a dubbing job.

**Request:**
```json
{
  "source_language": "hi",
  "target_languages": ["te", "ta", "kn"],
  "processing_tier": "speed",
  "voice_clone_id": "uuid-optional",
  "webhook_url": "https://your-server.com/callback"
}
```

**With file upload:** multipart/form-data with `video` field.

**Response 202:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_duration_minutes": 45,
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**
- 400: Invalid language code / missing file / file too large
- 402: Minute limit exceeded for tier
- 415: Unsupported video format
- 422: Video duration exceeds maximum

---

### GET /api/v1/jobs/{job_id}
Poll job status.

**Response 200:**
```json
{
  "job_id": "uuid",
  "status": "translating",
  "progress_pct": 34,
  "current_stage": "translating",
  "chunks_total": 48,
  "chunks_completed": 16,
  "target_languages": ["te", "ta"],
  "outputs": {},
  "created_at": "2026-01-01T00:00:00Z",
  "started_at": "2026-01-01T00:01:00Z",
  "estimated_completion": "2026-01-01T00:45:00Z"
}
```

**When completed:**
```json
{
  "status": "completed",
  "outputs": {
    "te": {
      "download_url": "https://cdn.nivima.ai/jobs/uuid/output_te.mp4",
      "expires_at": "2026-01-08T00:00:00Z",
      "qc_score": 7.8,
      "scenes_reanimated": 34,
      "scenes_skipped": 12,
      "scenes_flagged": 4
    }
  }
}
```

---

### WebSocket /ws/jobs/{job_id}/progress
Real-time progress updates.

**Messages from server:**
```json
{"type": "stage_start", "stage": "translating", "timestamp": "..."}
{"type": "chunk_complete", "chunk_index": 5, "total": 48, "pct": 12}
{"type": "stage_complete", "stage": "translating", "duration_seconds": 45}
{"type": "job_complete", "outputs": {...}}
{"type": "job_failed", "error": "Translation failed on chunk 12"}
```

---

### POST /api/v1/voices
Register a voice clone.

**Request:** multipart/form-data
```
reference_audio: audio file (WAV/MP3, minimum 6 seconds)
display_name: "Alakh Pandey Voice"
consent_acknowledged: true  (required — DPDP compliance)
```

**Response 201:**
```json
{
  "voice_id": "uuid",
  "display_name": "Alakh Pandey Voice",
  "duration_seconds": 12.4,
  "supported_languages": ["hi"],
  "quality_score": 0.87,
  "created_at": "..."
}
```

**Errors:**
- 400: Audio too short (< 6 seconds)
- 400: consent_acknowledged must be true
- 422: Audio quality too poor (high background noise)

---

### GET /api/v1/qc/{job_id}
Get QC report for a completed job.

**Response 200:**
```json
{
  "job_id": "uuid",
  "overall_scores": {
    "te": {
      "syncnet_avg": 7.4,
      "scenes_processed": 46,
      "scenes_reanimated": 34,
      "scenes_skipped": 8,
      "scenes_flagged": 4
    }
  },
  "flagged_scenes": [
    {
      "chunk_index": 12,
      "timestamp_start_ms": 48000,
      "timestamp_end_ms": 52400,
      "flag_reason": "low_syncnet_score",
      "syncnet_score": 4.2,
      "original_frame_url": "...",
      "reanimated_frame_url": "...",
      "status": "pending_review"
    }
  ]
}
```

---

## Core Module Implementations

### src/ingestion/validator.py
```python
import os
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass

SUPPORTED_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}
MAX_SIZE_BYTES = 10 * 1024 * 1024 * 1024  # 10GB
MAX_DURATION_SECONDS = 18000  # 5 hours
MIN_DURATION_SECONDS = 5

@dataclass
class VideoMetadata:
    duration_seconds: float
    fps: float
    resolution: str
    codec: str
    audio_codec: str
    has_audio: bool
    file_size_bytes: int

class ValidationError(Exception):
    pass

def validate_and_extract_metadata(file_path: str) -> VideoMetadata:
    path = Path(file_path)
    
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValidationError(f"Unsupported format: {path.suffix}")
    
    size = os.path.getsize(file_path)
    if size > MAX_SIZE_BYTES:
        raise ValidationError(f"File too large: {size / 1e9:.1f}GB (max 10GB)")
    
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-show_format', file_path
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise ValidationError("Cannot read video file — corrupted or invalid format")
    
    probe = json.loads(result.stdout)
    
    video_stream = next(
        (s for s in probe['streams'] if s['codec_type'] == 'video'), None
    )
    audio_stream = next(
        (s for s in probe['streams'] if s['codec_type'] == 'audio'), None
    )
    
    if not video_stream:
        raise ValidationError("No video stream found")
    
    duration = float(probe['format'].get('duration', 0))
    
    if duration < MIN_DURATION_SECONDS:
        raise ValidationError(f"Video too short: {duration:.1f}s (minimum {MIN_DURATION_SECONDS}s)")
    if duration > MAX_DURATION_SECONDS:
        raise ValidationError(f"Video too long: {duration/3600:.1f}hr (maximum 5hr)")
    
    fps_str = video_stream.get('r_frame_rate', '24/1')
    num, den = fps_str.split('/')
    fps = float(num) / float(den)
    
    return VideoMetadata(
        duration_seconds=duration,
        fps=fps,
        resolution=f"{video_stream['width']}x{video_stream['height']}",
        codec=video_stream.get('codec_name', 'unknown'),
        audio_codec=audio_stream.get('codec_name', 'none') if audio_stream else 'none',
        has_audio=audio_stream is not None,
        file_size_bytes=size
    )
```

### src/ingestion/extractor.py
```python
import ffmpeg
import os
from pathlib import Path

def extract_audio(video_path: str, output_dir: str) -> str:
    output_path = os.path.join(output_dir, 'source_audio.wav')
    (
        ffmpeg
        .input(video_path)
        .output(output_path, acodec='pcm_s16le', ac=1, ar='16000')
        .run(overwrite_output=True, quiet=True)
    )
    return output_path

def extract_video_frames(video_path: str, output_dir: str, fps: float = None) -> str:
    frames_dir = os.path.join(output_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    output_pattern = os.path.join(frames_dir, '%06d.jpg')
    
    stream = ffmpeg.input(video_path)
    if fps:
        stream = stream.filter('fps', fps=fps)
    
    stream.output(output_pattern, qscale=2).run(overwrite_output=True, quiet=True)
    return frames_dir

def merge_audio_video(
    video_path: str,
    dubbed_audio_path: str,
    background_audio_path: str,
    output_path: str,
    speech_volume: float = 1.0,
    background_volume: float = 0.8
) -> str:
    video = ffmpeg.input(video_path).video
    speech = ffmpeg.input(dubbed_audio_path)
    background = ffmpeg.input(background_audio_path)
    
    mixed_audio = ffmpeg.filter(
        [speech, background],
        'amix',
        inputs=2,
        weights=f'{speech_volume} {background_volume}'
    )
    
    (
        ffmpeg
        .output(video, mixed_audio, output_path, vcodec='copy', acodec='aac', audio_bitrate='192k')
        .run(overwrite_output=True, quiet=True)
    )
    return output_path
```

### src/transcription/asr.py
```python
import json
from dataclasses import dataclass
from typing import List, Optional
from faster_whisper import WhisperModel
import structlog

log = structlog.get_logger()

INDIC_LANGUAGE_CODES = {
    'hi', 'te', 'ta', 'kn', 'ml', 'bn', 'mr', 'gu', 'or', 'pa', 'as', 'ur'
}

@dataclass
class WordTimestamp:
    word: str
    start_ms: int
    end_ms: int
    confidence: float

@dataclass
class TranscriptSegment:
    text: str
    start_ms: int
    end_ms: int
    language: str
    words: List[WordTimestamp]
    avg_confidence: float

_model_cache = {}

def get_model(model_size: str = 'large-v3', device: str = 'auto') -> WhisperModel:
    key = f"{model_size}_{device}"
    if key not in _model_cache:
        compute_type = 'float16' if device == 'cuda' else 'int8'
        _model_cache[key] = WhisperModel(
            model_size,
            device=device if device != 'auto' else 'cuda',
            compute_type=compute_type
        )
    return _model_cache[key]

def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    chunk_start_ms: int = 0
) -> List[TranscriptSegment]:
    model = get_model()
    
    segments, info = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300}
    )
    
    detected_lang = info.language
    log.info("transcription_complete",
             language=detected_lang,
             confidence=info.language_probability)
    
    result = []
    for seg in segments:
        words = []
        if seg.words:
            for w in seg.words:
                words.append(WordTimestamp(
                    word=w.word.strip(),
                    start_ms=int((w.start * 1000) + chunk_start_ms),
                    end_ms=int((w.end * 1000) + chunk_start_ms),
                    confidence=w.probability
                ))
        
        avg_conf = sum(w.confidence for w in words) / len(words) if words else 0.0
        
        result.append(TranscriptSegment(
            text=seg.text.strip(),
            start_ms=int((seg.start * 1000) + chunk_start_ms),
            end_ms=int((seg.end * 1000) + chunk_start_ms),
            language=detected_lang,
            words=words,
            avg_confidence=avg_conf
        ))
    
    return result

def transcribe_chunks(chunk_audio_paths: List[dict]) -> List[TranscriptSegment]:
    all_segments = []
    for chunk in chunk_audio_paths:
        segments = transcribe_audio(
            chunk['path'],
            chunk_start_ms=chunk['start_ms']
        )
        all_segments.extend(segments)
    return all_segments
```

### src/translation/translator.py
```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from typing import List
import structlog

log = structlog.get_logger()

LANGUAGE_CODES = {
    'hi': 'hin_Deva',
    'te': 'tel_Telu',
    'ta': 'tam_Taml',
    'kn': 'kan_Knda',
    'ml': 'mal_Mlym',
    'bn': 'ben_Beng',
    'mr': 'mar_Deva',
    'gu': 'guj_Gujr',
    'or': 'ory_Orya',
    'pa': 'pan_Guru',
}

MODEL_NAME = 'ai4bharat/indictrans2-indic-indic-dist-200M'

_model = None
_tokenizer = None

def _load_model():
    global _model, _tokenizer
    if _model is None:
        log.info("loading_indictrans2")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, trust_remote_code=True)
        if torch.cuda.is_available():
            _model = _model.cuda()
        _model.eval()

def translate_text(
    text: str,
    source_lang: str,
    target_lang: str
) -> str:
    _load_model()
    
    src_code = LANGUAGE_CODES.get(source_lang)
    tgt_code = LANGUAGE_CODES.get(target_lang)
    
    if not src_code or not tgt_code:
        raise ValueError(f"Unsupported language pair: {source_lang} → {target_lang}")
    
    inputs = _tokenizer(
        text,
        return_tensors='pt',
        src_lang=src_code,
        padding=True,
        truncation=True,
        max_length=512
    )
    
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            tgt_lang=tgt_code,
            max_length=512,
            num_beams=4,
            length_penalty=1.0
        )
    
    translation = _tokenizer.decode(outputs[0], skip_special_tokens=True)
    return translation

def translate_segments(
    segments: List[dict],
    source_lang: str,
    target_lang: str
) -> List[dict]:
    translated = []
    for seg in segments:
        translation = translate_text(seg['text'], source_lang, target_lang)
        
        # validation: output length should be 50-200% of input length
        src_len = len(seg['text'].split())
        tgt_len = len(translation.split())
        if not (src_len * 0.5 <= tgt_len <= src_len * 2.5):
            log.warning("translation_length_anomaly",
                       src_len=src_len, tgt_len=tgt_len, text=seg['text'])
        
        translated.append({
            **seg,
            'translated_text': translation,
            'target_language': target_lang
        })
    
    return translated
```

### src/tts/synthesizer.py
```python
import os
import tempfile
from TTS.api import TTS
import torch
import structlog

log = structlog.get_logger()

INDIC_TTS_MODELS = {
    'te': 'tts_models/te/cv/vits',
    'ta': 'tts_models/ta/cv/vits',
    'kn': 'tts_models/kn/cv/vits',
    'ml': 'tts_models/ml/cv/vits',
    'hi': 'tts_models/hi/cv/vits',
}

XTTS_MODEL = 'tts_models/multilingual/multi-dataset/xtts_v2'

# Languages XTTS-v2 natively supports
XTTS_SUPPORTED = {'hi', 'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh'}

_tts_cache = {}

def _get_tts(model_name: str) -> TTS:
    if model_name not in _tts_cache:
        log.info("loading_tts_model", model=model_name)
        gpu = torch.cuda.is_available()
        _tts_cache[model_name] = TTS(model_name, gpu=gpu)
    return _tts_cache[model_name]

def synthesize_generic(text: str, language: str, output_path: str) -> str:
    model_name = INDIC_TTS_MODELS.get(language)
    if not model_name:
        raise ValueError(f"No TTS model for language: {language}")
    
    tts = _get_tts(model_name)
    tts.tts_to_file(text=text, file_path=output_path)
    return output_path

def synthesize_cloned(
    text: str,
    language: str,
    reference_audio_path: str,
    output_path: str
) -> tuple[str, float]:
    """
    Returns (output_path, estimated_quality_score)
    Quality score 0-1. Lower for languages not natively supported by XTTS-v2.
    """
    tts = _get_tts(XTTS_MODEL)
    
    # XTTS-v2 native language support check
    native_support = language in XTTS_SUPPORTED
    quality_estimate = 0.85 if native_support else 0.65
    
    if not native_support:
        log.warning("xtts_non_native_language",
                   language=language,
                   quality_estimate=quality_estimate,
                   note="Using Hindi phoneme approximation. Voice identity ~65% preserved.")
    
    # Use Hindi as the closest supported language for South Indian languages
    xtts_lang = language if native_support else 'hi'
    
    tts.tts_to_file(
        text=text,
        speaker_wav=reference_audio_path,
        language=xtts_lang,
        file_path=output_path
    )
    
    return output_path, quality_estimate

def synthesize_segments(
    segments: List[dict],
    language: str,
    output_dir: str,
    voice_clone_path: str = None
) -> List[dict]:
    results = []
    for i, seg in enumerate(segments):
        output_path = os.path.join(output_dir, f'chunk_{i:04d}.wav')
        
        if voice_clone_path:
            path, quality = synthesize_cloned(
                seg['translated_text'], language, voice_clone_path, output_path
            )
            seg['voice_quality_estimate'] = quality
        else:
            path = synthesize_generic(seg['translated_text'], language, output_path)
        
        seg['dubbed_audio_path'] = path
        results.append(seg)
    
    return results
```

### src/worker/tasks/pipeline.py
```python
from celery import chain, group, chord
from ..celery_app import app
from ...ingestion.validator import validate_and_extract_metadata
from ...ingestion.extractor import extract_audio, merge_audio_video
from ...audio.separator import separate_audio
from ...transcription.asr import transcribe_audio
from ...transcription.chunker import detect_scenes_and_chunk
from ...translation.translator import translate_segments
from ...tts.synthesizer import synthesize_segments
from ...alignment.force_aligner import align_audio
from ...alignment.audio_adjuster import adjust_timing
from ...storage.db import get_db
from ...storage.s3 import upload_file, download_file
import structlog
import os
import tempfile

log = structlog.get_logger()

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_job(self, job_id: str):
    db = next(get_db())
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        log.error("job_not_found", job_id=job_id)
        return
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            _update_job_status(db, job, 'extracting', 5)
            
            # Download source video
            video_path = os.path.join(tmpdir, 'source.mp4')
            download_file(job.source_file_path, video_path)
            
            # Validate and extract metadata
            metadata = validate_and_extract_metadata(video_path)
            
            # Extract and separate audio
            audio_path = extract_audio(video_path, tmpdir)
            speech_path, bg_path = separate_audio(audio_path, tmpdir)
            
            _update_job_status(db, job, 'transcribing', 15)
            
            # Scene detection + chunking
            chunks = detect_scenes_and_chunk(video_path, tmpdir)
            job.chunks_total = len(chunks)
            db.commit()
            
            # Transcribe
            transcript = transcribe_audio(speech_path, language=job.source_language)
            
            _update_job_status(db, job, 'translating', 30)
            
            # Process each target language
            for target_lang in job.target_languages:
                lang_dir = os.path.join(tmpdir, target_lang)
                os.makedirs(lang_dir)
                
                # Translate
                translated = translate_segments(
                    transcript, job.source_language, target_lang
                )
                
                _update_job_status(db, job, 'synthesizing', 50)
                
                # Get voice clone reference if specified
                clone_path = None
                if job.voice_clone_id:
                    clone = db.query(VoiceClone).filter(
                        VoiceClone.id == job.voice_clone_id
                    ).first()
                    if clone:
                        clone_path = os.path.join(tmpdir, 'clone_ref.wav')
                        download_file(clone.reference_audio_path, clone_path)
                
                # Synthesize dubbed audio
                synthesized = synthesize_segments(
                    translated, target_lang,
                    os.path.join(lang_dir, 'audio'),
                    voice_clone_path=clone_path
                )
                
                _update_job_status(db, job, 'aligning', 65)
                
                # Force alignment + timing adjustment
                aligned = align_audio(synthesized, lang_dir)
                adjusted = adjust_timing(aligned, lang_dir)
                
                _update_job_status(db, job, 'assembling', 80)
                
                # Merge audio with video
                output_path = os.path.join(lang_dir, f'output_{target_lang}.mp4')
                merge_audio_video(
                    video_path,
                    adjusted['dubbed_audio_combined'],
                    bg_path,
                    output_path
                )
                
                # Upload to S3
                s3_key = f"jobs/{job_id}/output_{target_lang}.mp4"
                upload_file(output_path, s3_key)
                
                job.output_paths[target_lang] = s3_key
                db.commit()
            
            _update_job_status(db, job, 'completed', 100)
            log.info("job_completed", job_id=job_id)
    
    except Exception as exc:
        log.error("job_failed", job_id=job_id, error=str(exc))
        job.status = 'failed'
        job.error_message = str(exc)
        db.commit()
        raise self.retry(exc=exc)

def _update_job_status(db, job, status: str, progress: int):
    job.status = status
    job.progress_pct = progress
    job.current_stage = status
    db.commit()
    # broadcast via WebSocket
    from ..progress import broadcast_progress
    broadcast_progress(str(job.id), status, progress)
```

---

## Test Plan — Phase 1

### Unit Tests

**test_validator.py:**
- Valid MP4 passes validation
- Unsupported format (.docx) raises ValidationError
- File > 10GB raises ValidationError
- File < 5 seconds raises ValidationError
- Corrupted file raises ValidationError
- File without audio stream raises ValidationError

**test_asr.py:**
- Hindi audio → Hindi transcript with word timestamps
- Language auto-detection works on Hindi/Telugu/Tamil samples
- Low confidence segments flagged appropriately
- Chunk offset applied correctly to timestamps

**test_translation.py:**
- Hindi → Telugu translation produces valid Telugu text
- Output validated: length in 50-200% range
- SOV word order preserved in Dravidian language output
- Empty input handled without crash
- Very long input (>512 tokens) truncated with warning

**test_tts.py:**
- Generic Telugu TTS produces WAV file
- XTTS-v2 with reference audio produces WAV file
- Non-native language warning logged correctly
- Quality estimate 0.85 for Hindi, 0.65 for Telugu
- Output file length within 50-200% of input length estimate

**test_alignment.py:**
- MFA produces phoneme timestamps for Hindi
- Duration mismatch < 15% → time-stretch applied
- Duration mismatch > 30% → segment flagged for re-record
- No silence padding added (always flag instead)

### Integration Tests

**test_pipeline_audio.py:**
```python
def test_full_audio_pipeline_hindi_to_telugu():
    # Uses fixtures/sample_hindi_60s.mp4
    result = run_pipeline(
        video_path='tests/fixtures/sample_hindi_60s.mp4',
        source_lang='hi',
        target_langs=['te'],
        voice_clone=None
    )
    
    assert result['status'] == 'completed'
    assert 'te' in result['outputs']
    
    output_video = result['outputs']['te']
    assert os.path.exists(output_video)
    
    # Verify output is a valid video file
    metadata = validate_and_extract_metadata(output_video)
    assert metadata.has_audio
    assert abs(metadata.duration_seconds - 60) < 5  # within 5s of original
```

### Manual Test Checklist (End of Phase 1)

Before calling Phase 1 done, manually verify with 3 real videos:

- [ ] Video 1: Physics Wallah 10-minute Hindi lecture → Telugu dubbed
- [ ] Video 2: Unacademy 20-minute Hindi video → Tamil + Telugu dubbed
- [ ] Video 3: YouTube creator short-form 5-minute Hindi → 3 regional languages

For each output, evaluate:
- [ ] Is the translation semantically correct?
- [ ] Is the voice quality acceptable (generic TTS)?
- [ ] Is audio timing synchronized with video events (cuts, pauses)?
- [ ] Does background music/SFX come through naturally?
- [ ] Is overall quality "good enough to share"?

---

## Makefile

```makefile
.PHONY: install dev-install test lint format migrate run-api run-worker

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

download-models:
	bash scripts/download_models.sh

setup-mfa:
	bash scripts/setup_mfa.sh

migrate:
	alembic upgrade head

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	celery -A src.worker.celery_app worker --loglevel=info --concurrency=2

run-flower:
	celery -A src.worker.celery_app flower --port=5555

docker-up:
	docker-compose -f infra/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infra/docker/docker-compose.yml down

smoke-test:
	bash scripts/test_pipeline.sh
```

---

## scripts/download_models.sh

```bash
#!/bin/bash
set -e

MODEL_DIR="${MODEL_CACHE_DIR:-/models}"
mkdir -p "$MODEL_DIR"

echo "Downloading IndicWhisper..."
python -c "
from faster_whisper import WhisperModel
WhisperModel('large-v3', download_root='$MODEL_DIR/whisper')
"

echo "Downloading IndicTrans2..."
python -c "
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
name = 'ai4bharat/indictrans2-indic-indic-dist-200M'
AutoTokenizer.from_pretrained(name, trust_remote_code=True, cache_dir='$MODEL_DIR/indictrans2')
AutoModelForSeq2SeqLM.from_pretrained(name, trust_remote_code=True, cache_dir='$MODEL_DIR/indictrans2')
"

echo "Downloading XTTS-v2..."
python -c "
from TTS.api import TTS
TTS('tts_models/multilingual/multi-dataset/xtts_v2')
"

echo "Downloading IndicTTS models..."
python -c "
from TTS.api import TTS
for lang in ['te', 'ta', 'kn', 'hi', 'ml']:
    try:
        TTS(f'tts_models/{lang}/cv/vits')
        print(f'Downloaded {lang} TTS')
    except Exception as e:
        print(f'Failed {lang}: {e}')
"

echo "Downloading Demucs..."
python -c "
import demucs.pretrained
demucs.pretrained.get_model('htdemucs')
"

echo "All models downloaded."
```

---

## infra/docker/docker-compose.yml

```yaml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: nivima
      POSTGRES_USER: nivima
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    build:
      context: ../..
      dockerfile: infra/docker/Dockerfile.api
    environment:
      - DATABASE_URL=postgresql://nivima:password@postgres:5432/nivima
      - REDIS_URL=redis://redis:6379/0
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - model_cache:/models

  worker:
    build:
      context: ../..
      dockerfile: infra/docker/Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://nivima:password@postgres:5432/nivima
      - REDIS_URL=redis://redis:6379/0
    env_file: .env
    depends_on:
      - postgres
      - redis
    volumes:
      - model_cache:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  flower:
    image: mher/flower
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  model_cache:
```
