"""
Quality gate — nothing gets delivered below minimum acceptable quality.

The Kanguva problem happened because someone delivered bad output.
This module prevents that.

Three tiers:
  PASS     — deliver immediately
  REVIEW   — deliver with warning + flag for manual QC
  BLOCK    — do not deliver, notify user, offer options

Options when BLOCK:
  1. Revert to audio-only dubbing (no visual lip sync) — always looks acceptable
  2. Re-queue with different parameters
  3. Partial delivery — deliver good segments, flag bad ones
"""

from dataclasses import dataclass
from enum import Enum
from src.qc.scorer import QCScore, THRESHOLDS
import structlog

log = structlog.get_logger()


class GateDecision(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    BLOCK = "block"


@dataclass
class GateResult:
    decision: GateDecision
    reason: str
    can_deliver: bool
    fallback_available: bool
    fallback_description: str
    scores: dict
    recommendations: list[str]


# Stricter than scorer thresholds — gate is more conservative
GATE_THRESHOLDS = {
    "syncnet_block": 3.5,     # below this: never deliver
    "syncnet_review": 5.5,    # below this: deliver with warning
    "syncnet_pass": 7.0,      # above this: deliver confidently

    "csim_block": 0.70,       # identity too far from original
    "csim_review": 0.80,

    "psnr_block": 25.0,       # compositing is visibly broken
    "psnr_review": 32.0,

    "temporal_block": 15.0,   # severe flickering
    "temporal_review": 10.0,

    "revert_pct_block": 0.50, # >50% frames reverted = reanimation failed overall
    "revert_pct_review": 0.30,
}


def evaluate_gate(score: QCScore) -> GateResult:
    reasons = []
    block_reasons = []
    review_reasons = []
    recommendations = []

    # Check each metric
    if score.syncnet_score < GATE_THRESHOLDS["syncnet_block"]:
        block_reasons.append(
            f"SyncNet {score.syncnet_score:.2f} below block threshold "
            f"{GATE_THRESHOLDS['syncnet_block']}"
        )
        recommendations.append("Audio-visual sync is too poor. Consider audio-only dubbing.")

    elif score.syncnet_score < GATE_THRESHOLDS["syncnet_review"]:
        review_reasons.append(f"SyncNet {score.syncnet_score:.2f} — marginal sync quality")
        recommendations.append("Sync is acceptable but not great. Review visually.")

    if score.csim_score < GATE_THRESHOLDS["csim_block"]:
        block_reasons.append(
            f"CSIM {score.csim_score:.3f} — face identity not preserved"
        )
        recommendations.append("The person's face is not recognizable. Do not deliver.")

    elif score.csim_score < GATE_THRESHOLDS["csim_review"]:
        review_reasons.append(f"CSIM {score.csim_score:.3f} — identity slightly degraded")

    if score.psnr_non_lip < GATE_THRESHOLDS["psnr_block"]:
        block_reasons.append(
            f"PSNR {score.psnr_non_lip:.1f}dB — compositing visibly broken"
        )
        recommendations.append("Non-lip regions are corrupted. Compositing failed.")

    elif score.psnr_non_lip < GATE_THRESHOLDS["psnr_review"]:
        review_reasons.append(f"PSNR {score.psnr_non_lip:.1f}dB — slight compositing issues")

    if score.temporal_variance > GATE_THRESHOLDS["temporal_block"]:
        block_reasons.append(
            f"Temporal variance {score.temporal_variance:.1f} — severe flickering"
        )
        recommendations.append(
            "Visible flickering detected. Apply stronger temporal smoothing or revert."
        )

    elif score.temporal_variance > GATE_THRESHOLDS["temporal_review"]:
        review_reasons.append(f"Temporal variance {score.temporal_variance:.1f} — mild flickering")

    if score.frames_total > 0:
        revert_pct = score.frames_reverted / score.frames_total
        if revert_pct > GATE_THRESHOLDS["revert_pct_block"]:
            block_reasons.append(
                f"{revert_pct:.0%} of frames auto-reverted — reanimation largely failed"
            )
            recommendations.append(
                "Reanimation failed on most frames. Deliver audio-only dubbed version."
            )
        elif revert_pct > GATE_THRESHOLDS["revert_pct_review"]:
            review_reasons.append(f"{revert_pct:.0%} frames reverted — partial reanimation")

    if block_reasons:
        return GateResult(
            decision=GateDecision.BLOCK,
            reason="; ".join(block_reasons),
            can_deliver=False,
            fallback_available=True,
            fallback_description=(
                "Audio-only dubbed version available — correct translation and "
                "voice cloning, no visual lip sync. This always looks acceptable."
            ),
            scores=_score_summary(score),
            recommendations=recommendations
        )

    if review_reasons:
        return GateResult(
            decision=GateDecision.REVIEW,
            reason="; ".join(review_reasons),
            can_deliver=True,
            fallback_available=True,
            fallback_description="Audio-only version also available if visual quality is unacceptable.",
            scores=_score_summary(score),
            recommendations=recommendations or ["Review the video before sharing publicly."]
        )

    return GateResult(
        decision=GateDecision.PASS,
        reason="All quality metrics within acceptable range",
        can_deliver=True,
        fallback_available=False,
        fallback_description="",
        scores=_score_summary(score),
        recommendations=[]
    )


def evaluate_job_gate(chunk_scores: list[QCScore]) -> dict:
    """
    Aggregate quality gate across all chunks in a job.
    A job passes if ≥80% of chunks pass or review.
    A job is blocked if >20% of chunks are blocked.
    """
    if not chunk_scores:
        return {"decision": "pass", "note": "No scores to evaluate"}

    results = [evaluate_gate(s) for s in chunk_scores]
    blocked = sum(1 for r in results if r.decision == GateDecision.BLOCK)
    review = sum(1 for r in results if r.decision == GateDecision.REVIEW)
    passed = sum(1 for r in results if r.decision == GateDecision.PASS)
    total = len(results)

    blocked_pct = blocked / total
    review_pct = review / total

    log.info("job_quality_gate",
             total=total,
             passed=passed,
             review=review,
             blocked=blocked,
             blocked_pct=round(blocked_pct, 2))

    if blocked_pct > 0.20:
        return {
            "decision": GateDecision.BLOCK,
            "blocked_chunks": blocked,
            "review_chunks": review,
            "passed_chunks": passed,
            "total_chunks": total,
            "message": (
                f"{blocked_pct:.0%} of chunks failed quality gate. "
                f"Delivering audio-only version instead of reanimated version."
            ),
            "action": "deliver_audio_only"
        }

    if review_pct > 0.30 or blocked_pct > 0:
        return {
            "decision": GateDecision.REVIEW,
            "blocked_chunks": blocked,
            "review_chunks": review,
            "passed_chunks": passed,
            "total_chunks": total,
            "message": "Video delivered with quality warnings. Manual review recommended.",
            "action": "deliver_with_warning"
        }

    return {
        "decision": GateDecision.PASS,
        "blocked_chunks": 0,
        "review_chunks": review,
        "passed_chunks": passed,
        "total_chunks": total,
        "message": "Quality gate passed. Video ready for delivery.",
        "action": "deliver"
    }


def _score_summary(score: QCScore) -> dict:
    return {
        "syncnet": score.syncnet_score,
        "csim": score.csim_score,
        "psnr_non_lip": score.psnr_non_lip,
        "temporal_variance": score.temporal_variance,
        "frames_reverted": score.frames_reverted,
        "frames_total": score.frames_total,
    }
