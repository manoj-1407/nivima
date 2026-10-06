#!/bin/bash
set -e

echo "=== VoxBridge Smoke Test ==="

echo "[1] Checking ffmpeg..."
ffmpeg -version | head -1

echo "[2] Checking Python imports..."
python -c "
import faster_whisper
import transformers
import TTS
import demucs
import scenedetect
import librosa
import soundfile
import ffmpeg
import celery
import fastapi
import sqlalchemy
print('All imports: OK')
"

echo "[3] Checking Whisper transcription..."
python -c "
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
import urllib.request, tempfile, os
url = 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'
with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
    urllib.request.urlretrieve(url, f.name)
    segs, info = model.transcribe(f.name)
    segs = list(segs)
    os.unlink(f.name)
print(f'Whisper: detected language={info.language}, segments={len(segs)}: OK')
"

echo "[4] Checking API health..."
curl -s http://localhost:8000/health | python -m json.tool || echo "API not running (start with: make run-api)"

echo "[5] Checking Redis..."
redis-cli ping || echo "Redis not running (start with: make docker-up)"

echo "[6] Checking PostgreSQL..."
psql "$DATABASE_URL" -c "SELECT 1" > /dev/null && echo "PostgreSQL: OK" || echo "PostgreSQL not running (start with: make docker-up)"

echo ""
echo "=== Smoke test complete ==="
