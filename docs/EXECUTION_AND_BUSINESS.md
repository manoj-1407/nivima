# Nivima — Execution Timeline, Dataset, Fine-Tuning, Business

---

## 1. Complete Execution Timeline

### Month 1 — Foundation

**Week 1: Environment + Models + First Transcription**
```
Day 1:
  - Conda env setup
  - Install all Phase 1 dependencies
  - Run download_models.sh
  - Verify: faster-whisper transcribes a Hindi YouTube video correctly

Day 2-3:
  - Build src/ingestion/validator.py
  - Build src/ingestion/extractor.py
  - Unit tests: test_validator.py (all 6 cases passing)
  - Verify: extract_audio produces 16kHz mono WAV

Day 4-5:
  - Build src/audio/separator.py (Demucs integration)
  - Test Demucs on video with background music
  - Verify: speech track clean, background preserved separately
  - Known issue: Demucs slow on CPU (~5x realtime). Accept for now.

Day 6-7:
  - Build src/transcription/asr.py
  - Build src/transcription/language_id.py
  - Unit tests: test_asr.py (Hindi transcription, word timestamps)
  - Milestone: Hindi YouTube video → clean transcript with timestamps
```

**Week 2: Translation + TTS**
```
Day 8-9:
  - Build src/transcription/chunker.py (PySceneDetect + VAD)
  - Test scene detection on 3 Indian videos
  - Verify: chunk boundaries at actual scene cuts

Day 10-11:
  - Build src/translation/translator.py (IndicTrans2)
  - Build src/translation/validator.py
  - Unit tests: test_translation.py
  - Verify: Hindi → Telugu semantically correct on 20 test sentences

Day 12-13:
  - Build src/translation/rewriter.py (Llama 3.1 8B via Ollama)
  - Ollama setup: ollama pull llama3.1:8b
  - Test constrained rewrite: translation + timing constraints

Day 14:
  - Build src/tts/synthesizer.py
  - Test generic Telugu TTS (IndicTTS)
  - Test XTTS-v2 voice clone (Hindi reference → Telugu output)
  - Benchmark: measure voice similarity informally with Telugu speaker
```

**Week 3: Alignment + Assembly**
```
Day 15-16:
  - Setup Montreal Forced Aligner (scripts/setup_mfa.sh)
  - Build src/alignment/force_aligner.py
  - Build src/alignment/audio_adjuster.py
  - Test: MFA on Hindi audio, verify phoneme timestamps

Day 17-18:
  - Build src/audio/mixer.py
  - Build full audio assembly in extractor.py
  - First end-to-end test: Hindi video → Telugu dubbed output
  - Evaluate: is audio synced with video events?

Day 19-20:
  - Fix timing issues found in e2e test
  - Handle duration mismatch cases
  - Verify background music comes through correctly
```

**Week 4: API + Queue**
```
Day 21-22:
  - Build src/api/main.py + routes/jobs.py
  - Build src/worker/celery_app.py
  - Build src/worker/tasks/pipeline.py
  - Docker-compose up: postgres + redis + api + worker

Day 23-24:
  - Database migrations (alembic)
  - API integration tests: test_api.py
  - Test job submission → async processing → status polling

Day 25-26:
  - WebSocket progress broadcasting
  - Basic web UI: file upload → job status → download link
  - End-to-end: browser upload → dubbed video download

Day 27-28:
  - 3 real video tests (PW, Unacademy, YouTube creator)
  - Document all issues found
  - Fix critical issues
  - Phase 1 demo ready
```

---

### Month 2 — Stabilize + Dataset Collection

**Week 5-6: Fix Phase 1 Issues**
```
- Address all issues found in week 4 real video tests
- Improve translation quality on code-mixed content
- Tune Demucs separation for Indian video audio profiles
- Handle edge cases: silent chunks, very short segments, all-music segments
- Load testing: can the pipeline handle 5 concurrent jobs?
- Set up monitoring: Prometheus + Grafana for pipeline metrics
```

**Week 7-8: Indian Face Dataset Collection**
```
Target: 50 volunteers × 10 minutes = 500 minutes of Indian talking face video

Recording setup:
  - Standard smartphone (1080p)
  - Ring light or natural daylight
  - Plain light-colored background
  - 60cm from camera (face fills ~30% of frame)

Volunteer criteria:
  - Diverse: skin tones 1-6 (Fitzpatrick scale), ages 18-60
  - Gender diversity: 25F, 25M minimum
  - Facial hair diversity: clean-shaven, stubble, beard, mustache
  - Glasses diversity: without, with (affects occlusion score)
  - Languages: 15 Hindi, 10 Telugu, 10 Tamil, 8 Kannada, 7 other

Recording script:
  - Phoneme-balanced sentences (see research/phoneme_coverage_analysis.py)
  - Cover all viseme types including Indian retroflex sounds
  - Natural conversational speed
  - Repeat each sentence 3 times

Annotation pipeline:
  - Auto-annotate with MediaPipe FaceMesh (landmarks)
  - Auto-align with MFA (phoneme timestamps)
  - Manual review: discard clips with >30% landmark tracking failures

Where to find volunteers:
  - GCET campus: 50 volunteers achievable in 2 weeks
  - Offer: ₹200 per session (10 minutes)
  - Total cost: ₹10,000

Storage: ~50GB raw video → compress to ~15GB for training
```

---

### Month 3 — Phase 1 Polish + Start Phase 2

**Week 9-10:**
```
- Phase 1 production-ready
- Handle video lengths up to 3 hours reliably
- Cost optimization: model quantization (int8) where possible
- First 5 external beta users (educators you know or reach via LinkedIn)
- Collect real feedback on translation quality, voice clone quality
```

**Week 11-12:**
```
- Start Phase 2: scene detection integration
- Build src/scene/detector.py
- Build src/scene/classifier.py (without 3DDFA-V2 yet — MediaPipe only)
- Test scene classification on 10 Indian videos
- Measure: what % of frames are FRONTAL_CLEAR in typical EdTech content?
  (Expected: 60-70% — educators usually face camera)
```

---

### Month 4 — Phase 2 Core

**Week 13-14: MuseTalk Integration**
```
- Clone MuseTalk repo, verify weights downloadable
- Verify license: Apache 2.0 — commercial use OK
- Build src/reanimation/musetalk.py
- Test: reanimate 10 FRONTAL_CLEAR scenes from dataset
- Evaluate: CSIM > 0.85? Temporal flickering visible?
- Fine-tune visual quality discriminator on Indian face dataset
  (Compute: ~24hr on Colab A100 or Vast.ai — ~$25)
```

**Week 15-16: Compositor + QC**
```
- Build src/reanimation/compositor.py
- Build src/reanimation/smoother.py
- Build src/reanimation/quality_guard.py
- Build src/qc/scorer.py
- Test PSNR guard: does it catch bad composites?
- Build human review queue dashboard
- Integration test: full Phase 2 pipeline on 3 videos
```

---

### Month 5 — Phase 2 Polish + Fine-Tuning

**Week 17-18: MuseTalk Fine-Tuning**
```
Fine-tuning on Indian face dataset:

Setup on Vast.ai A100:
  git clone https://github.com/TMElyralab/MuseTalk
  
  # Prepare dataset in MuseTalk format
  python scripts/prepare_musetalk_dataset.py \
    --input_dir data/indian_faces/ \
    --output_dir data/musetalk_format/
  
  # Fine-tune visual quality discriminator only
  # Keep sync discriminator frozen — it's already universal
  python train.py \
    --config configs/finetune_indian.yaml \
    --pretrained_weights checkpoints/musetalk_v15.pt \
    --data_dir data/musetalk_format/ \
    --freeze_sync_disc True \
    --epochs 20 \
    --batch_size 8 \
    --lr 1e-5

Training time: ~24 hours on A100
Cost on Vast.ai: ~$25

Evaluation:
  - CSIM on Indian face test set: before vs after
  - Visual flicker metric: before vs after
  - Target: CSIM improves by >0.05 on Indian faces
```

**Week 19-20: XTTS-v2 Fine-Tuning for Telugu/Tamil**
```
Fine-tuning on IndicVoices-R subset:

Dataset preparation:
  - Download IndicVoices-R from AI4Bharat (HuggingFace)
  - Extract Telugu subset: ~200 hours, ~1200 speakers
  - Format: (audio, text, speaker_id) triplets
  - Split: 90% train, 5% val, 5% test

Fine-tuning XTTS-v2 for Telugu:
  from TTS.tts.configs.xtts_config import XttsConfig
  from TTS.tts.models.xtts import Xtts
  
  # Load pretrained XTTS-v2
  config = XttsConfig()
  config.load_json("xtts_config.json")
  model = Xtts.init_from_config(config)
  model.load_checkpoint(config, checkpoint_dir="xtts_v2/")
  
  # Fine-tune decoder on Telugu data
  # Freeze encoder, fine-tune decoder + language embedding
  trainer = Trainer(
      args=TrainerArgs(epochs=30, batch_size=4, lr=1e-5),
      config=config,
      train_samples=telugu_train,
      eval_samples=telugu_val
  )
  trainer.fit()

Training time: ~36 hours on A100
Cost: ~$40 on Vast.ai
Expected improvement: voice clone similarity 65% → 75% for Telugu
```

---

### Month 6 — Phase 2 Complete + Phase 3 Start

**Week 21-22:**
```
- Phase 2 complete and stable
- LatentSync integration (quality tier)
- 48fps pre-render for speed playback (interim solution)
- Full pipeline test: upload → dubbing → lip sync → QC → download
- Second beta cohort: 20 creators, 3 languages
- Measure: regional view increase after dubbing (the key business metric)
```

**Week 23-24: Phase 3 Research Begin**
```
- Indian phoneme viseme mapping for Dravidian languages
  (Telugu, Tamil, Kannada retroflex sounds not in standard CMU phoneme set)
- Build blendshape_library.py
- Prior art search for patent
- Draft paper outline
- Build manifest_generator.py prototype
```

---

### Month 7-12 — Phase 3 + Revenue

```
Month 7: Animation manifest format finalized + mesh_builder.py
Month 8: NivimaPlayer SDK (web) — basic working version
Month 9: Speed-invariant playback working at 0.5x, 1x, 1.5x, 2x
Month 10: User study — 50 Indian students, evaluate across speeds
Month 11: Paper draft, provisional patent filing
Month 12: Paid product launch — creator tier + professional tier
```

---

## 2. Dataset Plan — Complete

### Phase 1 Datasets (All Publicly Available)

| Dataset | Source | Size | Download |
|---|---|---|---|
| AI4Bharat IndicVoices-R | HuggingFace | 1704hr, 22 langs | ai4bharat/IndicVoices-R |
| AI4Bharat Vistaar | HuggingFace | 10700hr benchmarks | ai4bharat/vistaar |
| VoxCeleb2 | Oxford VGG | 1M+ utterances | voxceleb.robots.ox.ac.uk |
| LRS2 | Oxford VGG | 150k utterances | Requires registration |
| MUAVIC | Meta AI | 9 languages | github.com/facebookresearch/muavic |
| Mozilla Common Voice | Mozilla | Indian language subset | commonvoice.mozilla.org |

### Phase 2 Dataset — Indian Face (Build It)

**Collection script:**
```python
# research/phoneme_coverage_analysis.py
# Generates sentences that cover all viseme types including Indian retroflex

VISEME_COVERAGE_SENTENCES = {
    'bilabial': [
        "amma bata paata maata",  # Telugu — heavy bilabials
        "Mera naam Manoj hai",    # Hindi
    ],
    'retroflex': [
        "Tamaatar baRaa meetaa hai",  # Hindi retroflexes
        "Naadu naatakam",              # Telugu
    ],
    'open_wide': [
        "Aakasha vaata",       # Telugu — open vowels
        "Aaj kaafi acha tha",  # Hindi
    ],
    # ... all viseme types covered
}
```

**Quality filtering pipeline:**
```python
def filter_volunteer_recording(video_path: str) -> bool:
    # Discard if:
    # 1. MediaPipe fails to detect face in >30% of frames
    # 2. Head pose > 30 degrees in >50% of frames
    # 3. Audio SNR < 20dB
    # 4. Speaker blinks for >15% of duration (eye detection)
    return True  # passes all filters
```

### Phase 3 Dataset — Dubbed Ground Truth Pairs (The Moat)

**Target:** 100 hours of (original Hindi video, dubbed Telugu video) pairs

**Sources:**
1. Partner with 5 YouTube educators — give them free dubbing, get their old
   manual dubbed content as training data. Mutual benefit.
2. Regional OTT content with existing dubs — licensed for training only
3. Our own pipeline outputs corrected by human reviewers (feedback flywheel)

**Why this matters:**
This dataset doesn't exist publicly anywhere.
Training a model on real dubbing ground truth pairs is fundamentally
better than training on synthetic pairs.
Anyone trying to replicate your model quality must collect this dataset too.
That takes 2+ years. That's the moat.

---

## 3. Fine-Tuning Guide — All Models

### MuseTalk Visual Quality Discriminator

**When:** Phase 2, after Indian face dataset collected
**Why:** Base model trained on LRS2 (BBC) — Western faces, studio lighting
**What changes:** Visual quality discriminator only. Sync discriminator frozen.

```yaml
# configs/finetune_indian.yaml
model:
  name: MuseTalk
  pretrained: checkpoints/musetalk_v15.pt
  
training:
  freeze_sync_discriminator: true
  freeze_generator_encoder: false
  freeze_generator_decoder: false
  epochs: 20
  batch_size: 8
  lr: 0.00001
  lr_scheduler: cosine
  warmup_steps: 500
  
data:
  train_dir: data/indian_faces/train/
  val_dir: data/indian_faces/val/
  frame_size: 256
  fps: 25
  
evaluation:
  metrics: [csim, temporal_variance, psnr_non_lip]
  eval_every_n_epochs: 2
  
hardware:
  gpu: a100
  mixed_precision: true  # fp16 training
  gradient_checkpointing: true  # saves VRAM
```

**Expected outcomes:**
- CSIM on Indian faces: 0.78 → 0.86
- Temporal flickering: measurable reduction
- Training cost: ~$25 on Vast.ai

---

### XTTS-v2 Telugu/Tamil Decoder Fine-Tuning

**When:** Phase 2, month 5
**Why:** Telugu/Tamil not natively supported — use Hindi approximation currently
**What changes:** Decoder + language embedding layers only

**Data preparation:**
```python
# Format IndicVoices-R for XTTS-v2 training
# XTTS-v2 needs: (audio_path, text, language, speaker_id)

import pandas as pd
from datasets import load_dataset

dataset = load_dataset("ai4bharat/IndicVoices-R", "te")  # Telugu

formatted = []
for item in dataset['train']:
    formatted.append({
        'audio_path': item['audio']['path'],
        'text': item['sentence'],
        'language': 'te',
        'speaker_id': item['client_id']
    })

# Save in XTTS-v2 training format
pd.DataFrame(formatted).to_csv('data/xtts_telugu_train.csv', index=False)
```

**Training command:**
```bash
python TTS/bin/train_tts.py \
  --config_path configs/xtts_telugu_finetune.json \
  --restore_path checkpoints/xtts_v2.pth
```

---

### Llama 3.1 8B — Constrained Translation Rewriter

**When:** Phase 1, week 2
**What:** Fine-tune on (source_segment + timing_constraints → dubbed_script) pairs
**Why fine-tune vs prompt:** Consistency, cost, speed, no API dependency

**Training data format:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a dubbing scriptwriter. Rewrite translations to fit phoneme timing constraints."
    },
    {
      "role": "user", 
      "content": "Source (Hindi): नमस्कार, आज हम भौतिकी पढ़ेंगे\nTranslation (Telugu): నమస్కారం, ఈరోజు మనం భౌతికశాస్త్రం చదువుతాం\nDuration constraint: 2.4 seconds\nAt 0.8s: mouth should produce bilabial sound\nRewrite the Telugu to fit:"
    },
    {
      "role": "assistant",
      "content": "నమస్కారం, భౌతికశాస్త్రం మొదలుపెట్టాం"
    }
  ]
}
```

**Generate training data:**
- Take 1000 (Hindi, Telugu) sentence pairs from IndicTrans2 output
- Add phoneme timing constraints from MFA alignment of Hindi audio
- Use GPT-4o to generate "ideal" constrained rewrites (once only — for dataset creation)
- Fine-tune Llama 3.1 8B on these 1000 pairs
- Cost to generate data: ~$20 one-time GPT-4o API cost
- Fine-tuning: Ollama or HuggingFace PEFT (LoRA) on Colab A100

**LoRA config:**
```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

---

## 4. Business Model — Complete

### Revenue Tiers

| Tier | Price | Minutes | Languages | Voice Clone | Lip Sync |
|---|---|---|---|---|---|
| Free | ₹0 | 10/month | 2 | No | No |
| Creator | ₹999/month | 120/month | 4 | Yes (1 voice) | Speed tier |
| Professional | ₹3999/month | 600/month | 8 | Yes (3 voices) | Speed + Quality |
| Enterprise | Custom | Unlimited | 22 | Unlimited | Quality tier + SLA |
| API | ₹4/minute | Pay-per-use | All | Per voice | Both tiers |

**Overage pricing:**
- Creator: ₹8/minute over 120
- Professional: ₹6/minute over 600

### Unit Economics — Detailed

**Cost per minute processed (Phase 1 — self-hosted models):**

| Component | Model | Compute | Cost/min |
|---|---|---|---|
| Transcription | IndicWhisper on A100 | 0.1× realtime | ₹0.15 |
| Demucs separation | htdemucs on A100 | 0.5× realtime | ₹0.40 |
| Translation | IndicTrans2 on A100 | 0.05× realtime | ₹0.08 |
| LLM rewrite | Llama 3.1 8B on A100 | 0.1× realtime | ₹0.15 |
| TTS synthesis | IndicTTS/XTTS on A100 | 0.3× realtime | ₹0.25 |
| Force alignment | MFA on CPU | 0.2× realtime | ₹0.05 |
| Assembly | FFmpeg on CPU | 0.1× realtime | ₹0.02 |
| Storage (R2) | Cloudflare R2 | per GB | ₹0.10 |
| **Total Phase 1** | | | **~₹1.20/min** |

**Phase 2 adds lip sync:**
| MuseTalk reanimation | MuseTalk on A100 | 2× realtime | ₹1.50 |
| QC scoring | SyncNet on A100 | 0.5× realtime | ₹0.40 |
| **Total Phase 2** | | | **~₹3.10/min** |

**Revenue vs cost:**
| Tier | Revenue/min | Cost/min (P2) | Gross Margin |
|---|---|---|---|
| Free | ₹0 | ₹3.10 | -∞ (acquisition cost) |
| Creator | ₹8.33 (999/120) | ₹3.10 | 63% |
| Professional | ₹6.67 (3999/600) | ₹3.10 | 54% |
| API | ₹4.00 | ₹3.10 | 23% |

**Free tier is a loss leader.** Cap at 10 minutes strictly. Cost: ₹31/user/month maximum.

**Spot instance optimization:**
Vast.ai A100 at $0.8/hr vs on-demand at $3.5/hr.
Process batch jobs overnight on spot: 4× cost reduction.
Cost/min on spot: ~₹0.80 (Phase 2).
Creator tier margin jumps to 90%.

### CAC vs LTV

**Customer Acquisition Cost (CAC):**
- Phase 1: ₹0 — give free processing to first 10 videos of target creators
- Phase 2: social media + creator community posts
- Phase 3: content marketing (write about the speed-invariant research)
- Target CAC: < ₹500

**Lifetime Value (LTV):**
- Creator tier: ₹999/month × average 18-month retention = ₹17,982
- Professional: ₹3999/month × 24-month = ₹95,976
- LTV:CAC ratio target: > 30:1

**Monthly churn target:** < 5% (voice clone lock-in helps retention significantly)

### Go-To-Market — Phase-Wise

**Phase 1 (Month 1-3): Zero budget, proof of concept**

Target: 10 Hindi YouTube educators, 100k-500k subscribers, education category.

Approach:
- DM them directly. Show a dubbed version of their own video.
- "I dubbed your last video into Telugu — want to see it?" converts.
- Give it free. Get feedback. Get testimonial.
- Ask: did your Telugu viewership go up?

Channels:
- YouTube educator communities (Discord, Telegram groups)
- GCET network — professors who create content
- LinkedIn outreach to EdTech founders

**Phase 2 (Month 3-6): First revenue**

- Convert 3-5 educators from beta to Creator tier (₹999/month)
- Partner with one regional EdTech company for API access
- Apply to: Y Combinator, Antler India, Surge (Sequoia India)
- Apply to: AWS Activate (free GPU credits — up to $100,000)
  Google for Startups (GCP credits)
  Microsoft for Startups (Azure credits + OpenAI credits)

**Phase 3 (Month 6-12): Scale**

- Creator tier: target 100 paying creators by month 12
- Revenue at 100 creators × ₹999 = ₹99,900 MRR (~₹1.2 crore ARR)
- Professional tier: 10 companies × ₹3999 = ₹39,990 MRR
- Combined: ~₹1.4 lakh MRR = ~₹1.7 crore ARR by month 12
- This is seed raise territory. Raise ₹2-3 crore seed at this point.

### Moat Layers (Revisited — Honest)

**What anyone can copy in 6 months:**
- Basic audio dubbing pipeline (IndicTrans2 + IndicTTS) — public models
- API wrapper around it — basic engineering

**What takes 18 months to copy:**
- Indian face dataset (500 minutes, annotated)
- MuseTalk fine-tuned on Indian faces
- XTTS-v2 fine-tuned on IndicVoices-R for Telugu/Tamil

**What takes 3+ years to copy:**
- Dubbed ground truth pairs dataset (creator partnerships)
- Speed-invariant playback SDK (research + engineering)
- Creator network lock-in (voice clones live on your platform)

**What you can never copy:**
- First-mover advantage in Indian educator community
- The research paper and patent on speed-invariant playback
- Trust built with creators who've seen their regional views grow

### Legal + Compliance

**Voice cloning consent:**
```
Mandatory consent flow before voice clone creation:

"By proceeding, you confirm that:
1. You are the owner of this voice, OR
2. You have explicit written permission from the voice owner
3. You understand that creating unauthorized voice clones
   may violate applicable laws
4. You consent to Nivima storing this voice embedding
   per our Privacy Policy and DPDP Act requirements"

Stored in DB: user_id, consent_timestamp, consent_version
Never delete consent records — legal protection
```

**DPDP Act 2023 compliance:**
- Voice data = sensitive personal data under DPDP Act
- Requires explicit consent: ✓ (consent flow above)
- Data localization: store all Indian user voice data on Indian servers
- Right to erasure: user can delete voice clone → remove from storage + DB
- Data processing agreement required for enterprise customers

**Copyright of output:**
- User retains copyright of all output videos
- Nivima takes no rights to user content
- We store processed videos temporarily (7 days default, 30 days paid)
- After expiry: permanently deleted, not retrievable

**Open questions requiring legal opinion:**
- Does processing a third-party video (e.g., PW lecture) for dubbing
  constitute copyright infringement even if user has license to view?
- Are we a "significant social media intermediary" under IT Rules 2021?
  (>5M users threshold — not relevant at launch but plan for it)

---

## 5. Competitive Response Plan

**If NeuralGarage launches a creator tier:**
- They'll price at ₹2999+ minimum (enterprise motion)
- Our ₹999 tier holds
- Their lip sync is better quality — we match on price + Indian language depth
- Accelerate voice clone feature — their product doesn't do this

**If Dubverse adds lip sync:**
- They have audio dubbing + Indian languages but no visual
- Adding lip sync is 6-12 months of engineering
- We'll have 6-12 months head start + better models (fine-tuned on Indian faces)
- Our speed-invariant playback SDK differentiates regardless

**If a well-funded startup directly targets our exact niche:**
- Dataset moat kicks in — they need 500+ minutes of Indian face data
- Creator network lock-in — voice clones live on our platform
- Speed-invariant research — published paper + patent gives credibility
- Response: raise a round immediately and accelerate

---

## 6. Success Metrics — Phase-Wise

### Phase 1 Success (End of Month 3)
- [ ] Pipeline processes 20-minute Hindi video → Telugu dubbed in < 1 hour
- [ ] WER on Hindi transcription < 12%
- [ ] Translation BLEU score > 28 on test set
- [ ] Background audio preserved (informal test: music still audible)
- [ ] 3 real creators have watched their own dubbed video
- [ ] At least 1 creator says they'd pay ₹999/month for this

### Phase 2 Success (End of Month 6)
- [ ] Lip sync applied to > 60% of scenes in typical EdTech video
- [ ] SyncNet score > 7.0 on processed scenes
- [ ] CSIM > 0.85 on Indian faces after fine-tuning
- [ ] QC flag rate < 20% of scenes
- [ ] Processing time < 2× video duration on A100
- [ ] 5 paying Creator tier users
- [ ] ₹5,000 MRR achieved

### Phase 3 Success (End of Month 12)
- [ ] Speed-invariant playback working at 0.5x, 1x, 1.5x, 2x
- [ ] Paper submitted to ACM MM 2026
- [ ] Provisional patent filed
- [ ] 100 paying Creator tier users
- [ ] ₹1.4 lakh MRR
- [ ] Seed round raised or term sheet received
- [ ] At least 1 creator whose regional views grew > 40% after dubbing

---

## 7. Risk Mitigation — Execution Level

**Risk: MuseTalk license issue**
Mitigation: Before writing a single line of Phase 2 reanimation code,
verify Apache 2.0 allows commercial use. Email Tencent Research if unclear.
Fallback confirmed: VideoReTalking (Apache 2.0, confirmed commercial OK).

**Risk: MFA missing Telugu acoustic model**
Check immediately:
```bash
mfa model download acoustic telugu_mfa
# If not available:
mfa model download acoustic hindi_mfa
# Use Hindi model as approximation for Telugu
# Or: build Telugu acoustic model from IndicVoices-R
```

**Risk: Demucs too slow on CPU (affects Phase 1 users without GPU)**
- Demucs CPU inference: ~10× realtime (10-min video = 100 min processing)
- Mitigation: Use lighter Demucs model (demucs.mdx_extra_q — 4× realtime on CPU)
- Or: skip separation for CPU-only tier, accept slightly lower quality

**Risk: XTTS-v2 Telugu quality rejected by real users**
Test in Week 3:
- Generate 10 Telugu sentences in 3 different cloned voices
- Play to 5 Telugu speakers (college friends/professors)
- If > 3/5 say "this doesn't sound like the original" → switch to Sarvam AI
  (API-based, better Indian language support, ~₹2/1000 chars)

**Risk: IndicTrans2 fails on code-mixed Hinglish**
- Benchmark immediately on 20 code-mixed sentences
- If BLEU < 15 on code-mixed: add language detection step
- Segment-level: detect code-mixed segments via IndicLID
- Route code-mixed segments to GPT-4o mini (better at Hinglish)
- Cost: ~₹0.08/minute extra for code-mixed content only

**Risk: Compute costs exceed budget during development**
- Use Google Colab Pro+ (₹4,000/month) for all experimentation
- Only move to Vast.ai for fine-tuning runs
- Track all GPU hours in a spreadsheet
- Set hard limit: ₹15,000/month compute budget during development

---

## 8. Tools and Accounts to Set Up Now

**Immediately:**
- [ ] GitHub repo: voxbridge (private)
- [ ] Google Colab Pro+ subscription
- [ ] Vast.ai account + $50 credit for fine-tuning
- [ ] Cloudflare account (R2 for storage — 10GB free)
- [ ] HuggingFace account (model hosting, dataset download)
- [ ] Weights & Biases account (experiment tracking — free for students)

**Before Phase 2:**
- [ ] AWS Activate application (GPU credits)
- [ ] Google for Startups application (GCP credits)
- [ ] Microsoft for Startups (Azure credits)
- [ ] AI4Bharat research collaboration email
  (They're at IIIT Hyderabad — reachable from your institution)

**Before Revenue:**
- [ ] Razorpay account (Indian payment gateway)
- [ ] Stripe account (international payments)
- [ ] Legal: register as LLP or Pvt Ltd
- [ ] DPDP Act compliance review (one-time legal consultation)
