from src.translation.phoneme_map import (
    PHONEME_TO_VISEME,
    VISEME_TO_BLENDWEIGHTS,
    get_blend_weights,
    get_viseme,
)


def test_bilabial_phonemes():
    assert get_viseme("p") == "bilabial_closure"
    assert get_viseme("b") == "bilabial_closure"
    assert get_viseme("m") == "bilabial_closure"


def test_retroflex_indian_phonemes():
    assert get_viseme("tt") == "retroflex"
    assert get_viseme("dd") == "retroflex"
    assert get_viseme("nn") == "retroflex"
    assert get_viseme("zh") == "retroflex"   # Tamil ழ
    assert get_viseme("ll") == "retroflex"   # Tamil ள
    assert get_viseme("rr") == "retroflex"   # Tamil ற


def test_vowels():
    assert get_viseme("aa") == "open_wide"
    assert get_viseme("ee") == "spread"
    assert get_viseme("oo") == "rounded"
    assert get_viseme("er") == "central"


def test_silence():
    assert get_viseme("sil") == "silence"
    assert get_viseme("sp") == "silence"
    assert get_viseme("") == "silence"


def test_unknown_phoneme_defaults_to_silence():
    assert get_viseme("xyz_unknown") == "silence"


def test_case_insensitive():
    assert get_viseme("P") == get_viseme("p")
    assert get_viseme("AA") == get_viseme("aa")


def test_all_visemes_have_blend_weights():
    for viseme in VISEME_TO_BLENDWEIGHTS:
        weights = get_blend_weights(viseme)
        assert "jaw_open" in weights
        assert "lip_tightener" in weights
        assert all(0.0 <= v <= 1.0 for v in weights.values()), \
            f"Weight out of range for viseme {viseme}"


def test_silence_has_minimal_jaw_open():
    w = get_blend_weights("silence")
    assert w["jaw_open"] == 0.0


def test_open_wide_has_high_jaw_open():
    w = get_blend_weights("open_wide")
    assert w["jaw_open"] > 0.7


def test_bilabial_has_high_lip_pressor():
    w = get_blend_weights("bilabial_closure")
    assert w["lip_pressor"] > 0.7
    assert w["jaw_open"] == 0.0


def test_retroflex_has_cheek_raiser():
    w = get_blend_weights("retroflex")
    assert w["cheek_raiser"] > 0.0


def test_rounded_has_high_lip_tightener():
    w = get_blend_weights("rounded")
    assert w["lip_tightener"] > 0.5


def test_spread_has_high_lip_corner_puller():
    w = get_blend_weights("spread")
    assert w["lip_corner_puller"] > 0.5


def test_all_phonemes_resolve_to_valid_viseme():
    for phoneme in PHONEME_TO_VISEME:
        viseme = get_viseme(phoneme)
        assert viseme in VISEME_TO_BLENDWEIGHTS, \
            f"Phoneme '{phoneme}' maps to '{viseme}' which has no blend weights"
