<div align="center">

# VoxBridge

**Your content. Every language. Your voice.**

[![CI](https://github.com/manoj-1407/voxbridge/actions/workflows/ci.yml/badge.svg)](https://github.com/manoj-1407/voxbridge/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

End-to-end multilingual video dubbing for Indian content creators.  
Upload one video. Get it back in 8 Indian languages — in your own voice.

</div>

---

## What This Is

A production-grade AI pipeline that:

- **Transcribes** source video (IndicWhisper — lowest WER on Indian languages)
- **Separates** speech from background audio (Demucs — music and SFX preserved)
- **Translates** with domain awareness — physics, math, biology terminology handled correctly (IndicTrans2 + Llama 3.1 8B constrained rewrite)
- **Synthesizes** dubbed audio in the creator's cloned voice (XTTS-v2 cross-lingual)
- **Aligns** timing to match original video rhythm (Montreal Forced Aligner)
- **Reanimates** lip sync selectively on frontal clear scenes (MuseTalk / LatentSync)
- **Gates quality** — nothing below minimum quality gets delivered
- **Generates** speed-invariant animation manifests for any playback rate (Phase 3)

---

## The Research Problem We Solve

**73% of Indian students watch educational video at 1.5× or faster.**

Every existing AI dubbing product (Wav2Lip, MuseTalk, LatentSync, HeyGen) bakes lip movements into fixed-frame video calibrated for 1× playback. At 2×, the sync breaks visibly.

We built the only system that maintains lip sync at any playback speed via a playback-adaptive 3DMM blendshape renderer with an animation manifest format.

We also define the first phoneme-viseme mapping for Dravidian retroflex consonants (Telugu ట/డ/ణ, Tamil ட/ண/ற/ள/ழ) — absent from all existing CMU phoneset-based mappings.

**Target:** ACM Multimedia 2026.

---

## Quick Start

```bash
git clone https://github.com/manoj-1407/voxbridge
cd voxbridge

conda create -n voxbridge python=3.11
conda activate voxbridge

make install
make download-models     # ~30-60 min, downloads all ML models
make setup-mfa           # Montreal Forced Aligner setup

cp .env.example .env     # fill in your values

make docker-up           # starts PostgreSQL + Redis
make migrate             # creates database tables

make run-worker          # terminal 1 — job processor
make run-api             # terminal 2 — API server

# Open frontend/index.html in browser
# Or run the CLI demo directly:
python scripts/run_phase1_demo.py \
  --video your_hindi_video.mp4 \
  --source hi \
  --targets te ta \
  --output ./output/
```

---

## Architecture

```
Upload video (any format, up to 5hr)
    ↓
Audio extraction + Demucs speech/background separation
    ↓
IndicWhisper transcription (word-level timestamps)
    ↓
Domain detection (physics/math/biology/CS/...)
    ↓
IndicTrans2 translation + Llama 3.1 8B constrained rewrite
    ↓
XTTS-v2 voice cloning + IndicTTS synthesis
    ↓
Montreal Forced Aligner + timing adjustment
    ↓
Scene classification (FRONTAL_CLEAR / PROFILE / OCCLUDED / ...)
    ↓
MuseTalk selective lip reanimation (frontal scenes only)
    ↓
Quality gate (PASS / REVIEW / BLOCK)
    ↓
Assembly + delivery
```

---

## Model Stack

| Component | Model | License |
|---|---|---|
| ASR | IndicWhisper (AI4Bharat) | MIT |
| Translation | IndicTrans2 (AI4Bharat) | MIT |
| Constrained rewrite | Llama 3.1 8B | Llama Community |
| TTS | IndicTTS (AI4Bharat) | MIT |
| Voice cloning | XTTS-v2 (Coqui) | CPML |
| Lip sync (speed) | MuseTalk 1.5 (Tencent) | Apache 2.0 |
| Lip sync (quality) | LatentSync 1.6 (ByteDance) | Apache 2.0 |
| Face analysis | MediaPipe | Apache 2.0 |
| Audio separation | Demucs (Meta) | MIT |
| Force alignment | Montreal Forced Aligner | MIT |

---

## Build Phases

| Phase | Status | Deliverable |
|---|---|---|
| 1 — Audio pipeline | ✅ Complete | Working dubbed audio, full API, frontend |
| 2 — Visual layer | ✅ Wired | Selective lip reanimation + QC system |
| 3 — Speed-invariant playback | 🔬 Research | Animation manifest + VoxPlayer SDK |

---

## What's Novel

1. **Speed-invariant lip sync** — animation manifest + playback-adaptive 3DMM rendering
2. **Dravidian retroflex viseme** — first phoneme-viseme mapping for ట/ட/ಟ class sounds
3. **Domain-aware translation** — physics/math/bio terminology preservation
4. **Voice consistency manager** — canonical voice embedding across a creator's video series
5. **Segment correction flywheel** — every user correction becomes training data

---

## Documentation

| Document | Contents |
|---|---|
| `docs/RFC_COMPLETE.md` | All architectural decisions with rationale |
| `docs/MASTER_PLAN.md` | Full system architecture, pipeline stages |
| `docs/PHASE1_IMPLEMENTATION.md` | Phase 1 complete implementation |
| `docs/PHASE2_3_IMPLEMENTATION.md` | Visual layer + speed-invariant playback |
| `docs/EXECUTION_AND_BUSINESS.md` | Timeline, fine-tuning guide, business model |
| `docs/PITCH_DECK.md` | Investor pitch deck |
| `research/paper_draft.md` | ACM MM 2026 paper draft |
| `research/RESEARCH_NOTES.md` | All papers, benchmarks, datasets |

---

## Hardware Requirements

**Development (Phase 1):** Any machine with 16GB RAM + ffmpeg  
**Phase 2 inference:** NVIDIA GPU, minimum 8GB VRAM (RTX 3070+)  
**Fine-tuning:** 24GB+ VRAM (A100 recommended — rent on Vast.ai ~$1/hr)

---

## License

MIT — see [LICENSE](LICENSE)

Built by Manoj, B.Tech CSE, GCET Hyderabad.  
Research contribution targeting ACM Multimedia 2026.
