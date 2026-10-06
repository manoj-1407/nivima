# VoxBridge — Complete RFC (Request For Comments)
**Version:** 1.0  
**Status:** Draft → Locked  
**Purpose:** Every architectural decision, tradeoff, open question, and rationale.
            This is the document you read before making any change to the system.

---

## Table of Contents
1. Problem Statement (Precise)
2. Non-Goals (Explicit)
3. System Constraints
4. Architecture Decisions (ADRs)
5. Open Questions
6. Risk Register
7. Dependency Map
8. Failure Modes

---

## 1. Problem Statement — Precise

Indian independent educators produce video content in one language.
Their content is inaccessible to students who speak other Indian languages.

Existing dubbing solutions either:
- Cost too much (NeuralGarage, Flawless AI — enterprise pricing)
- Produce audio only with no visual sync (Dubverse, Dubdub.ai)
- Don't support Indian languages properly (HeyGen, Synthesia)
- Don't preserve the teacher's voice (generic TTS tools)

The result: a Physics Wallah instructor with 2M Hindi subscribers reaches
zero Tamil Nadu students. Regional content is locked to its origin language.

We build: a pipeline that takes one video, outputs dubbed versions in N
languages, preserves the teacher's voice via cloning, applies visual lip
sync where technically feasible, and handles playback at variable speeds.

---

## 2. Non-Goals — Explicit

These are out of scope. Not now. Possibly never.

- Cinema-grade output (NeuralGarage owns this)
- Real-time video call dubbing (<200ms latency — physically impossible currently)
- Song/lyric dubbing (different problem, different models entirely)
- Dubbing non-Indian language content into Indian languages (Phase 1-3)
- Emotion transfer across languages (unsolved research problem globally)
- Profile shot lip reanimation (current models degrade badly, we skip)
- Lip sync on occluded faces (beard, hand, hair covering mouth — skip)
- Sub-64px face region reanimation (model output worse than original)
- Any content the user doesn't have rights to (copyright enforcement at ToS level)

---

## 3. System Constraints

**Hard constraints:**
- Processing must be async. No user-facing synchronous operation > 5 seconds.
- Original video must never be modified in storage. Always derive output.
- Non-lip regions of reanimated frames must match original within PSNR > 35dB.
- Voice cloning requires explicit user consent on the voice being cloned.
- No biometric voice data stored without user opt-in.

**Performance targets:**
- Turnaround: < 3x video duration on single A100 (Phase 1)
- Turnaround: < 1x video duration with parallel chunking (Phase 2)
- API response: < 200ms for job submission
- QC flag rate: < 20% of scenes flagged
- SyncNet score: > 7.0 on processed frontal scenes

**Cost targets:**
- Phase 1: < ₹4/minute processed (includes GPU compute)
- Phase 2: < ₹2.50/minute (self-hosted models, spot GPUs)
- Revenue target: ₹5-10/minute on paid tier

---

## 4. Architecture Decision Records (ADRs)

### ADR-001: Async Job Queue over Synchronous API

**Decision:** All video processing runs asynchronously via Celery + Redis.
Client submits job, gets job ID, polls for status via WebSocket or REST.

**Rationale:** 
- A 20-minute video takes 30-40 minutes to process.
- HTTP connections time out at 30-300 seconds depending on infrastructure.
- Sync API is physically impossible for this workload.

**Tradeoffs:**
- Adds complexity (job management, status tracking, failure handling)
- Requires WebSocket or polling on client side
- Better: users can close browser and come back — job still runs

**Rejected alternatives:**
- SSE (Server-Sent Events) — unidirectional, can't handle reconnection well
- Long polling — works but inefficient
- Webhook callback — good for API clients, bad for browser UI

---

### ADR-002: Chunk-Based Processing over Full-Video Processing

**Decision:** Every video is split into scene-boundary chunks before processing.
Each chunk is an independent processing unit in the job queue.

**Rationale:**
- A 3-hour film = 259,200 frames. Cannot hold in GPU memory at once.
- Chunking enables parallel processing (N chunks on N workers = N× speedup).
- Chunk failure doesn't kill the whole job — retry only failed chunk.
- Enables incremental output delivery (first chunks done while last chunks process).

**Chunk boundaries:**
- Primary: scene cuts detected by PySceneDetect (content-aware)
- Secondary: silence boundaries via WebRTC VAD (for long scenes > 30s)
- Minimum chunk: 0.5s (discard — not processable)
- Maximum chunk: 30s (split longer scenes at silence)

**Tradeoffs:**
- Context lost at chunk boundaries (word that spans a cut)
- Overlap handling needed: extend each chunk by 0.5s on each side,
  trim overlap in final assembly
- Assembly step required to concatenate chunks

---

### ADR-003: IndicWhisper over OpenAI Whisper for Transcription

**Decision:** Use AI4Bharat's IndicWhisper (fine-tuned Whisper) as primary ASR.
Fallback to OpenAI Whisper large-v3 for edge cases.

**Rationale:**
- IndicWhisper fine-tuned on 10,700 hours of Indian language audio
- Achieves lowest WER in 39/59 benchmarks on Vistaar benchmark
- Average 4.1 WER reduction vs base Whisper on Indian languages
- Free to self-host, no per-call API cost

**Known limitation:**
- IndicWhisper covers 12 languages. 10 remaining scheduled languages
  fall back to Whisper large-v3.
- Code-mixed Hinglish: IndicWhisper degrades. Whisper large-v3 handles
  better. Language ID step switches model per segment.

**Rejected:** Sarvam AI ASR — better for some dialects but API-only,
no self-hosting, cost per call doesn't scale.

---

### ADR-004: IndicTrans2 over Google Translate / DeepL for Translation

**Decision:** AI4Bharat's IndicTrans2 as primary translation engine.
LLM rewrite pass (Llama 3.1 8B) for constraint satisfaction.

**Rationale:**
- IndicTrans2 trained specifically on all 22 scheduled Indian languages
- Handles SOV word order for Dravidian languages correctly
- Self-hostable — zero per-call cost at scale
- Fine-tuned on colloquial Indian language pairs, not just formal text

**The two-step approach:**
Step 1: IndicTrans2 → semantically correct translation, ignores timing
Step 2: Llama 3.1 8B fine-tuned → rewrite under phoneme timing constraints

Why two steps and not one LLM call?
- IndicTrans2 is far better at translation quality than LLM direct translation
- LLM is better at constrained rewriting than translation from scratch
- Separation of concerns: one model does what it's good at

**Rejected:** GPT-4o for translation — quality is similar but costs $0.02/minute
vs $0 for self-hosted IndicTrans2. Not viable at scale.

---

### ADR-005: XTTS-v2 for Voice Cloning with Disclosed Limitations

**Decision:** XTTS-v2 (Coqui) for cross-lingual voice cloning.
Explicitly disclosed: Telugu/Tamil/Kannada are not natively supported.
Output labeled as "voice-inspired" not "exact clone" for these languages.

**Rationale:**
- XTTS-v2 clones from 6 seconds of audio — lowest data requirement available
- Sub-250ms inference latency for synthesis
- Cross-lingual voice transfer works well for Hindi (natively supported)
- Open weights — self-hostable

**The Hindi approximation:**
For Telugu/Tamil output with Hindi reference voice:
- XTTS-v2 generates Telugu text in a voice that carries Hindi phoneme
  characteristics of the reference speaker
- Result: recognizable voice identity (~60-70% similarity) with target language
- Better than generic TTS (0% similarity)
- Disclosed clearly to users

**Critical note:** Coqui has shut down. XTTS-v2 weights are frozen.
No future updates. We must plan migration:
- Sarvam AI TTS (Indian startup, API-based) — better Indian language support
- Fine-tuned XTTS-v2 on IndicVoices-R — our own improved version
- ParlerTTS with Indian voice prompting — emerging alternative

**Fine-tuning plan:**
- Dataset: IndicVoices-R (NeurIPS 2025) — 1704 hours, 10496 speakers, 22 languages
- Fine-tune XTTS-v2 decoder on Telugu/Tamil/Kannada subsets
- Expected: improve voice clone quality for these languages to 75-80% similarity
- Compute: ~48 hours on A100, ~$50 on Vast.ai

---

### ADR-006: MuseTalk for Speed Tier, LatentSync for Quality Tier

**Decision:** Two-tier lip reanimation. User selects at job submission.

Speed tier (MuseTalk 1.5):
- Single-step latent space inpainting
- 30fps+ on V100
- 256×256 face region
- Turnaround: ~2× video duration

Quality tier (LatentSync 1.6):
- Multi-step latent diffusion
- TREPA for temporal consistency
- Higher fidelity output
- Turnaround: ~10× video duration

**Rationale:**
- Most EdTech/creator use cases don't need cinema quality
- Speed tier dramatically reduces cost and turnaround
- Quality tier available for premium customers who need better output
- Two tiers = two price points = larger addressable market

**Why not Wav2Lip:**
- Renders mouth at 96×96 pixels — visibly blurry on HD footage
- Not suitable for production use in 2026
- Kept as emergency fallback only (if both primary models fail)

**Indian face fine-tuning:**
Both models trained primarily on Western faces (LRS2/LRS3 = BBC English).
Indian skin tones, facial structures — models produce more artifacts.
Fine-tuning plan:
- Collect 50-volunteer Indian face dataset (500 minutes)
- Fine-tune visual quality discriminator on Indian faces
- Keep sync discriminator frozen (already understands sync universally)

---

### ADR-007: Selective Reanimation — Skip What Can't Be Done Well

**Decision:** Run scene classification BEFORE reanimation.
Only reanimate scenes where output quality will be high.
Skip all others. Never hide failures — flag them.

**Classification thresholds:**
```
FRONTAL_CLEAR:   yaw < ±20°, occlusion < 10%, confidence > 0.9  → REANIMATE
PARTIAL:         yaw < ±40°, confidence > 0.7                   → REANIMATE + FLAG
PROFILE:         yaw > ±40°                                      → SKIP
OCCLUDED:        mouth occlusion > 40%                           → SKIP
MULTI_FACE:      > 1 face, active speaker unclear                → SKIP + FLAG
NO_FACE:         no face detected (B-roll, slides, animations)   → SKIP (no issue)
LOW_RES:         face region < 64×64px                           → SKIP
```

**What SKIP means:**
Original video frames used. Dubbed audio plays. Lip sync is
handled by Path A (script timing + audio alignment) not visually.
This is still better than raw dubbing — audio timing is improved.

**Rationale:**
A bad reanimation is worse than no reanimation.
Kanguva failed because they reanimated everything including scenes where
current technology can't produce good output.
Selective application = better average quality across the whole video.

---

### ADR-008: Speed-Invariant Playback via Animation Manifest (Phase 3)

**Decision:** Decouple animation from pixels. Store as manifest. Render at playback time.

**Why Option A (accept it) was rejected:**
Indian students watch at 1.5x-2x. This is not an edge case.
Accepting speed artifacts means the product fails for the primary use case.

**Why Option B (multiple pre-rendered versions) was rejected:**
YouTube has 8 speed options (0.25x to 2x).
Users change speed mid-video.
Pre-rendering all combinations = 8× storage + doesn't handle mid-video changes.

**The manifest approach:**
```json
{
  "version": "1.0",
  "base_video": "s3://voxbridge/jobs/123/original.mp4",
  "dubbed_audio": "s3://voxbridge/jobs/123/dubbed_te.aac",
  "fps": 24,
  "speaker_meshes": {
    "S1": "s3://voxbridge/jobs/123/mesh_S1.bin"
  },
  "segments": [
    {
      "frame": 142,
      "timestamp_ms": 5916,
      "speaker_id": "S1",
      "viseme": "open_wide",
      "intensity": 0.87,
      "duration_frames": 4,
      "blend_weights": {
        "jaw_open": 0.70,
        "lip_corner_puller": 0.30,
        "upper_lip_raiser": 0.40,
        "lip_stretcher": 0.20
      }
    }
  ]
}
```

**Player runtime:**
```
At any playback speed S:
  manifest_timestamp = real_timestamp × S
  Find nearest viseme entry in manifest
  Interpolate blend_weights between adjacent entries
  Apply 3DMM deformation to face mesh
  Composite deformed lip region onto base frame
  Output: frame with correct lip movement for current speed
```

**Research contribution:**
First published application of playback-adaptive 3DMM blendshape rendering
in an AI dubbing pipeline. Submit to ACM MM 2026.

---

### ADR-009: Demucs for Audio Source Separation Before Processing

**Decision:** Run Demucs (Meta) before transcription to separate speech from music/SFX.

**Rationale:**
- Background music confuses Whisper — WER increases significantly
- TTS output loses the background atmosphere if we replace full audio track
- Solution: separate speech, translate + synthesize speech, remix with
  original background audio (music, SFX, ambient sound)
- Output sounds natural — not the sterile "dubbed with silence" effect

**Pipeline with Demucs:**
```
Original audio
    ↓ Demucs
Speech track   +   Background track (music + SFX)
    ↓                       ↓
Transcribe               Preserve unchanged
Translate
Synthesize
    ↓
Dubbed speech track
    ↓ FFmpeg mix
Final audio (dubbed speech + original background)
```

**Tradeoff:** Adds ~2× audio processing time. Worth it for output quality.

---

### ADR-010: PostgreSQL + pgvector over NoSQL

**Decision:** PostgreSQL as primary database. pgvector extension for embeddings.

**Rationale:**
- Job metadata, chunk data, QC results are relational — fits RDBMS well
- pgvector allows storing voice clone embeddings for similarity search
  (find if a voice has already been cloned before — deduplication)
- ACID guarantees important for job status tracking
- One database instead of two (no separate vector DB like Pinecone)

**Schema design principle:**
JSONB for flexible data (QC scores, scene classification results, blend_weights).
Strict columns for data that's always present and queried (status, timestamps).

---

## 5. Open Questions

**OQ-001: MFA acoustic models for Indian languages**
Montreal Forced Aligner has models for Hindi. Telugu, Tamil, Kannada — unclear.
Need to verify before Phase 2. Fallback: Whisper-based alignment (less accurate).
Owner: Manoj. Deadline: Before Phase 2 start.

**OQ-002: XTTS-v2 Telugu quality — is it actually acceptable?**
Claimed: 60-70% voice similarity. Actual: untested on real Telugu speakers.
Need: user study with 10 Telugu speakers rating cloned voice quality.
If < 50% acceptable rating → switch to Sarvam AI TTS for Telugu.
Owner: Manoj. Deadline: End of Week 3.

**OQ-003: IndicTrans2 on code-mixed Hinglish input**
Teachers frequently switch between Hindi and English mid-sentence.
IndicTrans2 trained on formal language pairs — code-mixed performance unknown.
Need: test on 20 code-mixed sentences, measure translation accuracy.
Fallback: detect code-mixed segments via IndicLID, use Whisper + GPT translation.

**OQ-004: MuseTalk license for commercial use**
MuseTalk released by Tencent under Apache 2.0. Verify this allows commercial use.
LatentSync by ByteDance — license unclear. Must verify before Phase 2.
If commercial use blocked → VideoReTalking as fallback (also Apache 2.0).

**OQ-005: DPDP Act compliance for voice biometric data**
India's Digital Personal Data Protection Act (DPDP) 2023.
Voice data may qualify as biometric personal data.
Need: legal opinion on consent requirements, storage obligations, user rights.
Cannot launch paid product without this cleared.

**OQ-006: PySceneDetect accuracy on Indian content**
Designed for Hollywood-style cuts. Bollywood/South Indian cinema uses
different editing patterns (song sequences, rapid cuts, dissolves).
Need: test on 10 Indian videos, measure false positive/negative scene detection rate.

**OQ-007: Speed playback patent scope**
The animation manifest + playback-adaptive rendering approach.
Is this novel enough for a patent? Is there prior art in video games?
(Video game facial animation uses similar blendshape approach but not for dubbing.)
Need: prior art search before filing provisional application.

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| XTTS-v2 quality unacceptable for non-Hindi Indian languages | High | High | Sarvam AI TTS fallback; IndicVoices-R fine-tune |
| MuseTalk/LatentSync license blocks commercial use | Medium | High | VideoReTalking fallback; verify before Phase 2 |
| MFA acoustic models missing for South Indian languages | Medium | Medium | Whisper-based alignment fallback |
| GPU compute costs exceed revenue at scale | Medium | High | Spot instances; model quantization; self-hosted inference |
| NeuralGarage launches creator tier | Medium | Medium | Speed-invariant playback moat; Indian educator dataset |
| DPDP Act compliance blocks voice clone feature | Low | High | Legal review; consent framework; data minimization |
| IndicTrans2 quality poor on code-mixed content | High | Medium | IndicLID detection; GPT fallback for code-mixed segments |
| Indian educator dataset collection harder than expected | Medium | Medium | Partner with IIIT Hyderabad; use AI4Bharat IndicVoices-R subset |
| Kanguva-type user rejection of output quality | Medium | High | Quality floor threshold; selective reanimation; honest disclosure |
| PySceneDetect fails on Indian video editing styles | Medium | Low | Tune threshold; manual override via API |

---

## 7. Dependency Map

```
Pipeline dependencies (strict order):

Ingestion
  ├── requires: FFmpeg, file validation
  └── outputs: audio.wav, video frames, metadata.json

Audio Separation (Demucs)
  ├── requires: audio.wav from Ingestion
  └── outputs: speech.wav, background.wav

Scene Detection (PySceneDetect)
  ├── requires: video from Ingestion
  └── outputs: chunk_manifest.json (list of scene boundaries)

Transcription (IndicWhisper)
  ├── requires: speech.wav + chunk_manifest.json
  └── outputs: transcript.json (word-level timestamps per chunk)

Translation (IndicTrans2 + LLM rewrite)
  ├── requires: transcript.json + phoneme timing (from Transcription)
  └── outputs: translated_script.json per target language

Voice Synthesis (XTTS-v2 / IndicTTS)
  ├── requires: translated_script.json + voice_clone_reference (optional)
  └── outputs: dubbed_audio_chunks/ per language

Force Alignment (MFA)
  ├── requires: dubbed_audio_chunks/ + translated_script.json
  └── outputs: phoneme_timestamps.json per chunk

Scene Classification (MediaPipe + 3DDFA-V2)
  ├── requires: video frames from Ingestion
  └── outputs: scene_decisions.json (REANIMATE/SKIP per scene)

Lip Reanimation (MuseTalk / LatentSync)
  ├── requires: scene_decisions.json + dubbed_audio_chunks/ + video frames
  ├── SKIPS scenes classified as PROFILE/OCCLUDED/NO_FACE
  └── outputs: reanimated_frames/ per REANIMATE scene

Temporal Smoothing (OpenCV)
  ├── requires: reanimated_frames/
  └── outputs: smoothed_frames/

Assembly (FFmpeg)
  ├── requires: smoothed_frames/ + original frames (for SKIP scenes)
  │             + dubbed_audio_chunks/ + background.wav
  └── outputs: final_output_{lang}.mp4

QC Scoring
  ├── requires: final_output_{lang}.mp4 + scene_decisions.json
  └── outputs: qc_report.json + flagged_scenes list

Human Review Queue
  ├── requires: qc_report.json + flagged_scenes
  └── outputs: reviewer_decisions.json

Final Delivery
  ├── requires: reviewer_decisions.json
  └── outputs: approved segments rendered into final video
               (rejected segments reverted to original + dubbed audio)
```

---

## 8. Failure Modes

**Transcription fails on a chunk:**
- Retry 3 times with different decoding parameters
- If still fails: mark chunk as SKIP, use silence in dubbed audio for that segment
- Flag in QC report

**Translation produces empty or garbage output:**
- Validate output: length check (must be 50-200% of source length)
- Language detection on output (must match requested target)
- If validation fails: retry with different prompt
- If 3 retries fail: flag chunk for human translation

**TTS duration mismatch > 30% from original:**
- First: time-stretch up to 15% (perceptually transparent)
- If still >15% gap: constrained LLM rewrite with tighter duration constraint
- If 3 attempts fail: flag segment for human re-recording
- Never output silence padding — always flag instead

**Reanimation produces PSNR < 35dB on non-lip regions:**
- Compositing error detected
- Auto-revert that frame to original
- If > 30% frames in scene revert: mark entire scene SKIP
- This is an automatic quality guard

**Job queue worker crash mid-processing:**
- Celery with task state stored in Redis
- On worker restart: resume from last successful chunk
- No data loss (chunks processed atomically, result written before next starts)

**GPU OOM (Out of Memory) on large video:**
- MuseTalk processes one chunk at a time, not full video
- If chunk too large: auto-split at midpoint, retry
- If persistent OOM: fall back to CPU processing (slower, always works)

**Storage write failure:**
- All writes go to S3-compatible (Cloudflare R2) with multipart upload
- Failed chunks: exponential backoff retry (3 attempts)
- Partial uploads: R2 abort-and-retry
- If all retries fail: job marked FAILED, user notified, no charge

**Voice clone reference audio too short (< 6 seconds):**
- Validate at upload time before job submission
- Return 400 error with explicit message: minimum 6 seconds required
- UI prevents submission with clear feedback

**Entire pipeline failure:**
- Dead letter queue for failed jobs
- Automatic notification to user
- No charge for failed jobs
- Support ticket auto-created for investigation
