import pytest
from unittest.mock import patch, MagicMock
from src.scene.classifier import classify_face, Decision
from src.scene.face_analyzer import FaceAnalysis


def _analysis(**kwargs):
    defaults = dict(
        face_count=1, confidence=0.92,
        yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
        occlusion_score=0.05, face_area_pct=0.08,
        face_bbox=None, mouth_landmarks=[]
    )
    defaults.update(kwargs)
    return FaceAnalysis(**defaults)


def test_no_face():
    result = classify_face(_analysis(face_count=0, confidence=0.0))
    assert result.decision == Decision.NO_FACE
    assert result.should_reanimate is False


def test_frontal_clear():
    result = classify_face(_analysis(yaw_deg=5.0, occlusion_score=0.03))
    assert result.decision == Decision.FRONTAL_CLEAR
    assert result.should_reanimate is True
    assert result.expected_quality > 0.8


def test_partial_visible():
    result = classify_face(_analysis(yaw_deg=30.0, occlusion_score=0.05))
    assert result.decision == Decision.PARTIAL_VISIBLE
    assert result.should_reanimate is True


def test_profile():
    result = classify_face(_analysis(yaw_deg=55.0))
    assert result.decision == Decision.PROFILE
    assert result.should_reanimate is False


def test_occluded():
    result = classify_face(_analysis(occlusion_score=0.65))
    assert result.decision == Decision.OCCLUDED
    assert result.should_reanimate is False


def test_multi_face():
    result = classify_face(_analysis(face_count=3))
    assert result.decision == Decision.MULTI_FACE
    assert result.should_reanimate is False


def test_low_res():
    result = classify_face(_analysis(face_area_pct=0.002))
    assert result.decision == Decision.LOW_RES
    assert result.should_reanimate is False


def test_low_confidence_falls_back_to_profile():
    result = classify_face(_analysis(confidence=0.4, yaw_deg=10.0))
    assert result.decision == Decision.PROFILE
    assert result.should_reanimate is False


def test_quality_decreases_with_yaw():
    frontal = classify_face(_analysis(yaw_deg=2.0))
    partial = classify_face(_analysis(yaw_deg=18.0))
    assert frontal.expected_quality >= partial.expected_quality
