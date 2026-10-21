"""Unit tests for Patent Pillar 2: Biomechanical Kinematic Viseme PLL."""
from src.alignment.biomechanical_pll import AnatomicalLimits, BiomechanicalVisemePLL


def test_pll_initialization():
    pll = BiomechanicalVisemePLL(fps=30.0)
    assert pll.dt == 1.0 / 30.0
    assert pll.state.jaw_displacement_mm == 0.0


def test_jaw_velocity_and_acceleration_clamping():
    limits = AnatomicalLimits(
        max_jaw_displacement_mm=20.0,
        max_jaw_velocity_mm_s=100.0,
        max_jaw_acceleration_mm_s2=1500.0,
    )
    pll = BiomechanicalVisemePLL(fps=30.0, limits=limits)

    # Apply instantaneous full step response (unphysical acoustic spike)
    state = pll.filter_phoneme_impulse(
        target_jaw_aperture_normalized=1.0,
        target_lip_spread_normalized=0.5,
        acoustic_energy_db=0.0,
        acoustic_timestamp_ms=33.3,
        video_frame_timestamp_ms=33.3,
    )

    # Velocity must NOT exceed physiological bounds
    assert abs(state.jaw_velocity_mm_s) <= limits.max_jaw_velocity_mm_s
    assert abs(state.jaw_acceleration_mm_s2) <= limits.max_jaw_acceleration_mm_s2
    assert state.jaw_displacement_mm <= limits.max_jaw_displacement_mm
    assert state.is_phase_locked is True


def test_batch_sequence_smoothing():
    pll = BiomechanicalVisemePLL(fps=24.0)
    # Noisy, jumping apertures
    noisy_inputs = [0.1, 0.9, 0.1, 0.9, 0.2]
    spreads = [0.2, 0.5, 0.2, 0.6, 0.3]
    energies = [-10.0, -5.0, -20.0, 0.0, -15.0]

    states = pll.batch_filter_sequence(noisy_inputs, spreads, energies)
    assert len(states) == 5

    # Check that displacements transition smoothly without instantaneous jumps
    for i in range(1, len(states)):
        step_diff = abs(states[i].jaw_displacement_mm - states[i - 1].jaw_displacement_mm)
        # Max displacement change in one frame (dt = 1/24 s, max_v = 120 mm/s) is 5 mm
        assert step_diff <= 5.5
