# Nivima — RTX 3070 Deployment & Execution Guide

This guide details everything required to clone, configure, verify, and run the Nivima end-to-end pipeline on your **NVIDIA GeForce RTX 3070 (8GB VRAM)** workstation.

---

## 1. System Requirements & Hardware Context

- **GPU**: NVIDIA RTX 3070 (8GB GDDR6 VRAM)
- **OS**: Windows 10/11 or Ubuntu 22.04+ (both supported)
- **Python**: 3.10 or 3.11 (Python 3.11 recommended)
- **FFmpeg**: Must be installed and present on system PATH
- **Disk Space**: ~15–20 GB free space for weights (`~3GB Whisper`, `~1.5GB IndicTrans2`, `~2GB XTTS-v2`, `~1.5GB Demucs`)

---

## 2. Setup & Installation (One-Time)

### Step 2.1: Clone and Create Virtual Environment

```bash
# Clone repository
git clone https://github.com/manoj-1407/nivima.git
cd nivima

# Create virtual environment
python -m venv venv

# Activate venv:
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows CMD:
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate
```

### Step 2.2: Install PyTorch with CUDA Support

Install the PyTorch build matched to your CUDA driver (CUDA 12.1 is standard for RTX 30-series):

```bash
# For CUDA 12.1 (recommended for RTX 3070):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Or for CUDA 11.8:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Step 2.3: Install Nivima Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 2.4: Ensure FFmpeg is Installed

- **On Windows**:
  - Download from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) (Release Essentials zip).
  - Extract and add the `bin` directory to your user `PATH`.
  - Test by opening a new terminal and typing `ffmpeg -version`.
- **On Ubuntu/Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```

---

## 3. Pre-Flight Verification

Before running on real video, run our automated environment checker:

```bash
python scripts/check_environment.py
```

### Expected Output:
```text
=======================================================
  Python Environment
=======================================================
  ✓ Python 3.11.x

=======================================================
  System Tools
=======================================================
  ✓ ffmpeg: ffmpeg version ...
  ✓ ffprobe: ffprobe version ...

=======================================================
  GPU
=======================================================
  ✓ CUDA available: NVIDIA GeForce RTX 3070 (8.0GB VRAM)
  ✓ PyTorch version: 2.x.x+cu121
  ✓ CUDA version: 12.1

=======================================================
  Python Packages
=======================================================
  ✓ faster-whisper
  ✓ transformers
  ✓ TTS (Coqui)
  ✓ demucs
  ✓ ...
```

---

## 4. Run the Local Test Suite

Run unit and integration smoke tests to verify all plumbing:

```bash
pytest tests/unit/ tests/integration/test_api.py tests/integration/test_pipeline_smoke.py -v
```

On your 3070 (where `ffmpeg` is installed), **all 94 tests** (81 standard + 13 ffmpeg-dependent smoke tests) will execute and pass without skipping.

---

## 5. Pre-Download Model Weights (Optional but Recommended)

To avoid downloading multi-gigabyte models while executing your first video test:

```bash
python scripts/download_models.py
```

This caches:
1. `faster-whisper` (`large-v3`, ~3GB)
2. `IndicTrans2` (`indictrans2-indic-indic-dist-200M`, ~1GB)
3. `Coqui XTTS-v2` (~2GB)
4. `Demucs` (`htdemucs`, ~1.5GB)

---

## 6. Running Your First Real Video Test

Prepare a short Hindi video file (recommended: **30 seconds to 2 minutes** of a single speaker speaking clearly in Hindi).

Save it as `sample_hindi.mp4` in the project root.

### Execute Phase 1 Pipeline:

```bash
python scripts/run_phase1_demo.py \
    --video sample_hindi.mp4 \
    --source hi \
    --targets te \
    --output ./output_demo
```

### With Voice Cloning (Speaker Audio Match):
If you have a 6–10 second clean reference clip of the speaker's voice:

```bash
python scripts/run_phase1_demo.py \
    --video sample_hindi.mp4 \
    --source hi \
    --targets te \
    --voice reference_speaker.wav \
    --output ./output_demo
```

### Multi-Target Dubbing (Telugu + Tamil):
```bash
python scripts/run_phase1_demo.py \
    --video sample_hindi.mp4 \
    --source hi \
    --targets te ta \
    --output ./output_demo
```

---

## 7. Expected Pipeline Stages & Timing (RTX 3070)

For a **60-second Hindi video**:

| Stage | Process | RTX 3070 VRAM | Est. Time |
|---|---|---|---|
| **[1/6] Ingestion** | Metadata validation & format check | 0 MB | < 1 sec |
| **[2/6] Separation** | Demucs separates vocal from background | ~2.1 GB | ~8–12 sec |
| **[3/6] ASR** | Faster-Whisper large-v3 transcription | ~2.8 GB | ~3–5 sec |
| **[4/6] Translation** | IndicTrans2 Hindi → Telugu translation | ~1.2 GB | ~2–4 sec |
| **[5/6] TTS** | Coqui synthesis & voice clone | ~3.0 GB | ~15–20 sec |
| **[6/6] Assembly** | Time-stretching, background remuxing | 0 MB | ~3–5 sec |
| **Total** | **Full Dubbed Telugu Video** | **Peak ~3.5 GB** | **~35–50 sec** (< 1× realtime!) |

The resulting file will be located at:
`./output_demo/output_te.mp4`

---

## 8. Launching the Interactive Web UI

To run the complete Nivima web interface with live processing:

1. **Start the API backend**:
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **Open the frontend**:
   Open `frontend/index.html` in your browser.
3. Access API docs at `http://localhost:8000/docs`.

---

## 9. RTX 3070 Specific VRAM Optimization & Troubleshooting

Because the RTX 3070 has **8 GB VRAM**, sequential pipeline memory management is already optimized:

1. **CUDA Out of Memory (OOM)**:
   - Each pipeline stage loads its model, executes, and Python garbage collects.
   - If VRAM is constrained due to running browser/display windows simultaneously, set `WHISPER_COMPUTE_TYPE=int8_float16` or `float16` in `.env`.
2. **Demucs Fallback**:
   - If Demucs runs out of VRAM, the code automatically falls back to clean background silence without crashing.
3. **Telugu Pronunciation & TTS**:
   - Hindi has native XTTS-v2 support (~85% similarity).
   - Telugu uses the automated multi-tier fallback (IndicTTS VITS → XTTS-v2 → silence fallback).
4. **Timing Review Flags**:
   - If the speech length differential between Hindi and Telugu exceeds the threshold (1.2× speed ceiling), the CLI logs a review flag while safely scaling tempo without chipmunk distortion.
