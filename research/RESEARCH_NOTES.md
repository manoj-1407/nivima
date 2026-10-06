# VoxBridge — Research Notes

---

## 1. Core Papers — Must Read Before Building Each Component

### Lip Sync / Reanimation

**Wav2Lip (2020) — The baseline**
- Prajwal et al., ACM MM 2020
- "A Lip Sync Expert Is All You Need for Speech to Lip Generation in the Wild"
- Key insight: train a sync discriminator separately, use it to guide generator
- Limitation: 96×96 face crop — visibly blurry on HD footage
- Why we don't use it: quality too low for 2026 standards
- arXiv: 2008.10010

**MuseTalk 1.5 (2024) — Our speed tier**
- Zhang et al., Tencent AI Lab
- arXiv: 2410.10122
- Key insight: latent space inpainting — modify face in latent space, not pixel space
- Single-step inference → 30fps on V100
- Processes 256×256 face region → upscale back to original
- Training data: LRS2, VoxCeleb2, HDTF datasets
- License: Apache 2.0 ✓

**LatentSync 1.6 (2024) — Our quality tier**
- Li et al., ByteDance Research
- arXiv: 2412.09262
- Key insight: audio conditioned latent diffusion + TREPA for temporal consistency
- TREPA: temporal representations alignment — reduces flickering significantly
- Higher quality but multi-step diffusion → slower
- Outperforms MuseTalk on SyncNet score and visual quality
- License: verify before Phase 2

**UniSync (2025) — State of the art**
- arXiv: 2603.03882
- "Towards Generalizable and High-Fidelity Lip Synchronization"
- Handles challenging scenarios: profile views, multiple speakers
- Not yet practical for our timeline — monitor for Phase 3+

**TBDub (2025) — Production-oriented dubbing**
- arXiv: 2609.06144
- Most relevant to our full pipeline
- Addresses the full dubbing workflow not just reanimation
- Read carefully before Phase 2 architecture finalization

**NeRF-LipSync (2025)**
- ISPRS Journal 2025
- Diffusion + NeRF spatial alignment for view-consistent lip sync
- Interesting for future profile shot handling
- Not practical for Phase 2 timeline

---

### ASR and Transcription

**Whisper (2022) — Our fallback**
- Radford et al., OpenAI
- "Robust Speech Recognition via Large-Scale Weak Supervision"
- large-v3: best publicly available general ASR
- WER on Indian languages: 15-25% (acceptable as fallback)
- arXiv: 2212.04356

**Vistaar / IndicWhisper (2023) — Our primary**
- AI4Bharat, INTERSPEECH 2023
- "Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR"
- Fine-tuned Whisper on 10,700 hours of Indian language audio
- Achieves lowest WER in 39/59 test sets on Vistaar benchmark
- Average 4.1 WER reduction vs base Whisper on Indian languages
- HuggingFace: ai4bharat/indicwhisper

---

### Translation

**IndicTrans2 (2023) — Our primary translator**
- AI4Bharat, 2023
- "Towards High-Quality and Accessible Translation for All 22 Scheduled Indian Languages"
- Covers all 22 scheduled Indian languages
- Handles Devanagari, Dravidian scripts natively
- Model: ai4bharat/indictrans2-indic-indic-dist-200M (200M params, faster)
- Larger: ai4bharat/indictrans2-indic-indic-1B (better quality, slower)
- HuggingFace: ai4bharat/indictrans2-indic-indic-dist-200M

**NLLB-200 (2022) — Fallback translator**
- Meta AI
- "No Language Left Behind"
- Covers 200 languages including Indian languages
- Weaker than IndicTrans2 specifically for Indian pairs
- Use for languages IndicTrans2 doesn't cover
- HuggingFace: facebook/nllb-200-distilled-600M

---

### TTS and Voice Cloning

**XTTS-v2 (2023) — Our voice cloner**
- Coqui AI (now defunct — weights frozen at v2)
- Cross-lingual voice cloning from 6 seconds of reference audio
- Supports 17 languages natively (Hindi included, Telugu not)
- Available: github.com/coqui-ai/TTS, weights on HuggingFace
- Critical: Coqui shut down in Jan 2024 — no future updates
- License: Coqui Public Model License (non-commercial free, commercial needs agreement)
  **Verify this before Phase 2 paid launch**

**IndicVoices-R (2025) — Our fine-tuning data**
- AI4Bharat, NeurIPS 2025 Datasets Track
- 1704 hours, 10496 speakers, 22 Indian languages
- High quality, diverse demographics
- Specifically designed for TTS training
- HuggingFace: ai4bharat/IndicVoices-R

**IndicTTS — Generic voice**
- AI4Bharat
- Covers 13 Indian languages
- VITS-based architecture
- Good quality generic TTS, no voice cloning
- Used for free tier / when no voice clone provided

---

### Audio

**Demucs (2021) — Audio separation**
- Défossez et al., Meta AI
- "Music Source Separation in the Waveform Domain"
- Separates: vocals, bass, drums, other
- We use: vocals (speech) vs other (background)
- Model: htdemucs (best quality), mdx_extra_q (fastest)
- License: MIT ✓

**Montreal Forced Aligner (2017)**
- McAuliffe et al., INTERSPEECH 2017
- Aligns transcript to audio at phoneme level
- Required for: timing constraint generation (Path A), force alignment (Stage 6)
- Acoustic models available: Hindi, others may need training
- GitHub: MontrealCorpusTools/Montreal-Forced-Aligner

---

### Face Analysis

**MediaPipe FaceMesh — Face detection + landmarks**
- Google
- 468 face landmarks at 30fps on mobile
- Used for: face detection, landmark extraction, occlusion estimation
- License: Apache 2.0 ✓

**3DDFA-V2 (2020) — Head pose estimation**
- Guo et al., ECCV 2020
- "Towards Fast, Accurate and Stable 3D Dense Face Alignment"
- 3D face fitting: estimates yaw, pitch, roll
- Faster than older methods, works on video
- Used for: scene classification (FRONTAL_CLEAR vs PROFILE)
- GitHub: cleardusk/3DDFA_V2

**pyannote-audio 3.x — Speaker diarization**
- Bredin et al., ICASSP 2023
- Who speaks when
- Used for: multi-speaker scene handling
- HuggingFace: pyannote/speaker-diarization-3.1
- Requires HuggingFace token + terms acceptance

---

## 2. Benchmark Targets

### Transcription (IndicWhisper)
| Language | Target WER | Baseline (Whisper) |
|---|---|---|
| Hindi | < 8% | ~15% |
| Telugu | < 12% | ~22% |
| Tamil | < 12% | ~20% |
| Kannada | < 15% | ~25% |

Evaluate on Vistaar benchmark: ai4bharat/vistaar

### Translation (IndicTrans2)
| Direction | Target BLEU | Baseline |
|---|---|---|
| Hindi → Telugu | > 32 | ~28 |
| Hindi → Tamil | > 30 | ~26 |
| Hindi → Kannada | > 30 | ~25 |

Evaluate on IN22-Gen benchmark (IndicTrans2 paper)

### Lip Sync Quality (MuseTalk fine-tuned)
| Metric | Target | Baseline (no fine-tune) |
|---|---|---|
| SyncNet Score | > 7.5 | ~6.8 |
| CSIM (Indian faces) | > 0.86 | ~0.79 |
| PSNR non-lip region | > 40 dB | ~38 dB |
| Temporal variance | < 5.0 | ~8.2 |

### Voice Clone Quality (XTTS-v2)
| Language | Target similarity | Current |
|---|---|---|
| Hindi (native) | > 80% | ~82% |
| Telugu (fine-tuned) | > 75% | ~62% |
| Tamil (fine-tuned) | > 72% | ~60% |

Measure: MOS (Mean Opinion Score) from human evaluators + speaker similarity via speaker verification model

---

## 3. Evaluation Methodology

### Automated Evaluation Pipeline
```python
# research/evaluate_pipeline.py

def run_full_evaluation(test_set_dir: str) -> dict:
    results = {}
    
    # 1. Transcription quality
    results['asr'] = evaluate_asr(
        test_set_dir,
        model='indicwhisper',
        metric='wer'
    )
    
    # 2. Translation quality
    results['translation'] = evaluate_translation(
        test_set_dir,
        model='indictrans2',
        metric='sacrebleu'
    )
    
    # 3. TTS naturalness (automated MOS estimation)
    results['tts'] = evaluate_tts(
        test_set_dir,
        metric='utmos'  # UTMOS: automated MOS estimator
    )
    
    # 4. Voice clone similarity
    results['voice_clone'] = evaluate_voice_similarity(
        test_set_dir,
        metric='speaker_similarity'  # cosine similarity of speaker embeddings
    )
    
    # 5. Lip sync quality (reanimated scenes only)
    results['lip_sync'] = evaluate_lip_sync(
        test_set_dir,
        metrics=['syncnet', 'csim', 'psnr', 'temporal_variance']
    )
    
    return results
```

### Human Evaluation Protocol

**Evaluators:** 20 native speakers per target language (recruited from campus)

**Tasks:**
1. Translation quality: rate semantic accuracy 1-5
2. Voice naturalness: rate TTS quality 1-5
3. Voice similarity: rate how similar cloned voice is to original 1-5
4. Lip sync quality: rate how natural lip movement looks 1-5
5. Overall quality: would you watch content dubbed this way? Yes/No

**For speed-invariant evaluation (Phase 3):**
Watch same clip at 1x, 1.5x, 2x
Rate: does lip sync look worse at higher speeds? (1-5, 5=no difference)
Compare: VoxBridge (speed-invariant) vs MuseTalk baked (standard) at each speed

---

## 4. Our Research Contribution

### Paper 1: Speed-Invariant Lip Sync

**Novel contributions:**
1. First identification of the playback-speed problem in AI dubbing
2. Animation manifest format — separates intent from pixels
3. Indian phoneme viseme library for Dravidian languages
4. Playback-adaptive 3DMM blendshape rendering
5. Quantitative evaluation across playback speeds

**Baseline comparisons:**
- MuseTalk (baked video) at 0.5x, 1x, 1.5x, 2x
- LatentSync (baked video) at same speeds
- Our method at same speeds
- Metric: SyncNet score vs playback speed (shows degradation in baselines, stability in ours)

**Target venues:**
- Primary: ACM Multimedia 2026 (submission deadline: ~April 2026)
- Secondary: EMNLP 2026 multilingual track
- Workshop: CVPR 2026 workshop on video synthesis

### Paper 2: Constrained Multilingual Dubbing Script Generation

**Novel contributions:**
1. Formal definition of phoneme-constrained translation
2. Two-step approach: IndicTrans2 + LLM constrained rewrite
3. Evaluation: does constrained script reduce dubbing iterations?
4. Dataset: Hindi-Telugu dubbing pairs with phoneme timing annotations

**Target venue:** EMNLP 2026, ACL 2026

---

## 5. Phoneme-Viseme Mapping — Indian Languages Extension

Standard English phoneme-viseme mapping (CMU phoneset) doesn't cover:
- Telugu retroflex stops: ట (ṭa), డ (ḍa), ణ (ṇa)
- Tamil retroflex: ட, ண, ற
- Aspirated stops in Hindi: ख (kha), घ (gha), छ (cha)
- Retroflex fricative: ष (ṣa)

**Extended mapping for Dravidian languages:**
```python
EXTENDED_PHONEME_VISEME = {
    # Standard English set
    'p': 'bilabial_closure',
    'b': 'bilabial_closure',
    'm': 'bilabial_closure',
    'f': 'labiodental',
    'v': 'labiodental',
    'th': 'dental',
    'dh': 'dental',
    't': 'alveolar',
    'd': 'alveolar',
    'n': 'alveolar',
    's': 'alveolar',
    'z': 'alveolar',
    'sh': 'palatal',
    'zh': 'palatal',
    'ch': 'palatal',
    'jh': 'palatal',
    'k': 'velar',
    'g': 'velar',
    'ng': 'velar',
    'aa': 'open_wide',
    'ae': 'mid_open',
    'ah': 'mid_open',
    'eh': 'mid_open',
    'ih': 'spread',
    'iy': 'spread',
    'ow': 'rounded',
    'uw': 'rounded',
    'er': 'central',
    
    # Indian language extensions
    # Retroflex stops (tongue curled back — unique mouth shape)
    'tt_retro': 'retroflex',   # ट, ட
    'dd_retro': 'retroflex',   # ड, ட
    'nn_retro': 'retroflex',   # ण, ண
    'rr_retro': 'retroflex',   # ற (Tamil alveolar trill)
    'll_retro': 'retroflex',   # ள (Tamil retroflex lateral)
    'zh_retro': 'retroflex',   # ழ (Tamil retroflex approximant — unique)
    
    # Aspirated stops (more airflow — visible in lip separation)
    'kh': 'velar_aspirated',   # ख, க்
    'gh': 'velar_aspirated',   # घ
    'ch_asp': 'palatal_aspirated',  # छ
    'ph': 'bilabial_aspirated', # फ, ப
    'bh': 'bilabial_aspirated', # भ
    'th_asp': 'dental_aspirated',  # थ
    'dh_asp': 'dental_aspirated',  # ध
    
    # Silence and boundary
    'sil': 'silence',
    'sp': 'silence',
}

# Blendshape weights per viseme
VISEME_BLENDWEIGHTS = {
    'bilabial_closure': {
        'jaw_open': 0.0,
        'lip_corner_puller': 0.0,
        'upper_lip_raiser': 0.0,
        'lower_lip_depressor': 0.0,
        'lip_pressor': 0.9,      # lips pressed together
        'lip_tightener': 0.3,
    },
    'retroflex': {
        'jaw_open': 0.3,
        'lip_corner_puller': 0.1,
        'upper_lip_raiser': 0.2,
        'lower_lip_depressor': 0.2,
        'cheek_raiser': 0.2,     # slight cheek engagement
        'lip_tightener': 0.4,   # tongue curled back creates visible tension
    },
    'open_wide': {
        'jaw_open': 0.9,
        'lip_corner_puller': 0.3,
        'upper_lip_raiser': 0.2,
        'lower_lip_depressor': 0.6,
        'lip_tightener': 0.0,
    },
    'rounded': {
        'jaw_open': 0.4,
        'lip_corner_puller': 0.0,
        'lip_corner_depressor': 0.0,
        'upper_lip_raiser': 0.0,
        'lip_tightener': 0.6,   # rounded shape requires lip tension
        'lip_pressor': 0.3,
    },
    'silence': {
        'jaw_open': 0.0,
        'lip_corner_puller': 0.0,
        'upper_lip_raiser': 0.0,
        'lower_lip_depressor': 0.0,
        'lip_tightener': 0.1,   # slight natural resting tension
        'lip_pressor': 0.0,
    },
    # ... all viseme types
}
```

**This mapping is a novel research contribution.**
No published phoneme-viseme mapping exists for Dravidian retroflex sounds.
Standard CMU phoneset used by all existing lip sync research doesn't include these.
Our mapping = gap in the literature = paper contribution.

---

## 6. Datasets to Download — Priority Order

```bash
# 1. IndicVoices-R (highest priority — needed for TTS fine-tuning)
python -c "
from datasets import load_dataset
ds = load_dataset('ai4bharat/IndicVoices-R', 'te', split='train')
ds.save_to_disk('data/indicvoices_te')
"

# 2. Vistaar benchmarks (needed for ASR evaluation)
python -c "
from datasets import load_dataset
for lang in ['hi', 'te', 'ta', 'kn']:
    ds = load_dataset('ai4bharat/vistaar', lang)
    ds.save_to_disk(f'data/vistaar_{lang}')
"

# 3. VoxCeleb2 (needed for lip sync base training)
# Requires registration at: https://www.robots.ox.ac.uk/~vgg/data/voxceleb/
# Download script provided after registration

# 4. MUAVIC (multilingual audio-visual)
# github.com/facebookresearch/muavic
git clone https://github.com/facebookresearch/muavic
python muavic/download.py --languages hi te ta

# 5. LRS2 (BBC talking face — requires registration)
# https://www.robots.ox.ac.uk/~vgg/data/lip_reading/
# Academic use only — register with institutional email
```
