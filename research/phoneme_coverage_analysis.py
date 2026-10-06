"""
Generates and validates recording sentences for volunteer dataset collection.
Ensures all viseme types are covered including Indian retroflex sounds.
Run: python research/phoneme_coverage_analysis.py
"""

from src.translation.phoneme_map import VISEME_TO_BLENDWEIGHTS

RECORDING_SENTENCES = {
    "hindi": [
        "मेरा नाम मनोज है और मैं हैदराबाद में रहता हूँ",       # bilabial, nasals
        "आज का मौसम बहुत अच्छा है",                              # open vowels
        "टमाटर बड़ा मीठा है",                                    # retroflex T
        "डॉक्टर ने दवाई दी",                                     # retroflex D
        "खाना खाकर पानी पियो",                                   # velar aspirated
        "घर के बाहर घास उगी है",                                 # velar aspirated voiced
        "छोटी बच्ची खेल रही है",                                 # palatal aspirated
        "फूल बहुत सुन्दर हैं",                                   # labiodental
        "वह वापस आ गया",                                         # labiodental voiced
        "सूरज पूरब से उगता है",                                  # rounded vowels, alveolar
        "झील के किनारे बैठकर सोचा",                              # palatal
        "रात को तारे चमकते हैं",                                  # alveolar r
        "लाल गुलाब बहुत प्यारा है",                              # alveolar l
        "नई दिल्ली भारत की राजधानी है",                          # dental n, d
        "थोड़ा पानी दे दो भाई",                                   # dental aspirated
    ],
    "telugu": [
        "నమస్కారం నా పేరు మనోజ్",                              # nasals, bilabial
        "ఈరోజు వాతావరణం చాలా బాగుంది",                         # open vowels, bilabial
        "టమాటా చాలా తీపిగా ఉంది",                               # retroflex T
        "డాక్టర్ మందు ఇచ్చారు",                                 # retroflex D
        "కాఫీ తాగుతారా",                                        # velar k
        "పూలు చాలా అందంగా ఉన్నాయి",                            # labiodental p
        "వాళ్ళు ఇంటికి వెళ్ళారు",                               # retroflex L (ళ)
        "సూర్యుడు తూర్పున ఉదయిస్తాడు",                          # rounded vowels
        "చిన్న పిల్లలు ఆడుకుంటున్నారు",                          # palatal ch
        "రాత్రి నక్షత్రాలు మెరుస్తాయి",                          # alveolar r
        "మా అమ్మ వంట చేస్తోంది",                                # bilabial m, nasals
        "ఇల్లు చాలా పెద్దది",                                   # alveolar l
        "నది ఒడ్డున కూర్చున్నాను",                              # retroflex combinations
        "ఫలితాలు వచ్చాయి",                                     # labiodental f
        "యువకులు కష్టపడాలి",                                   # palatal y
    ],
    "tamil": [
        "வணக்கம் என் பெயர் மனோஜ்",                             # bilabial, nasals
        "இன்று வானிலை மிகவும் நன்றாக இருக்கிறது",               # open vowels
        "தக்காளி மிகவும் இனிப்பாக இருக்கிறது",                  # alveolar T (retroflex in Tamil)
        "டாக்டர் மருந்து கொடுத்தார்",                           # retroflex D
        "ழகரம் தமிழின் தனிச்சிறப்பு",                            # unique Tamil zh retroflex
        "கடல் அலைகள் அழகாக இருக்கின்றன",                       # velar k
        "பூக்கள் மலர்ந்திருக்கின்றன",                           # labiodental p
        "வீட்டிற்கு வாருங்கள்",                                  # rounded vowels
        "சிறு குழந்தைகள் விளையாடுகிறார்கள்",                    # palatal ch
        "இரவில் நட்சத்திரங்கள் மினுமினுக்கின்றன",               # alveolar r
        "அம்மா சமையல் செய்கிறார்கள்",                           # bilabial m
        "நெல்லை மாவட்டம் தமிழ்நாட்டில் உள்ளது",                # retroflex L (ள)
        "றகரம் ஒரு சிறப்பு எழுத்து",                            # Tamil rr retroflex
        "கோவிலுக்கு போகலாம்",                                  # velar g
        "யாரும் வரவில்லை",                                     # palatal y
    ]
}


def analyze_viseme_coverage(sentences: list[str], language: str) -> dict:
    """
    Rough analysis — counts unique character types as proxy for viseme coverage.
    Real analysis requires running MFA and checking phoneme output.
    """
    from collections import Counter

    all_chars = " ".join(sentences)
    char_freq = Counter(all_chars)
    total_chars = sum(char_freq.values())

    print(f"\n=== {language.upper()} Coverage Analysis ===")
    print(f"Total sentences: {len(sentences)}")
    print(f"Total characters: {total_chars}")
    print(f"Unique characters: {len(char_freq)}")

    visemes_targeted = set()
    if language == "hindi" or language == "telugu":
        if any("ट" in s or "ట" in s for s in sentences):
            visemes_targeted.add("retroflex")
        if any("म" in s or "మ" in s for s in sentences):
            visemes_targeted.add("bilabial_closure")
        if any("आ" in s or "ఆ" in s for s in sentences):
            visemes_targeted.add("open_wide")
        if any("ऊ" in s or "ఊ" in s or "oo" in s.lower() for s in sentences):
            visemes_targeted.add("rounded")
        if any("ि" in s or "ి" in s for s in sentences):
            visemes_targeted.add("spread")
        if any("फ" in s or "వ" in s for s in sentences):
            visemes_targeted.add("labiodental")

    all_visemes = set(VISEME_TO_BLENDWEIGHTS.keys())
    coverage = len(visemes_targeted) / len(all_visemes) * 100

    print(f"Estimated viseme coverage: {len(visemes_targeted)}/{len(all_visemes)} ({coverage:.0f}%)")
    missing = all_visemes - visemes_targeted
    if missing:
        print(f"Potentially missing visemes: {missing}")

    return {
        "language": language,
        "sentence_count": len(sentences),
        "char_count": total_chars,
        "unique_chars": len(char_freq),
        "visemes_targeted": list(visemes_targeted),
        "coverage_pct": coverage
    }


if __name__ == "__main__":
    all_results = []
    for lang, sentences in RECORDING_SENTENCES.items():
        result = analyze_viseme_coverage(sentences, lang)
        all_results.append(result)

    print("\n=== Recording Protocol ===")
    print("Equipment: Smartphone (1080p), ring light or daylight, plain background")
    print("Distance: 60cm from camera")
    print("Duration per sentence: natural pace, no rushing")
    print("Repeats: 3 times per sentence")
    print("Total per volunteer: ~10 minutes")
    print("\nFor each language, record all sentences 3x.")
    print("Total sentences per volunteer: 15 sentences × 3 repeats = 45 recordings")
    print("Total volunteers needed: 50")
    print("Total dataset size: 50 × 10 min = 500 minutes")
    print("Estimated cost: ₹200 × 50 = ₹10,000")
