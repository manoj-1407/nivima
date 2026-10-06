PHONEME_TO_VISEME: dict[str, str] = {
    # Bilabial stops and nasals — lips fully closed
    "p": "bilabial_closure",
    "b": "bilabial_closure",
    "m": "bilabial_closure",
    "ph": "bilabial_aspirated",
    "bh": "bilabial_aspirated",

    # Labiodental fricatives — lower lip touches upper teeth
    "f": "labiodental",
    "v": "labiodental",

    # Dental fricatives — tongue near teeth
    "th": "dental",
    "dh": "dental",
    "th_asp": "dental_aspirated",
    "dh_asp": "dental_aspirated",

    # Alveolar stops — tongue on alveolar ridge
    "t": "alveolar",
    "d": "alveolar",
    "n": "alveolar",
    "s": "alveolar",
    "z": "alveolar",
    "l": "alveolar",
    "r": "alveolar",
    "th_dental": "dental_aspirated",

    # Retroflex — tongue curled back (Indian languages specifically)
    "tt": "retroflex",       # ट (Hindi), ట (Telugu)
    "dd": "retroflex",       # ड (Hindi), డ (Telugu)
    "nn": "retroflex",       # ण (Hindi), ణ (Telugu)
    "rr": "retroflex",       # ற (Tamil alveolar trill)
    "ll": "retroflex",       # ள (Tamil retroflex lateral)
    "zh": "retroflex",       # ழ (Tamil retroflex approximant — unique to Tamil)
    "tt_asp": "retroflex",   # ठ aspirated retroflex

    # Palatal — tongue on hard palate
    "ch": "palatal",
    "jh": "palatal",
    "sh": "palatal",
    "y": "palatal",
    "ch_asp": "palatal_aspirated",

    # Velar — tongue on soft palate
    "k": "velar",
    "g": "velar",
    "ng": "velar",
    "kh": "velar_aspirated",
    "gh": "velar_aspirated",

    # Glottal
    "h": "glottal",

    # Vowels — open wide
    "aa": "open_wide",
    "ah": "open_wide",
    "a": "open_wide",

    # Vowels — mid open
    "ae": "mid_open",
    "eh": "mid_open",
    "e": "mid_open",

    # Vowels — spread
    "ee": "spread",
    "ih": "spread",
    "iy": "spread",
    "i": "spread",

    # Vowels — rounded
    "oo": "rounded",
    "uw": "rounded",
    "u": "rounded",
    "ow": "rounded",

    # Vowels — central schwa
    "er": "central",
    "ax": "central",
    "schwa": "central",

    # Silence and boundary markers
    "sil": "silence",
    "sp": "silence",
    "": "silence",
}

# Blendshape weights per viseme for 3DMM rendering (Phase 3)
VISEME_TO_BLENDWEIGHTS: dict[str, dict[str, float]] = {
    "bilabial_closure": {
        "jaw_open": 0.0,
        "lip_corner_puller": 0.0,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.0,
        "lip_pressor": 0.9,
        "lip_tightener": 0.3,
        "cheek_raiser": 0.0,
    },
    "bilabial_aspirated": {
        "jaw_open": 0.1,
        "lip_corner_puller": 0.0,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.1,
        "lip_pressor": 0.6,
        "lip_tightener": 0.2,
        "cheek_raiser": 0.0,
    },
    "labiodental": {
        "jaw_open": 0.2,
        "lip_corner_puller": 0.1,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.3,
        "lip_pressor": 0.0,
        "lip_tightener": 0.4,
        "cheek_raiser": 0.0,
    },
    "dental": {
        "jaw_open": 0.2,
        "lip_corner_puller": 0.2,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.0,
        "lip_tightener": 0.3,
        "cheek_raiser": 0.0,
    },
    "alveolar": {
        "jaw_open": 0.25,
        "lip_corner_puller": 0.1,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.0,
        "lip_tightener": 0.2,
        "cheek_raiser": 0.0,
    },
    "retroflex": {
        "jaw_open": 0.3,
        "lip_corner_puller": 0.1,
        "upper_lip_raiser": 0.15,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.0,
        "lip_tightener": 0.5,
        "cheek_raiser": 0.2,  # tongue curl creates visible cheek tension
    },
    "palatal": {
        "jaw_open": 0.3,
        "lip_corner_puller": 0.3,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.0,
        "lip_tightener": 0.2,
        "cheek_raiser": 0.1,
    },
    "palatal_aspirated": {
        "jaw_open": 0.35,
        "lip_corner_puller": 0.25,
        "upper_lip_raiser": 0.15,
        "lower_lip_depressor": 0.25,
        "lip_pressor": 0.0,
        "lip_tightener": 0.15,
        "cheek_raiser": 0.1,
    },
    "velar": {
        "jaw_open": 0.3,
        "lip_corner_puller": 0.1,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.0,
        "lip_tightener": 0.15,
        "cheek_raiser": 0.0,
    },
    "velar_aspirated": {
        "jaw_open": 0.35,
        "lip_corner_puller": 0.1,
        "upper_lip_raiser": 0.05,
        "lower_lip_depressor": 0.25,
        "lip_pressor": 0.0,
        "lip_tightener": 0.1,
        "cheek_raiser": 0.0,
    },
    "glottal": {
        "jaw_open": 0.4,
        "lip_corner_puller": 0.0,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.3,
        "lip_pressor": 0.0,
        "lip_tightener": 0.0,
        "cheek_raiser": 0.0,
    },
    "open_wide": {
        "jaw_open": 0.9,
        "lip_corner_puller": 0.3,
        "upper_lip_raiser": 0.2,
        "lower_lip_depressor": 0.6,
        "lip_pressor": 0.0,
        "lip_tightener": 0.0,
        "cheek_raiser": 0.0,
    },
    "mid_open": {
        "jaw_open": 0.55,
        "lip_corner_puller": 0.2,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.35,
        "lip_pressor": 0.0,
        "lip_tightener": 0.0,
        "cheek_raiser": 0.0,
    },
    "spread": {
        "jaw_open": 0.2,
        "lip_corner_puller": 0.7,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.1,
        "lip_pressor": 0.0,
        "lip_tightener": 0.2,
        "cheek_raiser": 0.1,
    },
    "rounded": {
        "jaw_open": 0.4,
        "lip_corner_puller": 0.0,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.3,
        "lip_tightener": 0.6,
        "cheek_raiser": 0.0,
    },
    "central": {
        "jaw_open": 0.3,
        "lip_corner_puller": 0.1,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.15,
        "lip_pressor": 0.0,
        "lip_tightener": 0.1,
        "cheek_raiser": 0.0,
    },
    "silence": {
        "jaw_open": 0.0,
        "lip_corner_puller": 0.0,
        "upper_lip_raiser": 0.0,
        "lower_lip_depressor": 0.0,
        "lip_pressor": 0.0,
        "lip_tightener": 0.1,
        "cheek_raiser": 0.0,
    },
    "dental_aspirated": {
        "jaw_open": 0.25,
        "lip_corner_puller": 0.15,
        "upper_lip_raiser": 0.1,
        "lower_lip_depressor": 0.2,
        "lip_pressor": 0.0,
        "lip_tightener": 0.25,
        "cheek_raiser": 0.0,
    },
}


def get_viseme(phoneme: str) -> str:
    return PHONEME_TO_VISEME.get(phoneme.lower(), "silence")


def get_blend_weights(viseme: str) -> dict[str, float]:
    return VISEME_TO_BLENDWEIGHTS.get(viseme, VISEME_TO_BLENDWEIGHTS["silence"])
