# FORM 2
### THE PATENTS ACT, 1970 (39 of 1970)
### &
### THE PATENTS RULES, 2003
## PROVISIONAL SPECIFICATION
*(See section 10 and rule 13)*

---

### 1. TITLE OF THE INVENTION
**SYSTEM AND METHOD FOR PLAYBACK-ADAPTIVE NEURAL VIDEO LIP SYNCHRONIZATION UTILIZING DYNAMIC BLENDSHAPE MANIFESTS AND DRAVIDIAN RETROFLEX ARTICULATION PARAMETERIZATION**

---

### 2. APPLICANT(S)

| Attribute | Details |
|---|---|
| **Name** | Manoj |
| **Nationality** | Indian |
| **Address** | Hyderabad, Telangana, India |
| **Category** | Natural Person / Student Inventor (Eligible for Concessional Filing Fee under Startups/Educational Institutions Scheme) |

---

### 3. PREAMBLE TO THE DESCRIPTION

**THE FOLLOWING SPECIFICATION DESCRIBES THE INVENTION.**

---

### 4. FIELD OF THE INVENTION

The present invention relates generally to artificial intelligence video synthesis, multilingual voice dubbing, computer vision, and digital facial reanimation. More particularly, the invention relates to a system and method for real-time, playback-speed-invariant synchronization of facial visual geometry with time-stretched audio, and an anatomical phonetic-to-visemic parameterization matrix for retroflex consonants in Dravidian and Indo-Aryan language families.

---

### 5. BACKGROUND OF THE INVENTION & OBJECTS

#### 5.1 Deficiencies of the Prior Art
Digital instructional video in India is predominantly consumed at accelerated playback speeds ($1.25\times$, $1.5\times$, $1.75\times$, or $2.0\times$) by students preparing for competitive technical and academic examinations. Existing state-of-the-art neural dubbing pipelines (such as Wav2Lip, MuseTalk, LatentSync, VideoReTalking, and commercial platforms like HeyGen) exhibit two critical technical deficiencies:

1. **The Fixed-Frame Temporal Aliasing Defect:**  
   Existing deep learning dubbing architectures synthesize rasterized pixel frames at a fixed temporal capture rate ($25.0$ or $30.0$ frames per second) calibrated strictly for $1.0\times$ normal-speed playback. When client video decoders accelerate playback, they apply frame-skipping or coarse frame interpolation while the audio engine applies phase-vocoder time stretching. This causes a progressive phase mismatch:
   $$\Delta t_{\text{desync}} \approx 60\text{ ms to } 180\text{ ms}$$
   High-frequency phonetic events—such as plosive bursts ($10\text{–}25\text{ ms}$) and rapid consonants—are frequently skipped, inducing visible desynchronization and unnatural mouth flutter.

2. **The CMU Phoneset Linguistic Blindspot for Indian Retroflex Consonants:**  
   Mainstream lip synchronization models utilize phonetic dictionaries derived from the Carnegie Mellon University (CMU) Pronouncing Dictionary (Arpabet), which was designed strictly for English phonology. Indian languages (including Telugu, Tamil, Kannada, Malayalam, Hindi, Marathi, Odia, Gujarati, Punjabi, Bengali) possess a distinct class of **retroflex consonants** (International Phonetic Alphabet: $[ʈ], [ɖ], [ɳ], [ɭ], [ɻ]$):
   - Telugu: ట $[ʈ]$, డ $[ɖ]$, ణ $[ɳ]$
   - Tamil: ட $[ʈ]$, ண $[ɳ]$, ள $[ɭ]$, ழ $[ɻ]$
   - Hindi: ट $[ʈ]$, ठ $[ʈʰ]$, ड $[ɖ]$, ढ $[ɖʱ]$, ण $[ɳ]$
   
   Conventional systems map these sounds to standard alveolar visemes ($[t], [d], [n]$). Physiologically, alveolar articulation involves minimal cheek and lip displacement. In contrast, retroflex articulation curls the apical tongue surface backwards against the palatal arch, inducing marked lateral cheek tension (via the *buccinator* muscle) and lip aperture widening. Substituting alveolar visemes creates visibly discordant, synthetic-looking facial motion that native Indian speakers instantly detect as unnatural.

#### 5.2 Objects of the Present Invention
- It is an object of the invention to provide a lightweight **Neural Animation Manifest (NAM)** format decoupling facial geometry from baked video frames.
- It is another object of the invention to evaluate blendshape trajectories continuously at the instantaneous client media clock, bounding cumulative phase drift to less than $2.0\text{ ms}$ across playback speeds from $0.5\times$ to $3.0\times$.
- It is a further object of the invention to establish the first formal 8-dimensional blendshape parameterization vector for Dravidian and Indo-Aryan retroflex phonemes.
- It is yet another object of the invention to provide an automated multi-metric quality control gate with feathered convex lip compositing to prevent non-lip video distortion.

---

### 6. SUMMARY OF THE INVENTION

The present invention solves the aforementioned challenges through an integrated system comprising:

1. **Acoustic Extraction and Domain-Aware Adaptation:** Ingesting source video, extracting vocals via harmonic separation, generating timestamps using Indian-accented acoustic models (IndicWhisper), and applying domain-constrained terminology preservation during bilingual machine translation (IndicTrans2).
2. **Dravidian Retroflex Viseme Parameterization:** Mapping identified retroflex consonants ($[ʈ], [ɖ], [ɳ], [ɭ], [ɻ]$) to a target blendshape vector comprising:
   $$\vec{V}_{\text{retroflex}} = \left[ w_{\text{jaw}}, w_{\text{lip\_press}}, w_{\text{lip\_tight}}, w_{\text{cheek\_raise}}, w_{\text{tongue\_elev}}, w_{\text{tongue\_curl}}, w_{\text{buccal\_tension}}, w_{\text{upper\_lip}} \right]$$
   where tongue curl activation is configured in the range $0.80\text{–}1.0$ and cheek raiser activation is configured in the range $0.50\text{–}0.75$.
3. **Decoupled Continuous Trajectory Manifest Generation:** Compiling target blendshape sequences into continuous piecewise cubic Hermite spline equations stored in a compact JSON manifest alongside time-stretched, timbre-cloned audio.
4. **Playback-Adaptive Edge Rendering:** A client-side WebGL/WebAssembly rendering engine that continuously evaluates spline polynomials at the audio hardware clock $\tau_{\text{audio}} = t \times s$, ensuring zero frame decimation and bounded sync error ($< 2.0\text{ ms}$) across variable playback rates.
5. **Human-In-The-Loop Data Flywheel:** A correction interface capturing user timeline adjustments to update regional phonetic transition matrices.

---

### 7. BRIEF DESCRIPTION OF THE DRAWINGS

- **Figure 1:** Block diagram illustrating the end-to-end cloud pipeline architecture of the Nivima platform.
- **Figure 2:** Graph depicting temporal alignment curves comparing fixed-frame rasterization vs continuous Hermite spline evaluation across varying playback rates.
- **Figure 3:** Anatomical facial landmark diagram showing retroflex tongue curl and buccinator cheek tension vectors.
- **Figure 4:** Flowchart of the automated multi-stage Quality Control (QC) decision tree and feathered convex-hull compositing pipeline.
- **Figure 5:** Architectural schematic of the client-side WebGL playback engine evaluating the Neural Animation Manifest.

---

### 8. DETAILED DESCRIPTION OF THE INVENTION

#### 8.1 Ingestion and Vocal Separation Pipeline
The input video $V_{\text{src}}$ is processed by an automated media validator verifying container codecs, minimum duration ($5.0\text{ s}$), and resolution. An audio demuxer isolates the primary audio track, which is processed by a 4-stem convolutional source separator to decouple the vocal speech signal $A_{\text{speech}}$ from background musical and environmental ambiance $A_{\text{ambient}}$.

The vocal signal is segmented into acoustic chunks ($4.0\text{–}8.0\text{ s}$) aligned to natural silence pauses ($> 300\text{ ms}$) and scene cuts identified by color histogram changes. Each chunk is transcribed using an acoustic model trained on regional Indian speech corpus, yielding word and phoneme timestamps:
$$\mathcal{T} = \left\{ (p_i, t_{\text{start}, i}, t_{\text{end}, i}, c_i) \right\}_{i=1}^N$$

#### 8.2 Bilingual Machine Translation with Lexical Constraint
A domain detection module classifies the speech transcript into technical categories (e.g., Physics, Engineering, Mathematics, Medicine). Technical register keywords are preserved in original English transliteration or mapped to standardized regional equivalents. A neural translation engine translates source sentences into the chosen Indian target language (Telugu, Tamil, Kannada, Malayalam, Hindi, etc.).

Target speech is synthesized using a cross-lingual voice cloning synthesizer conditioned on a reference vocal embedding ($\ge 6.0\text{ s}$) of the original speaker, preserving vocal identity and timbre across languages.

#### 8.3 Dravidian Retroflex Articulatory Blendshape Matrix
Synthesized audio is aligned to target phonemes using forced phonetic alignment. Unlike classical systems that discard retroflex articulation, the present invention maps retroflex phonemes to specialized 3D Morphable Model (3DMM) weights:

| Viseme Class | IPA Symbols | Jaw Open | Lip Tightener | Cheek Raiser | Tongue Curl | Buccal Tension |
|---|---|---|---|---|---|---|
| **Alveolar (Prior Art)** | $[t], [d], [n]$ | 0.25 | 0.20 | 0.00 | 0.05 | 0.00 |
| **Retroflex Plosive** | $[ʈ], [ɖ]$ (ట, డ, ट, ड) | 0.38 | 0.48 | 0.62 | 0.95 | 0.70 |
| **Retroflex Nasal** | $[ɳ]$ (ణ, ண, ण) | 0.30 | 0.35 | 0.55 | 0.90 | 0.60 |
| **Retroflex Approximant** | $[ɻ]$ (Tamil ழ) | 0.32 | 0.35 | 0.58 | 0.98 | 0.65 |
| **Retroflex Lateral** | $[ɭ]$ (Tamil ள) | 0.30 | 0.30 | 0.50 | 0.88 | 0.55 |

The non-zero activation of `cheek_raiser` ($0.50\text{–}0.75$) and `buccal_tension` ($0.55\text{–}0.70$) accurately reflects cutaneous displacement created by tongue-palate contact during retroflex articulation.

#### 8.4 Continuous Neural Animation Manifest (NAM) & Playback Engine
The blendshape targets are assembled into the Neural Animation Manifest:
$$S_k(t) = (1 - 3\theta^2 + 2\theta^3) P_k + (3\theta^2 - 2\theta^3) P_{k+1} + \theta(1 - \theta)^2 d_k + \theta^2(\theta - 1) d_{k+1}$$
where $\theta = (t - t_k) / (t_{k+1} - t_k)$, $P_k$ denotes target blendshape position, and $d_k$ represents velocity tangents calculated from adjacent coarticulation windows.

During client playback at variable playback multiplier $s \in [0.5, 3.0]$:
1. Client audio hardware outputs time-stretched audio at speed $s$.
2. The client video playback engine queries the audio timestamp $\tau_{\text{audio}}$ at display refresh intervals ($60\text{ Hz}$, $90\text{ Hz}$, or $120\text{ Hz}$).
3. The engine computes blendshape vector $W(\tau_{\text{audio}})$ continuously from spline polynomials without dropping frames.
4. A WebGL vertex shader applies vertex offsets $\vec{V} = \vec{V}_{\text{base}} + \sum W_j \vec{\Delta V}_j$ directly to the facial mesh.

This ensures cumulative phase drift remains strictly bounded:
$$\Delta t_{\text{desync}}(s) < 2.0\text{ ms}$$
preserving lip sync fidelity even at $2.0\times$ and $2.5\times$ speed.

#### 8.5 Automated Quality Gate & Safeguards
Synthesized frames are evaluated by a multi-objective Quality Control module:
- **SyncNet Confidence:** LSE-C $\ge 6.0$ and LSE-D $\le 8.5$.
- **Identity Preservation:** Cosine similarity of face embeddings CSIM $\ge 0.72$.
- **PSNR Safeguard:** Non-lip facial skin must maintain PSNR $\ge 35.0\text{ dB}$ against original frames.
- Chunks failing these thresholds automatically revert to original video frames with dubbed audio.

---

### 9. ABSTRACT OF THE INVENTION

A system and method for playback-speed-invariant multilingual video dubbing and facial reanimation are disclosed. Traditional deep learning lip-sync systems rasterize facial movements into static pixel frames calibrated strictly for $1.0\times$ playback and fail on Indian languages due to the lack of retroflex viseme modeling. The present invention decouples facial geometry into a continuous Neural Animation Manifest (NAM) encoding blendshapes as cubic Hermite splines. A client playback engine evaluates the splines at the instantaneous audio hardware clock, bounding cumulative phase drift to under $2.0\text{ ms}$ across playback speeds between $0.5\times$ and $3.0\times$. The invention further provides the first 8-dimensional blendshape parameterization vector for Dravidian and Indo-Aryan retroflex phonemes ($[ʈ], [ɖ], [ɳ], [ɭ], [ɻ]$), modeling tongue curvature and cheek tension.

---

### 10. DATED THIS 8th DAY OF OCTOBER, 2026

**SIGNATURE:**  
___________________________  
**Manoj**  
*(Applicant & Natural Person / Student Inventor)*

---

### 11. CHECKLIST FOR E-FILING AT IPINDIA.GOV.IN

To file this provisional application online at the Indian Patent Office portal (`https://ipindiaonline.gov.in/epass/`):

1. **User Registration:** Register on the e-Filing portal as a **Natural Person**.
2. **Form 1 (Application for Grant of Patent):** Fill in Applicant details, Inventor details, and Title of Invention.
3. **Form 2 (Provisional Specification):** Upload this specification as a PDF document.
4. **Form 3 (Statement and Undertaking under Section 8):** Statement regarding foreign filings (select 'None' if filing first in India).
5. **Form 5 (Declaration as to Inventorship):** Confirms Manoj as the sole inventor.
6. **Student Concession Document:** Upload Student ID card or College Bonafide Certificate (GCET Hyderabad) to claim the reduced fee tier.
7. **Statutory Fee:** **₹1,750/-** (payable via Net Banking / UPI on the e-filing portal).

*Filing this Form 2 establishes your international priority date under the Paris Convention, granting 12 months to file the Complete Specification and PCT international applications.*
