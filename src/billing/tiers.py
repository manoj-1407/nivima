"""
Nivima Subscription Tiers & Quota Management.
Defines pricing tiers, feature gates, resolution caps, and watermark rules.
"""

from dataclasses import dataclass
from enum import Enum


class PlanType(str, Enum):
    FREE_EXPLORER = "free_explorer"
    CREATOR_PRO = "creator_pro"
    STUDIO_TEAM = "studio_team"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class TierLimits:
    plan_name: str
    price_inr_month: int
    monthly_minutes: int
    max_resolution: str
    max_fps: int
    watermark_required: bool
    voice_cloning_allowed: bool
    max_clone_profiles: int
    persona_voices_allowed: bool
    priority_queue: bool
    api_access: bool


TIER_CONFIG: dict[PlanType, TierLimits] = {
    PlanType.FREE_EXPLORER: TierLimits(
        plan_name="Explorer",
        price_inr_month=0,
        monthly_minutes=3,
        max_resolution="1280x720",
        max_fps=30,
        watermark_required=True,
        voice_cloning_allowed=False,
        max_clone_profiles=0,
        persona_voices_allowed=True,
        priority_queue=False,
        api_access=False,
    ),
    PlanType.CREATOR_PRO: TierLimits(
        plan_name="Creator Pro",
        price_inr_month=1499,
        monthly_minutes=60,
        max_resolution="1920x1080",
        max_fps=60,
        watermark_required=False,
        voice_cloning_allowed=True,
        max_clone_profiles=3,
        persona_voices_allowed=True,
        priority_queue=True,
        api_access=False,
    ),
    PlanType.STUDIO_TEAM: TierLimits(
        plan_name="Studio & Team",
        price_inr_month=4999,
        monthly_minutes=300,
        max_resolution="3840x2160",
        max_fps=60,
        watermark_required=False,
        voice_cloning_allowed=True,
        max_clone_profiles=999,
        persona_voices_allowed=True,
        priority_queue=True,
        api_access=True,
    ),
    PlanType.ENTERPRISE: TierLimits(
        plan_name="Enterprise Sovereign",
        price_inr_month=150000,
        monthly_minutes=999999,
        max_resolution="3840x2160",
        max_fps=120,
        watermark_required=False,
        voice_cloning_allowed=True,
        max_clone_profiles=9999,
        persona_voices_allowed=True,
        priority_queue=True,
        api_access=True,
    ),
}


def get_tier_limits(plan: PlanType | str) -> TierLimits:
    if isinstance(plan, str):
        try:
            plan = PlanType(plan.lower())
        except ValueError:
            plan = PlanType.FREE_EXPLORER
    return TIER_CONFIG.get(plan, TIER_CONFIG[PlanType.FREE_EXPLORER])


def validate_job_against_tier(plan: PlanType | str, video_duration_seconds: float, resolution: str) -> tuple[bool, str | None]:
    limits = get_tier_limits(plan)
    duration_mins = video_duration_seconds / 60.0

    if duration_mins > limits.monthly_minutes:
        return False, f"Video duration ({duration_mins:.1f}m) exceeds {limits.plan_name} allowance ({limits.monthly_minutes}m)."

    return True, None
