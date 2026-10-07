# Nivima — Master Project Document
**Version:** 1.0  
**Status:** Planning → Build  
**Owner:** Manoj

---

## 1. What This Is

An end-to-end multilingual video dubbing platform built specifically for Indian independent educators, YouTube creators, and EdTech companies.

**Core value proposition:**  
Upload one video in any Indian language. Get it back dubbed in 8 languages with the original creator's cloned voice and approximate lip sync — without re-recording, without a studio, without a budget.

**Tagline:** Your content. Every language. Your voice.

---

## 2. The Problem — Precisely Stated

Indian independent educators create content in one language (usually Hindi or Telugu). Students who speak Tamil, Kannada, Bengali, Malayalam — they either watch with subtitles or don't watch at all.

Existing solutions fail this market:
- NeuralGarage / Flawless AI — cinema-grade, enterprise pricing, inaccessible to creators
- HeyGen / Synthesia — talking head only, western face bias, expensive
- Dubverse / Dubdub.ai — audio dubbing only, no visual lip sync layer
- YouTube auto-translate — audio only, terrible quality, no voice preservation

Nobody has: **audio dubbing + voice cloning + lip sync + playback-speed awareness**, at creator-accessible pricing, for Indian languages.

---

## 3. Competitive Landscape

| Player | What They Do | What They Miss | Our Angle |
|---|---|---|---|
| NeuralGarage (VisualDub) | Cinema lip sync, 40+ facial muscles, used in Coolie | Enterprise pricing, studio sales motion | Creator/EdTech price point |
| HeyGen | Talking head, polished UX | Western face bias, no Indian language stack | Indian face + language |
| Sync Labs (sync-3) | Best technical quality, 4K, 95+ languages | No Indian language pipeline, expensive | Indian specific stack |
| Dubverse.ai | 30+ Indian languages, creator focused | Audio only, zero visual component | Add visual layer |
| Dubdub.ai | 50+ languages, voice cloning | No lip sync | Visual layer |
| XTTS-v2 (Coqui) | Cross-lingual voice clone from 6s audio | Model only, no product | We build product on top |
| AI4Bharat | IndicWhisper, IndicTTS, IndicTrans2 — 22 languages | Research tools, not a product | We productize their stack |

**Important:** Coqui (XTTS maintainer) has shut down. XTTS-v2 weights are frozen — no future updates. We use it but we need a fallback. Sarvam AI is the Indian alternative.

---

## 4. The Real Moat — Layered

**Layer 1 — Indian language dubbing pipeline**  
Replicable in 18 months by a funded competitor. Not a moat alone.

**Layer 2 — Indian educator voice clone dataset**  
Ground truth dubbed pairs from real creators. Takes 2-3 years to replicate.

**Layer 3 — Speed-invariant playback-adaptive lip sync**  
The unsolved research problem we identified. No competitor has this.  
Details in Section 8.

Layer 3 is the patent, the paper, and the product differentiation simultaneously.

---

## 5. What It Solves vs What It Doesn't

**Solves:**
- EdTech lecture localization (Hindi → 8 regional languages)
- Corporate training video multilingual versions
- YouTube creator pan-India reach
- Reducing dubbing iterations from 8 takes to 2
- Voice preservation across languages via cloning

**Explicitly does not solve (be honest about this):**
- Cinema-grade output — NeuralGarage owns this
- Real-time video calls — latency physically impossible currently
- Profile shots and heavy occlusion — we skip, flag, let human fix
- Emotion preservation across languages — unsolved globally
- Multiple simultaneous speakers — degrades, partial support only
- Songs and music — lyrics dubbing is a completely different problem
- Very low resolution source footage — garbage in, garbage out
- Playback speed artifacts — addressed partially in Phase 2, fully in Phase 3

---

## 6. Full System Architecture

### 6.1 High-Level Pipeline

```
INPUT
  └─ Video file (any format, any length, 1min to 5hr)
  └─ Source language (auto-detected if not specified)
  └─ Target languages (1 to 8)
  └─ Voice clone reference audio (optional, 6s minimum)

PIPELINE
  ├─ Stage 1: Ingestion & Preprocessing
  ├─ Stage 2: Scene Detection & Chunking
  ├─ Stage 3: Audio Extraction & Transcription
  ├─ Stage 4: Translation (Lip-Sync Aware)
  ├─ Stage 5: Voice Synthesis (Cloned or Generic)
  ├─ Stage 6: Force Alignment
  ├─ Stage 7: Scene Classification (reanimation decision)
  ├─ Stage 8: Lip Reanimation (selective)
  ├─ Stage 9: Temporal Smoothing
  ├─ Stage 10: Assembly & Render
  └─ Stage 11: QC Scoring & Human Review Queue

OUTPUT
  └─ Dubbed video per target language
  └─ QC report with per-scene confidence scores
  └─ Flagged segments list for human review
  └─ Animation manifest (Phase 3 — speed-invariant playback)
```

### 6.2 Stage-by-Stage Detail

**Stage 1: Ingestion & Preprocessing**
```
Input validation:
  - Supported formats: MP4, MKV, AVI, MOV, WebM
  - Max file size: 10GB (Phase 1), unlimited with chunked upload (Phase 2)
  - Auto-detect source language via IndicWhisper language ID

Preprocessing:
  - Extract audio track: FFmpeg → WAV 16kHz mono
  - Extract video track: FFmpeg → frame sequence
  - Detect resolution, fps, codec metadata
  - Store original untouched — never modify source
```

**Stage 2: Scene Detection & Chunking**
```
Tool: PySceneDetect (content-aware detection)
Output: List of scene boundaries with timestamps

Chunking strategy:
  - Each scene = one processing unit
  - Maximum chunk length: 30 seconds
  - If scene > 30s: split at silence boundaries using WebRTC VAD
  - Minimum chunk: 0.5s (ignore, don't process)

Why chunking matters:
  - Enables parallel processing across chunks
  - Isolates failures — one bad chunk doesn't kill entire video
  - Enables targeted reprocessing without full re-run
```

**Stage 3: Audio Extraction & Transcription**
```
Model: IndicWhisper (AI4Bharat) — fine-tuned Whisper for 12 Indian languages
Fallback: OpenAI Whisper large-v3 for unsupported languages

Output per chunk:
  - Full transcript text
  - Word-level timestamps
  - Confidence score per word
  - Detected language

Speaker diarization:
  - Tool: pyannote-audio
  - Output: who speaks when (Speaker 1, Speaker 2...)
  - Multi-speaker scenes: transcribe each speaker separately
  - This feeds into Stage 8 — only reanimate the active speaker
```

**Stage 4: Lip-Sync Aware Translation (Path A — The Core Innovation)**
```
This is not naive translation. This is constrained generation.

Input per chunk:
  - Source text segment
  - Phoneme timing map from Stage 3
  - Viseme sequence (mouth shapes at each timestamp)
  - Critical timestamps (close-up frames where lips visible)
  - Duration constraint (target audio must fit within ± 15% of original)

Phoneme → Viseme mapping:
  PHONEME_VISEME_MAP = {
    'p', 'b', 'm'  → 'bilabial_closure',    # fully closed
    'f', 'v'       → 'labiodental',          # teeth on lip
    'aa', 'ah'     → 'open_wide',            # open wide
    'ee', 'ih'     → 'spread',               # lips spread
    'oo', 'uw'     → 'rounded',              # lips rounded
    'th', 'dh'     → 'dental',               # tongue near teeth
    't', 'd', 'n'  → 'alveolar',             # tongue on ridge
    # Telugu/Tamil specific phonemes added
    'retroflex'    → 'custom_retroflex',
  }

LLM prompt (per chunk):
  System: "You are a professional dubbing scriptwriter. Generate
           {target_language} dialogue under phonetic constraints."
  
  Constraints passed:
    1. Semantic: same meaning as source
    2. Duration: fit within {duration_ms} milliseconds
    3. Phoneme match: at timestamp {ts}ms use word with {phoneme} sound
    4. Natural speech rhythm in {target_language}
    5. SOV word order for Dravidian languages (Telugu, Tamil, Kannada)
    6. Avoid code-mixing unless original has it

Model: IndicTrans2 (AI4Bharat) for initial translation
       + LLM rewrite pass (Llama 3.1 8B fine-tuned) for constraint satisfaction

Output: target language script, per-segment, with timing annotations
```

**Stage 5: Voice Synthesis**
```
Two modes:

Mode A — Generic Voice (no clone):
  Model: AI4Bharat IndicTTS (13 Indian languages)
  Fallback: Parler-TTS with Indian language support
  Output: natural TTS in target language

Mode B — Creator Voice Clone:
  Model: XTTS-v2 (Coqui) — cross-lingual voice cloning from 6s audio
  Input: creator's reference audio + translated script
  Output: dubbed audio in creator's voice speaking target language
  
  Limitation to disclose: XTTS-v2 supports Hindi natively.
  Telugu, Tamil, Kannada: use Hindi phoneme approximation + IndicTTS
  blend. Not perfect — disclosed to users as "voice-inspired" not
  "exact clone" for non-Hindi target languages.
  
  Future: Fine-tune XTTS-v2 on IndicVoices-R dataset for better
  regional language voice cloning. IndicVoices-R accepted at NeurIPS
  2025, 1704 hours, 10496 speakers across 22 languages — this is
  our fine-tuning data.
```

**Stage 6: Force Alignment**
```
Tool: Montreal Forced Aligner (MFA) with Indian language acoustic models
Fallback: Whisper-based alignment for languages without MFA model

Input: dubbed audio + translated script
Output: phoneme-level timestamps in dubbed audio
  {
    "word": "నమస్కారం",
    "start_ms": 1240,
    "end_ms": 1680,
    "phonemes": [
      {"phoneme": "n", "start_ms": 1240, "end_ms": 1280},
      {"phoneme": "a", "start_ms": 1280, "end_ms": 1340},
      ...
    ]
  }

Audio timing adjustment:
  If dubbed audio > original duration by >15%:
    - Time-stretch using librosa (perceptually transparent up to 15%)
    - If >15% stretch needed: flag segment for re-recording
  
  If dubbed audio < original duration by >20%:
    - Add natural pause or slow speech rate
    - Never add silence padding — sounds unnatural
```

**Stage 7: Scene Classification (Reanimation Decision Engine)**
```
This is what separates product from demo.
Run BEFORE reanimation. Decide per-scene.

Features extracted per scene:
  - Face detection confidence (MediaPipe FaceMesh)
  - Head pose: yaw (left-right), pitch (up-down), roll angles
    Tool: 3DDFA-V2 CNN model
  - Occlusion score: hand/beard/hair over mouth region
  - Face size in frame (% of frame area)
  - Motion blur score
  - Lighting consistency score
  - Number of detected faces

Decision logic:
  FRONTAL_CLEAR:
    yaw < ±20°, pitch < ±15°, occlusion < 10%, confidence > 0.9
    → Run MuseTalk (speed tier) or LatentSync (quality tier)
  
  PARTIAL_VISIBLE:
    yaw < ±40°, confidence > 0.7
    → Run MuseTalk, lower confidence output, flag for review
  
  PROFILE_SHOT:
    yaw > ±40°
    → SKIP reanimation. Rely on Path A audio alignment only.
  
  OCCLUDED:
    occlusion > 40%
    → SKIP reanimation. Flag for manual review.
  
  MULTI_FACE:
    >1 face detected
    → Run speaker diarization output to identify active speaker
    → Reanimate active speaker face only
    → Flag if cannot determine active speaker
  
  NO_FACE:
    No face detected (B-roll, text slides, animations)
    → SKIP. No reanimation needed.
  
  LOW_QUALITY:
    Face region < 64x64 pixels in frame
    → SKIP. Model output would be worse than original.

Output: per-scene decision map JSON
```

**Stage 8: Lip Reanimation**
```
Two tiers (user selects):

Speed Tier (MuseTalk 1.5):
  - 30fps+ on V100 GPU
  - 256x256 face region
  - Latent space inpainting (single step, no diffusion)
  - Best for: EdTech, corporate, YouTube creators
  - Processing: ~2x realtime (1min video = 2min processing)

Quality Tier (LatentSync 1.6):
  - Multi-step latent diffusion
  - Higher fidelity, temporal consistency via TREPA
  - Processing: ~10x realtime (1min video = 10min processing)
  - Best for: OTT pre-production, premium tier customers

Temporal consistency post-processing (both tiers):
  1. Extract lip region per frame
  2. Optical flow between adjacent frames
  3. Weighted blend to reduce flicker
  4. Preserve non-lip regions exactly (PSNR check)
  
  If PSNR of non-lip region drops below threshold:
    → Compositing error detected
    → Revert that frame to original
    → Flag in QC report

Indian face fine-tuning:
  Base: MuseTalk 1.5 pretrained weights
  Fine-tune on: VoxCeleb2 Indian subset + our collected dataset
  Dataset plan: 50 volunteers × 10min = 500min talking face video
  Fine-tuning: visual quality discriminator on Indian skin tones
  Compute: ~24hr on A100 (~$25 on Vast.ai)
```

**Stage 9: Temporal Smoothing & Compositing**
```
Per-frame operations:
  1. Detect lip region bounding box
  2. Blend reanimated region with original using feathered mask
  3. Optical flow warp to ensure smooth transition at boundaries
  4. Color correction: match illumination of reanimated region
     to surrounding face pixels
  5. Temporal smooth: weighted average across 3 adjacent frames
     in lip region only

Compositing pipeline:
  original_frame[lip_region] = alpha_blend(
    reanimated_lip,
    original_lip,
    alpha=confidence_score  # higher confidence = more reanimated
  )

Output: composited frame sequence
```

**Stage 10: Assembly & Render**
```
FFmpeg pipeline:
  1. Concatenate processed chunk frame sequences
  2. Merge dubbed audio track
  3. Preserve original: background audio, music, sound effects
     (separate from speech using Demucs audio source separation)
  4. Re-encode at original resolution and bitrate
  5. Add metadata: language, processing version, QC score

Output format: MP4 H.264 (universal compatibility)
Optional: VP9 for web, HEVC for quality tier
```

**Stage 11: QC Scoring & Human Review Queue**
```
Automated metrics per scene:
  - SyncNet score: audio-visual correlation
  - CSIM: face identity preservation
  - PSNR on non-lip regions
  - Temporal consistency variance (flickering detector)

Overall video score: weighted average of scene scores

Flagging thresholds:
  SyncNet < 5.0          → Flag for review
  CSIM < 0.85            → Flag (identity not preserved)
  PSNR_non_lip < 35dB    → Compositing error, auto-revert
  Temporal variance > σ  → Flickering detected, flag

Human review queue:
  - Dashboard showing flagged scenes
  - Side-by-side: original vs reanimated
  - Reviewer actions: approve / reject / re-process
  - Rejected scenes: revert to original video + dubbed audio only
```

---

## 7. The Speed Playback Problem — Architecture

### Why It's A Real Problem
Indian students routinely watch at 1.5x and 2x. Generated lip movements look increasingly mechanical at non-1x speeds because the model learned natural mouth physics at 1x.

This is not an edge case. It's the primary usage pattern of the core customer.

### Phase 2 Solution: High-Framerate Pre-Render
```
Instead of 24fps rendering:
  Render reanimated output at 48fps

At playback:
  1x  → display every frame (48fps source = 48fps playback → smooth)
  0.5x → display every frame slowed (still 48fps source, smooth)
  1.5x → skip every 3rd frame (32fps effective, acceptable)
  2x  → display every other frame (24fps effective, acceptable)

Storage: 2x original. Processing: same GPU time (48 frames not 24
per second of output, but parallelizable).

Covers 80% of real use cases.
```

### Phase 3 Solution: Speed-Invariant Playback (The Moat)
```
Architecture: Decouple animation from pixels

Component 1 — Base Video:
  Original video, no modification. Stored once.

Component 2 — Animation Manifest:
  Not pixel data. Lightweight JSON.
  {
    "version": "1.0",
    "fps": 24,
    "segments": [
      {
        "frame": 142,
        "timestamp_ms": 5916,
        "viseme": "open_wide",
        "intensity": 0.87,
        "duration_frames": 4,
        "speaker_id": "S1",
        "blend_weights": {
          "jaw_open": 0.7,
          "lip_corner_puller": 0.3,
          "upper_lip_raiser": 0.4
        }
      },
      ...
    ],
    "face_mesh_reference": "speaker_S1_mesh.bin"
  }

Component 3 — Custom Player (VoxPlayer SDK):
  At render time:
    1. Read base video frame
    2. Read animation manifest entry for current timestamp
       (scaled by playback speed)
    3. Apply blendshape deformation to face mesh
    4. Composite deformed lip region onto base frame
    5. Output final frame

  Speed handling:
    manifest_timestamp = real_timestamp × playback_speed
    Look up viseme at manifest_timestamp
    Interpolate between adjacent visemes if needed
    
    Result: lip movement always matches audio at any playback speed

Technology: 3D Morphable Model (3DMM) blendshapes
  - Pre-compute face mesh for each speaker once
  - Runtime deformation is < 2ms per frame on CPU
  - Works on mobile without GPU
  - This is how video game facial animation works — we apply
    it to dubbing for the first time

Research contribution: first application of real-time 3DMM-based
playback-adaptive lip sync in a dubbing pipeline.
This is the paper. This is the patent.
```

---

## 8. Model Stack — Final Decisions

| Component | Primary | Fallback | License |
|---|---|---|---|
| ASR | IndicWhisper (AI4Bharat) | Whisper large-v3 | MIT / Apache |
| Translation | IndicTrans2 (AI4Bharat) | NLLB-200 (Meta) | MIT / CC-BY |
| Constrained rewrite | Llama 3.1 8B (fine-tuned) | GPT-4o API | Llama community |
| TTS (generic) | IndicTTS (AI4Bharat) | Parler-TTS | MIT |
| Voice cloning | XTTS-v2 (Coqui) | Sarvam AI TTS | CPML (non-commercial OK) |
| TTS dataset | IndicVoices-R (NeurIPS 2025) | LJSpeech | CC-BY |
| Lip sync (speed) | MuseTalk 1.5 (Tencent) | Wav2Lip | Apache |
| Lip sync (quality) | LatentSync 1.6 (ByteDance) | VideoReTalking | Apache |
| Face detection | MediaPipe FaceMesh | dlib | Apache |
| Head pose | 3DDFA-V2 | OpenFace | MIT |
| Speaker diarization | pyannote-audio 3.x | SpeechBrain | MIT |
| Scene detection | PySceneDetect | custom FFmpeg | BSD |
| Audio separation | Demucs (Meta) | Spleeter | MIT |
| Force alignment | Montreal Forced Aligner | Whisper alignment | MIT |
| Temporal smooth | OpenCV optical flow | custom | Apache |

**Critical note:** XTTS-v2 supports Hindi officially. For other
Indian languages — Telugu, Tamil, Kannada — XTTS-v2 performance
degrades. Mitigation: fine-tune on IndicVoices-R. This is Phase 2 work.

---

## 9. Data Strategy

### Existing Public Datasets
| Dataset | What | Size | Use |
|---|---|---|---|
| IndicVoices-R | Indian TTS, 22 langs | 1704 hr, 10496 speakers | TTS fine-tune |
| IndicWhisper/Vistaar | Indian ASR benchmarks | 10,700 hr, 12 langs | ASR evaluation |
| VoxCeleb2 | Celebrity talking face | 1M+ utterances | Lip sync base |
| LRS2/LRS3 | BBC talking face, English | 150k utterances | Lip sync base |
| MUAVIC | Multilingual audio-visual | 9 languages | Multilingual lip sync |
| AI4Bharat IndicTTS | TTS training data | 13 langs | TTS |

### Data We Build (The Moat)
**Phase 1 — Indian face dataset:**
- 50 Indian volunteers, diverse: skin tone, age, gender, facial hair
- 10 minutes each, reading prepared sentences in their native language
- Sentences cover all viseme shapes (designed phoneme coverage)
- Equipment: standard smartphone, ring light, plain background
- Annotation: automatically via MFA + MediaPipe
- Size: 500 minutes of talking face data
- Cost: ₹10,000 volunteer incentives + ₹2,000 equipment

**Phase 2 — Dubbed ground truth pairs:**
- Partner with 5 regional YouTube educators
- Collect: original Hindi video + manually dubbed Telugu/Tamil version
- These are gold pairs — real dubbing ground truth
- Target: 100 hours of ground truth dubbed pairs
- This dataset doesn't exist anywhere. This is the moat.

**Phase 3 — Feedback loop:**
- Every human review correction in QC queue
- Feeds back into fine-tuning pipeline
- Model improves on exactly the content types customers use
- More customers → better data → better model → more customers
- Classic data flywheel

---

## 10. Infrastructure & Deployment

### Processing Pipeline Infrastructure
```
Job Queue: Celery + Redis
  - Each video = one job
  - Each chunk = one sub-task
  - Priority queue: paid users > free tier

Worker Infrastructure: Kubernetes
  - Auto-scale based on queue depth
  - GPU workers for: MuseTalk, LatentSync, XTTS-v2
  - CPU workers for: FFmpeg, MFA, scene detection, QC

GPU Strategy:
  Development: Google Colab Pro+ (A100)
  MVP: Vast.ai spot instances (~$1/hr A100)
  Scale: AWS p3.2xlarge or GCP A100 with auto-scaling
  Cost target: < $0.04/minute of video processed

Storage:
  Raw uploads: S3-compatible (Cloudflare R2 — egress free)
  Processed outputs: same
  Models: EFS or persistent volume on Kubernetes
  Animation manifests (Phase 3): tiny, store in PostgreSQL

CDN: Cloudflare for output video delivery
```

### API Architecture
```
FastAPI backend
  POST /api/v1/jobs          — submit dubbing job
  GET  /api/v1/jobs/{id}     — poll job status
  GET  /api/v1/jobs/{id}/output  — download result
  POST /api/v1/voices        — register voice clone
  GET  /api/v1/qc/{job_id}   — get QC report
  POST /api/v1/qc/review     — submit human review decision

WebSocket: /ws/jobs/{id}/progress
  — real-time progress updates
  — stage completion events
  — ETA updates

Rate limiting: per API key, tier-based
Auth: JWT + API key for programmatic access
```

### Database Schema (Core Tables)
```sql
jobs (
  id UUID PRIMARY KEY,
  user_id UUID,
  status ENUM(queued, processing, qc_review, completed, failed),
  source_language VARCHAR,
  target_languages VARCHAR[],
  source_duration_seconds INTEGER,
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  processing_cost_cents INTEGER
)

chunks (
  id UUID PRIMARY KEY,
  job_id UUID REFERENCES jobs,
  chunk_index INTEGER,
  start_ms INTEGER,
  end_ms INTEGER,
  scene_classification JSONB,
  qc_scores JSONB,
  reanimation_applied BOOLEAN,
  status ENUM(...)
)

voice_clones (
  id UUID PRIMARY KEY,
  user_id UUID,
  display_name VARCHAR,
  reference_audio_path VARCHAR,
  supported_languages VARCHAR[],
  created_at TIMESTAMP
)

qc_queue (
  id UUID PRIMARY KEY,
  chunk_id UUID REFERENCES chunks,
  flag_reason VARCHAR,
  flagged_at TIMESTAMP,
  reviewed_at TIMESTAMP,
  reviewer_decision ENUM(approve, reject, reprocess)
)
```

---

## 11. Build Phases

### Phase 1 — Path A: Script Generation Only (Month 1-3)
**Goal:** Working dubbed audio, no video manipulation.

**What you build:**
- Ingestion API (FastAPI)
- Audio extraction (FFmpeg)
- Transcription (IndicWhisper)
- Translation (IndicTrans2)
- Constrained rewrite (Llama 3.1 8B via Ollama)
- TTS (IndicTTS)
- Force alignment (MFA)
- Audio merge (FFmpeg)
- Basic job queue (Celery + Redis)
- Simple web UI: upload → status → download

**What you skip:** Everything visual. No face detection. No lip sync.

**Deliverable:** Upload Hindi lecture, get Telugu dubbed audio track merged with original video. No visual changes. Works.

**Demo target:** Take 3 real Physics Wallah Hindi videos, dub them in Telugu and Tamil. Share with 5 Telugu students. Measure reaction.

---

### Phase 2 — Add Visual Layer (Month 3-6)
**Goal:** Selective lip reanimation for frontal clear scenes.

**What you build:**
- Scene detection (PySceneDetect)
- Chunking pipeline
- Face detection + head pose (MediaPipe + 3DDFA-V2)
- Scene classifier (FRONTAL_CLEAR vs SKIP)
- MuseTalk integration (speed tier)
- Temporal smoothing (OpenCV)
- QC scoring (SyncNet-based)
- Human review queue (simple dashboard)
- High-framerate render (48fps for speed playback)

**Fine-tuning tasks:**
- Collect 50-volunteer Indian face dataset
- Fine-tune MuseTalk visual quality discriminator on Indian faces
- Fine-tune XTTS-v2 on IndicVoices-R for Telugu/Tamil voice cloning

**Deliverable:** Full pipeline. Upload video, select languages, get dubbed video with lip sync on frontal scenes, original video on profile/occluded scenes.

---

### Phase 3 — Speed-Invariant Playback (Month 6-12)
**Goal:** Build the research moat.

**What you build:**
- Animation manifest generation (viseme extraction → JSON)
- Face mesh computation per speaker (3DMM)
- Blendshape library for Indian phoneme set
- VoxPlayer SDK (web, React Native)
- Speed-adaptive playback at render time
- Manifest storage + delivery pipeline

**Research output:**
- Paper: "Speed-Invariant Lip Sync via Playback-Adaptive 3DMM Blendshapes for Multilingual Dubbing"
- Submit to: ACM MM 2026 or ICCV 2025 workshop
- Patent filing: provisional application on the manifest + player architecture

---

### Phase 4 — Platform & Revenue (Month 12+)
- Creator onboarding with voice clone setup
- Self-serve pricing tiers
- Analytics dashboard for creators
- API for EdTech platform integration
- LatentSync quality tier
- Language expansion beyond 8

---

## 12. Remaining Hard Problems — Not Ignored

**Songs and music:**
Completely different problem. Lyric dubbing requires prosody matching, rhyme matching, syllable matching. We explicitly exclude it in Phase 1-3. Mark scenes with music as SKIP in scene classifier.

**Audio longer than original:**
If dubbed audio is >15% longer than original segment:
- First try: constrained rewrite (tighter instructions to LLM)
- Second try: time-stretch up to 15%
- If still doesn't fit: flag for re-recording. Show user exactly which segment needs human work.

**Multi-speaker scenes:**
Use pyannote-audio speaker diarization. Reanimate only the active speaker per frame. If diarization confidence < 0.8, flag scene, skip reanimation.

**Copyright and consent:**
- Voice cloning a specific person requires explicit consent
- Terms of service: users warrant they have rights to voice they upload
- Creator voice clone: opt-in, documented consent flow
- Output copyright: user owns it, we take no rights
- DPDP Act (India's data protection law) compliance required for biometric voice data

**What if reanimation makes it worse:**
PSNR check on non-lip regions after compositing.
If PSNR drops below 35dB → compositing error → auto-revert that frame to original.
If >30% of frames in a scene revert → mark entire scene as SKIP, revert fully.

**Code-mixed content (Hinglish, Tanglish):**
Teachers often switch mid-sentence. IndicTrans2 handles code-mixed input reasonably. Flag segments with >20% code-mixing for human review of translation quality.

---

## 13. Metrics — How We Measure Success

**Technical metrics:**
- WER on source transcription: target < 10% on clean audio
- Translation BLEU score: target > 30 on IndicTrans2 benchmark
- SyncNet score: target > 7.0 on processed scenes
- CSIM (identity preservation): target > 0.85
- Processing time: target < 3× video duration on single A100
- Uptime: 99.5% for API

**Product metrics:**
- % of output scenes flagged for review: target < 20%
- % of flagged scenes that human reviewers approve: target > 70%
- Creator retention: % still using after 30 days
- Regional view increase: do creator's regional language views go up after dubbing?

**Business metrics:**
- Cost per minute processed: target < ₹3/minute
- Revenue per minute processed: ₹5-10/minute (paid tier)
- Gross margin target: >50%
- Time to first paying customer: month 4

---

## 14. Tech Stack Summary

```
Backend:         FastAPI (Python)
Job Queue:       Celery + Redis
Database:        PostgreSQL + pgvector (for embeddings)
Storage:         Cloudflare R2 (S3-compatible)
Container:       Docker + Kubernetes (k3s for dev, EKS for prod)
GPU Compute:     Vast.ai (dev) → AWS p3/p4 (prod)
ML Framework:    PyTorch + HuggingFace Transformers
Video:           FFmpeg + OpenCV
Frontend:        Next.js (simple upload/status/download)
Player SDK:      React + WebAssembly (Phase 3)
Monitoring:      Prometheus + Grafana
Experiment:      MLflow (model versioning, fine-tune tracking)
CI/CD:           GitHub Actions
```

---

## 15. Week 1 Start — Exactly This

```bash
# Environment setup
conda create -n nivima python=3.11
conda activate nivima

pip install openai-whisper faster-whisper
pip install montreal-forced-aligner
pip install TTS  # XTTS-v2
pip install fastapi celery redis
pip install ffmpeg-python opencv-python
pip install torch torchvision torchaudio

# First working script: transcribe → translate → TTS → merge
# Target: Hindi YouTube video → Telugu audio output
# No lip sync. Just audio. Prove the pipeline works.
```

**Day 1-3:** Whisper transcription working on 3 test videos
**Day 4-5:** IndicTrans2 translation working
**Day 6-7:** IndicTTS synthesis working, audio merged with FFmpeg

**Week 2:**
MFA force alignment. Constrained LLM rewrite. First end-to-end audio dub.

**Week 3-4:**
FastAPI wrapper. Job queue. Basic UI. First shareable demo.

---

## 16. References & Research Papers

1. Wav2Lip — Prajwal et al., ACM MM 2020
   "A Lip Sync Expert Is All You Need for Speech to Lip Generation in the Wild"

2. MuseTalk — Zhang et al., arXiv 2410.10122 (2024/2025)
   "Real-Time High Quality Lip Synchronization with Latent Space Inpainting"

3. LatentSync — Li et al., arXiv 2412.09262 (ByteDance, 2024)
   "Audio Conditioned Latent Diffusion Models for Lip Sync"

4. IndicTrans2 — AI4Bharat, 2023
   "Towards High-Quality and Accessible Machine Translation for All 22 Scheduled Indian Languages"

5. IndicWhisper / Vistaar — AI4Bharat, INTERSPEECH 2023
   "Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR"

6. IndicVoices-R — AI4Bharat, NeurIPS 2025 (Datasets Track)
   "Unlocking a Massive Multilingual Multi-speaker Speech Corpus for Scaling Indian TTS"

7. XTTS-v2 — Coqui AI, 2023
   "Cross-lingual voice cloning from 6-second reference audio"

8. 3DDFA-V2 — Guo et al., ECCV 2020
   "Towards Fast, Accurate and Stable 3D Dense Face Alignment"

9. NeRF-LipSync — ISPRS 2025
   "Diffusion + NeRF spatial alignment for view-consistent lip sync"

10. UniSync — arXiv 2603.03882, 2025
    "Towards Generalizable and High-Fidelity Lip Synchronization for Challenging Scenarios"

11. TBDub — arXiv 2609.06144, 2025
    "Production-Oriented Visual Dubbing"

12. pyannote-audio — Bredin et al., ICASSP 2023
    Speaker diarization

13. Demucs — Défossez et al., 2019/2021
    "Music Source Separation in the Waveform Domain"

14. Montreal Forced Aligner — McAuliffe et al., INTERSPEECH 2017

---

## 17. What This Project Is For You

**Portfolio:** A real ML + systems engineering project with depth.
Not a tutorial clone. Not a CRUD app with "AI" bolted on.

**Research:** The speed-invariant playback problem is publishable.
Target: ACM MM 2026, or EMNLP 2026 for the constrained translation angle.

**GSoC / LFX:** AI4Bharat, Mozilla Common Voice, and Hugging Face
all have tracks where this pipeline is directly relevant.
IndicVoices-R contribution is a real open-source angle.

**Startup:** The business case is real.
Market validated. Gap confirmed. Unit economics modeled.
Technical path is clear. Build the demo first.
