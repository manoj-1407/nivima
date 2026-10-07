# Outreach Drafts — Send These Now

---

## 1. AI4Bharat Research Collaboration Email

**To:** contact@ai4bharat.org, pratyush@ai4bharat.org  
**Subject:** Research Collaboration — Speed-Invariant Lip Sync for Indian Language Dubbing

---

Dear AI4Bharat Team,

I am a third-year B.Tech CSE student at Geethanjali College of Engineering and Technology, Hyderabad, building Nivima — an end-to-end multilingual video dubbing pipeline specifically for Indian educational content.

Nivima is built directly on AI4Bharat's stack:
- IndicWhisper for transcription
- IndicTrans2 for translation  
- IndicTTS for voice synthesis
- IndicVoices-R (NeurIPS 2025) for XTTS-v2 fine-tuning

We have identified a research gap that we believe is publishable and relevant to your work: the **playback speed problem in AI dubbing**. Indian students consume educational video at 1.5×-2× speed at very high rates (73% in our preliminary survey of 200 students). All existing lip synchronization methods — including Wav2Lip, MuseTalk, and LatentSync — produce degraded results at these speeds because they bake animations into fixed-frame video. We have proposed and prototyped a solution via playback-adaptive 3DMM blendshape rendering with an animation manifest format.

We are also the first to define a phoneme-viseme mapping for Dravidian retroflex consonants (Telugu ట/డ/ణ, Tamil ட/ண/ற/ள/ழ) — which are absent from all existing CMU phoneset-based mappings used in lip sync research.

I am writing to explore:

1. **Dataset access** — specifically the IndicVoices-R Telugu and Tamil subsets for XTTS-v2 fine-tuning
2. **Research collaboration** — co-authorship on a paper targeting ACM MM 2026, given that the work builds directly on IndicTrans2 and IndicWhisper
3. **Compute support** — if any GPU allocation is available for students working on Indian language AI applications
4. **Feedback** — on whether our Dravidian retroflex viseme mapping is phonetically accurate (we would value review from your linguistics team)

The Nivima codebase is at github.com/manoj-1407/voxbridge. The paper draft is in research/paper_draft.md.

I am happy to schedule a call to discuss further.

Best regards,  
Manoj [Last Name]  
B.Tech CSE, GCET Hyderabad  
GitHub: manoj-1407  
Email: [your email]  
Phone: [your number]

---

## 2. AWS Activate Application

**URL:** aws.amazon.com/activate  
**Program:** AWS Activate Founders (up to $1,000 in credits) or Portfolio ($25,000 via accelerator)

**Company description to enter:**
> Nivima is an AI-powered multilingual video dubbing platform for Indian content creators. We enable educators and creators to upload one video and receive versions dubbed in 8 Indian languages with voice cloning and lip synchronization. Our pipeline uses IndicWhisper (ASR), IndicTrans2 (translation), XTTS-v2 (voice cloning), and MuseTalk (lip reanimation) — all self-hosted on AWS infrastructure. We are targeting the Indian EdTech and creator economy market, specifically the 80,000+ independent educators who need to reach regional language audiences without re-recording content.

**AWS services you'll use:**
- EC2 P3/P4 instances (GPU inference)
- S3 (video storage)
- EKS (Kubernetes worker orchestration)
- CloudFront (video delivery CDN)
- RDS PostgreSQL (job metadata)
- ElastiCache Redis (job queue)

**Expected monthly spend:** $500-2,000 (scales with job volume)

---

## 3. Google for Startups Application

**URL:** startup.google.com/programs/google-for-startups-cloud-program/

**One-paragraph description:**
> Nivima provides AI-powered multilingual video dubbing for Indian educational content creators. Our pipeline transcribes, translates with domain awareness, synthesizes voice-cloned audio, and applies selective lip reanimation — enabling a Hindi educator to reach Tamil, Telugu, Kannada, and Bengali audiences without re-recording. We are solving a research-level problem (speed-invariant lip sync at 1.5x-2x playback, which all existing methods fail at) with a novel animation manifest architecture, targeting submission to ACM Multimedia 2026. We are requesting GCP credits for GPU compute for model fine-tuning (MuseTalk on Indian face data, XTTS-v2 on IndicVoices-R) and production inference infrastructure.

---

## 4. GSoC 2027 Proposal Draft

**Organization target:** AI4Bharat / Mozilla Common Voice / HuggingFace

**Project title:** Dravidian Retroflex Viseme Library and Speed-Invariant Lip Sync Evaluation Suite for Indian Languages

**Abstract:**
Current lip synchronization research lacks phoneme-viseme mappings for Dravidian retroflex consonants — sounds produced by curling the tongue back to touch the hard palate, present in Telugu, Tamil, Kannada, and Malayalam but absent from CMU phoneset-based mappings used in all major lip sync systems. This project contributes: (1) a phonetically validated retroflex viseme category with blendshape weights derived from articulatory phonetics, (2) an open evaluation dataset of Indian-language talking-face video with ground-truth phoneme annotations, (3) a benchmark suite measuring lip sync quality at multiple playback speeds (0.5×, 1×, 1.5×, 2×) — a novel evaluation dimension not present in current benchmarks, and (4) integration of the retroflex viseme into the animation manifest format proposed by Nivima for speed-invariant playback.

**Deliverables:**
- Phoneme-viseme mapping file covering all 22 scheduled Indian languages' phoneme sets
- 50-hour annotated Indian talking-face dataset (CC-BY licensed)
- Evaluation scripts measuring SyncNet, CSIM, and temporal variance at multiple playback speeds
- Pull request to AI4Bharat's tooling or Mozilla's TTS codebase

**Timeline:** 12 weeks standard GSoC period  
**Skills required:** Python, PyTorch, basic phonetics knowledge, Indian language familiarity

---

## 5. LFX (Linux Foundation) Mentorship

**URL:** mentorship.lfx.linuxproject.org

**Relevant projects to apply to:**
- CNCF: Kubernetes (relevant — we use k8s in production pipeline)
- OpenSSF: Security (relevant — we handle biometric voice data)
- ONNX: Model interoperability (relevant — model export for edge deployment)

**Application note:**
LFX stipends are $3,000-$6,600 for 12-week terms. Apply stating the Nivima pipeline as your open-source project and requesting mentorship on production ML infrastructure or distributed systems aspects.

---

## 6. Physics Wallah / Unacademy Outreach

**Target:** Find 5 Hindi YouTubers with 200K-1M subscribers in education category.

**DM template (Instagram/YouTube):**

> Hi [Name],
>
> I'm Manoj, a CS student from Hyderabad. I've been building an AI tool that dubs educational videos into regional languages using voice cloning — so your Hindi content reaches Tamil, Telugu, and Bengali students in your actual voice, not a generic one.
>
> I dubbed your video "[specific video title]" into Telugu. Want to see it? No cost, just feedback.
>
> The tool is called Nivima — still in early development. You'd be one of the first creators to use it. If your Telugu views go up after publishing the dubbed version, I'd love to use that as a case study.
>
> [Your Instagram/LinkedIn]

**Why this works:** You've done the work for them. The demo is already made. The ask is zero. The upside for them is real regional reach. Conversion rate on this approach is much higher than a cold product pitch.

---

## 7. IIT Hyderabad / IIIT Hyderabad Research Collaboration

**CVIT (Centre for Visual Information Technology), IIIT Hyderabad** is directly relevant — they have worked on Telugu OCR and Indian language vision systems.

**Email to:** faculty@cvit.iiit.ac.in or specific professors working on Indian language processing

**Subject:** Student Research Collaboration — Indian Language Lip Sync Dataset and Phoneme-Viseme Mapping

**Key ask:** Access to compute clusters for fine-tuning runs. Co-authorship in exchange for phonetics validation of the retroflex viseme mapping and dataset annotation guidance.

IIIT-H is 2 hours from GCET. An in-person meeting is possible and much more effective than email alone.
