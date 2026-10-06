#!/bin/bash
set -e

MODEL_DIR="${MODEL_CACHE_DIR:-./models}"
mkdir -p "$MODEL_DIR"

echo "=== VoxBridge Model Download ==="

echo "[1/5] Downloading Whisper large-v3..."
python -c "
from faster_whisper import WhisperModel
WhisperModel('large-v3', device='cpu', compute_type='int8', download_root='$MODEL_DIR/whisper')
print('Whisper: done')
"

echo "[2/5] Downloading IndicTrans2..."
python -c "
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
name = 'ai4bharat/indictrans2-indic-indic-dist-200M'
AutoTokenizer.from_pretrained(name, trust_remote_code=True, cache_dir='$MODEL_DIR/indictrans2')
AutoModelForSeq2SeqLM.from_pretrained(name, trust_remote_code=True, cache_dir='$MODEL_DIR/indictrans2')
print('IndicTrans2: done')
"

echo "[3/5] Downloading XTTS-v2..."
python -c "
from TTS.api import TTS
TTS('tts_models/multilingual/multi-dataset/xtts_v2')
print('XTTS-v2: done')
"

echo "[4/5] Downloading IndicTTS models..."
python -c "
from TTS.api import TTS
langs = ['te', 'ta', 'kn', 'hi', 'ml']
for lang in langs:
    try:
        TTS(f'tts_models/{lang}/cv/vits')
        print(f'IndicTTS {lang}: done')
    except Exception as e:
        print(f'IndicTTS {lang}: FAILED - {e}')
"

echo "[5/5] Downloading Demucs..."
python -c "
import demucs.pretrained
demucs.pretrained.get_model('htdemucs')
demucs.pretrained.get_model('mdx_extra_q')
print('Demucs: done')
"

echo ""
echo "=== All models downloaded to $MODEL_DIR ==="
echo "Disk usage:"
du -sh "$MODEL_DIR"
