from dataclasses import dataclass
from enum import Enum
import numpy as np
import structlog
from src.scene.face_analyzer import FaceAnalysis, analyze_frame, sample_frames

log = structlog.get_logger()


class Decision(str, Enum):
    FRONTAL_CLEAR = "FRONTAL_CLEAR"
    PARTIAL_VISIBLE = "PARTIAL_VISIBLE"
    PROFILE = "PROFILE"
    OCCLUDED = "OCCLUDED"
    MULTI_FACE = "MULTI_FACE"
    NO_FACE = "NO_FACE"
    LOW_RES = "LOW_RES"


REANIMATES = {Decision.FRONTAL_CLEAR, Decision.PARTIAL_VISIBLE}

T = {
    "yaw_frontal": 20.0,
    "yaw_partial": 40.0,
    "occlusion_frontal": 0.10,
    "occlusion_partial": 0.40,
    "min_confidence": 0.65,
    "min_face_area": 0.005,
}

DECISION_PRIORITY = [
    Decision.LOW_RES,
    Decision.OCCLUDED,
    Decision.PROFILE,
    Decision.MULTI_FACE,
    Decision.PARTIAL_VISIBLE,
    Decision.FRONTAL_CLEAR,
    Decision.NO_FACE,
]


@dataclass
class SceneClassification:
    decision: Decision
    confidence: float
    yaw_deg: float
    pitch_deg: float
    occlusion_score: float
    face_count: int
    face_area_pct: float
    expected_quality: float
    should_reanimate: bool

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "yaw_deg": self.yaw_deg,
            "pitch_deg": self.pitch_deg,
            "occlusion_score": self.occlusion_score,
            "face_count": self.face_count,
            "face_area_pct": self.face_area_pct,
            "expected_quality": self.expected_quality,
            "should_reanimate": self.should_reanimate,
        }


def classify_face(analysis: FaceAnalysis) -> SceneClassification:
    if analysis.face_count == 0:
        return _make(Decision.NO_FACE, analysis, 0.0)

    if analysis.face_count > 1:
        return _make(Decision.MULTI_FACE, analysis, 0.3)

    if analysis.face_area_pct < T["min_face_area"]:
        return _make(Decision.LOW_RES, analysis, 0.0)

    if analysis.confidence < T["min_confidence"]:
        return _make(Decision.PROFILE, analysis, 0.1)

    abs_yaw = abs(analysis.yaw_deg)

    if abs_yaw > T["yaw_partial"]:
        return _make(Decision.PROFILE, analysis, 0.1)

    if analysis.occlusion_score > T["occlusion_partial"]:
        return _make(Decision.OCCLUDED, analysis, 0.2)

    if abs_yaw <= T["yaw_frontal"] and analysis.occlusion_score <= T["occlusion_frontal"]:
        q = 0.88 - (abs_yaw / T["yaw_frontal"]) * 0.08
        return _make(Decision.FRONTAL_CLEAR, analysis, round(q, 3))

    q = 0.62 - (abs_yaw / T["yaw_partial"]) * 0.15
    return _make(Decision.PARTIAL_VISIBLE, analysis, round(max(0.3, q), 3))


def classify_chunk(frames_dir: str) -> SceneClassification:
    frames = sample_frames(frames_dir, max_samples=8)

    if not frames:
        return SceneClassification(
            decision=Decision.NO_FACE, confidence=1.0,
            yaw_deg=0, pitch_deg=0, occlusion_score=0,
            face_count=0, face_area_pct=0,
            expected_quality=0, should_reanimate=False
        )

    analyses = [analyze_frame(f) for f in frames]
    classifications = [classify_face(a) for a in analyses]

    decisions_seen = {c.decision for c in classifications}
    for decision in DECISION_PRIORITY:
        if decision in decisions_seen:
            worst = next(c for c in classifications if c.decision == decision)
            return worst

    return classifications[0]


def _make(decision: Decision, analysis: FaceAnalysis, quality: float) -> SceneClassification:
    return SceneClassification(
        decision=decision,
        confidence=analysis.confidence,
        yaw_deg=analysis.yaw_deg,
        pitch_deg=analysis.pitch_deg,
        occlusion_score=analysis.occlusion_score,
        face_count=analysis.face_count,
        face_area_pct=analysis.face_area_pct,
        expected_quality=quality,
        should_reanimate=decision in REANIMATES
    )
