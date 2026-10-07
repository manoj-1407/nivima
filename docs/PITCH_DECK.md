# Nivima — Investor Pitch Deck
**Stage:** Pre-seed  
**Ask:** ₹1.5 crore (~$180K)  
**Use:** 12 months runway — finish product, acquire first 100 paying creators  

---

## Slide 1 — The Hook

**73% of Indian students watch educational video at 1.5× or faster.**

Every existing AI dubbing product breaks at that speed.

We built the only one that doesn't.

---

## Slide 2 — The Problem

India has 500M+ internet users consuming content in 22 languages.

The top 1000 Hindi educational creators on YouTube collectively have 800M+ subscribers.

Zero of them can reach Tamil Nadu, Kerala, or Bengal students without re-recording everything.

**Current options:**

| Option | Cost | Quality | Time |
|---|---|---|---|
| Professional dubbing studio | ₹15,000-50,000/hour | High | 2-4 weeks |
| Generic AI audio dubbing | ₹1,000-5,000/video | Mediocre | Hours |
| Re-record in regional language | ₹0 but impossible | High | Never done |

The gap: **no affordable, high-quality, creator-accessible dubbing tool exists for Indian languages.**

---

## Slide 3 — The Solution

**Nivima: Upload once. Reach everyone.**

Upload one Hindi lecture. Get it back dubbed in Telugu, Tamil, Kannada, Malayalam, Bengali — in the creator's own cloned voice — with lip sync that works at any playback speed.

**Three things nobody else does:**

1. **Voice preservation** — not a generic voice. The creator's actual voice, cloned, speaking regional languages. Students recognize their teacher.

2. **Domain awareness** — a physics lecture translates differently than a cooking video. We detect the domain and apply subject-specific terminology handling.

3. **Speed-invariant lip sync** — the only dubbing system that maintains sync quality at 1.5× and 2× playback. Patent pending.

---

## Slide 4 — Product Demo

*[Live demo or video recording of the pipeline]*

**Input:** 10-minute Physics Wallah-style Hindi lecture  
**Output:** Telugu dubbed video, creator's cloned voice, lip sync maintained at 2×

**Processing time:** 25 minutes on our infrastructure  
**Cost to us:** ₹40  
**Price to creator:** ₹100-200  

---

## Slide 5 — Market Size

**Indian OTT market:** $5.4B in 2025, projected $28.1B by 2034 (19% CAGR)

**Regional language content:** 52% of total OTT viewing, growing faster than Hindi

**Independent Indian YouTube creators with 100K+ subscribers:** 500,000+  
**Education category (our entry point):** ~80,000 creators

**Total Addressable Market (TAM):** Content localization in India — $800M/year  
**Serviceable Addressable Market (SAM):** Independent creators + EdTech — $120M/year  
**Serviceable Obtainable Market (SOM) Year 3:** $6M ARR (5% of SAM)

---

## Slide 6 — Business Model

**Three revenue streams:**

**1. Creator SaaS (primary)**
| Tier | Price | Minutes | Voice Clone |
|---|---|---|---|
| Free | ₹0 | 10/month | No |
| Creator | ₹999/month | 120/month | Yes |
| Professional | ₹3,999/month | 600/month | 3 voices |

**2. API Access**
EdTech platforms integrate our pipeline. ₹4/minute processed.
BYJUs, Unacademy, PhysicsWallah can white-label instead of building in-house.

**3. Enterprise**
Custom pricing for production houses, corporate L&D, government communication.

**Unit economics (Creator tier):**
- Revenue per minute: ₹8.33
- Cost per minute: ₹3.10 (self-hosted models, spot GPU)
- Gross margin: **63%**

---

## Slide 7 — Traction

*[To be filled in as milestones are hit]*

**Month 1:** Pipeline running end-to-end. First 5 real videos processed.  
**Month 2:** First 10 beta creators. Regional view increase measured.  
**Month 3:** First paying customer.  
**Month 6:** 50 paying creators. ₹50,000 MRR.  
**Month 12:** 200 paying creators. ₹2L MRR.  

**Key leading indicator:** Do creators' regional language views increase after dubbing?  
First case study target: 30%+ view increase within 30 days of publishing dubbed versions.

---

## Slide 8 — Why Now

**Three things that just became true:**

1. **MuseTalk (2024) and LatentSync (2024)** — lip reanimation quality crossed the acceptable threshold for non-cinema content

2. **IndicVoices-R (NeurIPS 2025)** — 1,704 hours of Indian language voice data just became publicly available. Cross-lingual voice cloning for Indian languages is now trainable.

3. **DPDP Act 2023** — India's data protection law creates demand for on-premise / privacy-first processing. A product built with privacy-first architecture has regulatory tailwind.

These three didn't exist 18 months ago. The window is open now.

---

## Slide 9 — Competitive Landscape

| Player | What They Do | Why We Win |
|---|---|---|
| NeuralGarage (India) | Cinema lip sync, used in Coolie | Enterprise pricing (₹50K+ per film). Ignores creators. |
| Dubverse.ai (India) | Audio dubbing, 30+ Indian languages | No visual component. No voice cloning. |
| HeyGen (US) | Talking head lip sync | Western face bias. No Indian language pipeline. $30/month minimum. |
| Sync Labs (US) | Best technical quality | No Indian languages. US-focused. |
| Manual dubbing studios | High quality | ₹50,000/hour. 2-week turnaround. |

**The gap we fill:** Indian languages + voice cloning + lip sync + creator pricing + speed-invariant playback.

No one else has all five.

---

## Slide 10 — Moat

**Why can't someone copy this in 6 months?**

**Layer 1 — Technical (copyable in 18 months):**
IndicTrans2 + MuseTalk + XTTS-v2 pipeline. Any competent ML team can replicate.

**Layer 2 — Data (copyable in 3 years):**
Indian face dataset (500 min, 50 volunteers, annotated). Dubbed ground truth pairs from creator partnerships. Models fine-tuned on this data outperform generic models on Indian content.

**Layer 3 — Research (5+ years with a head start):**
Speed-invariant playback via animation manifest + 3DMM blendshape renderer. Published paper + provisional patent. Nobody else has even identified this problem.

**Layer 4 — Network (never copyable):**
Creator voice clones live on our platform. Switching means rebuilding the clone. Creator community trust built over years of delivering regional audience growth.

---

## Slide 11 — Team

**Manoj [Last Name]** — Founder & CEO  
B.Tech CSE, Geethanjali College of Engineering, Hyderabad  
Built Nivima pipeline architecture, Phase 1-3 implementation  
Background: backend systems, distributed systems, ML pipelines  
GitHub: manoj-1407  

*[Co-founders / advisors to be added]*

**What we're looking for:**
- ML engineer with TTS/voice experience
- Business development for EdTech partnerships
- Advisor with media/OTT industry connections

---

## Slide 12 — The Ask

**Raising:** ₹1.5 crore pre-seed  
**Structure:** SAFE note, 15% discount, ₹15 crore cap  

**Use of funds:**
| Allocation | Amount | Purpose |
|---|---|---|
| GPU compute | ₹30L | Fine-tuning + production inference |
| Engineering (1 ML hire) | ₹60L | 12 months, model quality improvement |
| Creator acquisition | ₹20L | Free processing for first 100 creators |
| Legal + compliance | ₹15L | DPDP Act, IP filing, entity setup |
| Operations | ₹25L | Infrastructure, tools, misc |

**Milestones this raise gets us to:**
- 200 paying creators
- ₹2L MRR
- Paper submitted to ACM MM 2026
- Provisional patent filed
- Seed round raise at proven metrics

---

## Slide 13 — Vision

**Year 1:** The tool every serious Indian YouTube educator uses to reach all of India.

**Year 3:** The infrastructure layer for all regional language content distribution in India. EdTech platforms, OTT, government communications, corporate training all running through Nivima APIs.

**Year 5:** Expand to Southeast Asia (Indonesia, Vietnam, Thailand) — same problem, same structural gap, larger market.

**The 10-year vision:** Every piece of human knowledge produced in one language, accessible to every person in their own language, in the creator's own voice. Nivima is the infrastructure that makes that happen.

---

## Appendix A — Technical Architecture

*[Link to RFC_COMPLETE.md and MASTER_PLAN.md]*

## Appendix B — Unit Economics Detail

*[Link to EXECUTION_AND_BUSINESS.md — Unit Economics section]*

## Appendix C — Research Paper

*[Link to paper_draft.md]*
