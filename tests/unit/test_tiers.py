"""Tests for subscription tiers and quota validation."""
from src.billing.tiers import PlanType, get_tier_limits, validate_job_against_tier


def test_free_explorer_limits():
    limits = get_tier_limits(PlanType.FREE_EXPLORER)
    assert limits.price_inr_month == 0
    assert limits.monthly_minutes == 3
    assert limits.watermark_required is True
    assert limits.voice_cloning_allowed is False


def test_creator_pro_limits():
    limits = get_tier_limits(PlanType.CREATOR_PRO)
    assert limits.price_inr_month == 1499
    assert limits.monthly_minutes == 60
    assert limits.watermark_required is False
    assert limits.voice_cloning_allowed is True
    assert limits.max_clone_profiles == 3


def test_studio_team_limits():
    limits = get_tier_limits(PlanType.STUDIO_TEAM)
    assert limits.price_inr_month == 4999
    assert limits.monthly_minutes == 300
    assert limits.api_access is True


def test_duration_validation():
    # 2-minute video is valid for Free Explorer (limit 3 min)
    valid, err = validate_job_against_tier(PlanType.FREE_EXPLORER, video_duration_seconds=120, resolution="1280x720")
    assert valid is True
    assert err is None

    # 10-minute video exceeds Free Explorer limit
    valid, err = validate_job_against_tier(PlanType.FREE_EXPLORER, video_duration_seconds=600, resolution="1280x720")
    assert valid is False
    assert "exceeds" in err
