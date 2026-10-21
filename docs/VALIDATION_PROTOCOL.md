# Nivima Empirical Validation Protocol & Decision Gate

**Status**: FROZEN (Feature Freeze in Effect)  
**Date**: October 2026  
**Objective**: Empirically evaluate technical quality, buyer willingness-to-pay (WTP), and unit economics before committing to commercial software development.

---

## 1. Pre-Registered Benchmark Scoring Rubric

To eliminate evaluation bias, the scoring rubric is locked prior to testing. Two independent bilingual STEM educators will evaluate 3 complex 5-minute video samples (Hindi source dubbed into Telugu and Tamil) across Nivima, ElevenLabs Dubbing v2, and Dubverse under blinded conditions (system identities masked).

### Evaluation Dimensions (1–5 Likert Scale)

| Metric | 1 (Unacceptable) | 3 (Passable / Needs Edit) | 5 (Flawless / Broadcast Ready) |
| :--- | :--- | :--- | :--- |
| **Intelligibility** | Incomprehensible, muffled, or distorted audio. | Understandable with effort; occasional garbled syllables. | Crystal clear, natural acoustics, effortless comprehension. |
| **Translation Fidelity** | Meaning inverted, major omissions, or hallucinated facts. | Core concept intact, but awkward phrasing or lost nuances. | Pedagogically accurate, natural idioms, complete preservation of intent. |
| **Technical Terminology** | Core STEM terms mistranslated (e.g., literal Hindi idioms for physics laws). | Standard terms translated, but inconsistent with regional textbook standards. | Precise syllabus-standard scientific terminology (State Board / NCERT). |
| **Pronunciation & Prosody** | Robotic pacing, incorrect phoneme stresses, unnatural pitch resets. | Understandable cadence, but unnatural sentence boundary pauses. | Native regional speaker inflection, appropriate pedagogical emphasis. |
| **A/V Synchronization** | Severe drift (>250ms), jarring visual/auditory mismatch. | Timing acceptable for screen shares; noticeable lip drift on talking heads. | Tight alignment (<=40ms drift), natural articulatory transitions. |

### Critical Terminology Error Count (Tracked Separately)
* **Definition**: Any error in a formula, unit, proper noun, scientific principle, or definition that renders the educational explanation factually incorrect.
* **Metric**: Total count of critical errors per 5-minute lecture. Target: **0 critical errors** after human-in-the-loop review.

---

## 2. Event-Driven Quota & Cost Ledger Schema

To prevent accounting discrepancies and correctly isolate infrastructure costs from labor overhead, every pilot transaction must be audited against this event schema:

### Ledger Event Model

$$\Delta \text{Quota Balance} = \sum (\text{RESERVED}) - \sum (\text{RELEASED}) - \sum (\text{REFUNDED}) + \text{ADJUSTMENTS}$$

$$\text{Delivered Output Minutes} = \sum (\text{COMPLETED})$$

*Note: Completed output minutes are tracked independently of quota deductions.*

| Event Type | Trigger | Database Impact | Cost Allocation |
| :--- | :--- | :--- | :--- |
| `RESERVATION_CREATED` | Job submitted via API. | Increments pending reservation lock. | $0.00 |
| `STORAGE_UPLOAD_COMMITTED` | Video uploaded to S3. | Records object S3 key and byte size. | Storage ingest cost. |
| `JOB_EXECUTION_STARTED` | Celery worker picks up task. | Job status $\rightarrow$ `processing`. | GPU wall-clock run begins. |
| `JOB_EXECUTION_COMPLETED` | Output MP4 rendered and QC verified. | Job status $\rightarrow$ `completed`. Quota $\rightarrow$ `CONSUMED`. | Actual GPU + egress compute cost. |
| `JOB_EXECUTION_FAILED` | Pipeline error or worker failure. | Job status $\rightarrow$ `failed`. Quota $\rightarrow$ `RELEASED`. | Sunk GPU compute cost (tracked as waste). |
| `HUMAN_REVIEW_LOGGED` | Reviewer approves/edits segment. | Review duration (minutes) & wage recorded. | Direct human labor cost. |
| `CUSTOMER_REVISION_LOGGED` | Customer requests re-render/re-edit. | Additional labor & compute recorded. | Direct rework expense. |

---

## 3. Customer Discovery Interview Guide (10 Budget Holders)

Target respondents: Content Operations Heads, Academic Directors, or Technical Publishers managing regional content (State test-prep, vocational institutes, STEM academies).

### Core Questions (Evidence-Based)
1. **Existing Spend**: *"In the last 6 months, how many hours of video did you localize into Telugu/Tamil/Marathi, and what was your total expenditure (agency invoices or in-house salaries)?"*
2. **Turnaround & Bottleneck**: *"What is your average turnaround time per lecture, and where does the workflow stall (translation accuracy, voice talent availability, teacher review)?"*
3. **Acceptance Threshold**: *"What specific errors cause your academic team to reject a dubbed video?"*
4. **Subtitles vs. Audio**: *"Under what circumstances do your students reject English subtitles and demand regional audio dubbing?"*
5. **Budget Authority**: *"Who approves localization purchase orders, and what is the ceiling per minute before requiring executive sign-off?"*

---

## 4. Conjunctive Go / No-Go Decision Gate

To prevent confirmation bias, **all four criteria must pass simultaneously**. A superior result on one dimension cannot compensate for a failure on another:

| Gate | Metric | Pass Condition | Fail Action |
| :--- | :--- | :--- | :--- |
| **Gate 1: Technical Quality** | Blind Educator Benchmark across 3 STEM lectures | Nivima achieves mean score $\ge 3.8/5.0$ and $\le 1$ critical terminology error per lecture. | If quality fails: Revert to core research prototype or deprecate generator. |
| **Gate 2: Buyer Willingness-to-Pay** | 10 Customer Discovery Interviews | At least 3 qualified decision-makers confirm active budget $\ge ₹40\text{/output minute}$. | If WTP $< ₹30$: Conclude B2B EdTech SaaS thesis; discontinue commercialization. |
| **Gate 3: Direct Delivery Margin** | 3-Hour Paid Pilot (180 output minutes) | Total direct cost (Compute + Review + Revisions) $\le ₹24.00\text{/minute}$ ($>40\%$ gross margin). | If delivery cost $> ₹24$: Automated pipeline is insufficient; conclude business experiment. |
| **Gate 4: Commercial Repeatability** | Pilot Conclusion | Pilot customer commits to a paid contract for a second batch at $\ge ₹40\text{/minute}$. | If customer churns post-pilot: Workflow lacks retention; halt startup roadmap. |

---

## 5. Execution Timeline

1. **Step 1: Protocol Freeze**: Lock rubric, event definitions, and scoring forms. *(Completed)*
2. **Step 2: 3-Video Blind Benchmark**: Process identical test lectures and collect blind educator ratings.
3. **Step 3: 10 Buyer Interviews**: Conduct interviews, logging actual historical spend and purchasing authority.
4. **Step 4: Paid Pilot (Contingent on Gates 1 & 2)**: Execute 180-minute batch, logging all compute and human review minutes.
5. **Step 5: Publish Final Empirical Report**: Present all data, cataloged errors, exact costs, and conjunctive verdict.
