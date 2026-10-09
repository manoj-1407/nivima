#!/usr/bin/env python3
"""
Nivima Volunteer Dataset Collection Tool
Records volunteers reading phoneme-balanced sentences for Indian face dataset.

Usage:
    python scripts/collect_volunteer_dataset.py \
        --volunteer-id V001 \
        --language te \
        --output ./data/volunteers/

Controls:
    SPACE = start/stop recording
    N     = next sentence
    R     = re-record current
    Q     = quit and save
"""

import argparse
import json
import os
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


SENTENCES = {
    "hi": [
        "मेरा नाम मनोज है और मैं हैदराबाद में रहता हूँ",
        "आज का मौसम बहुत अच्छा है और आसमान साफ है",
        "टमाटर बड़ा मीठा है और बाज़ार में मिलता है",
        "डॉक्टर ने दवाई दी और आराम करने को कहा",
        "खाना खाकर पानी पियो यह सेहत के लिए अच्छा है",
        "घर के बाहर घास उगी है और फूल खिले हैं",
        "छोटी बच्ची खेल रही है मैदान में",
        "फूल बहुत सुन्दर हैं और महक अच्छी है",
        "वह वापस आ गया लम्बी यात्रा के बाद",
        "सूरज पूरब से उगता है और पश्चिम में डूबता है",
        "झील के किनारे बैठकर सोचा और मन शांत हुआ",
        "रात को तारे चमकते हैं और चाँद उगता है",
        "लाल गुलाब बहुत प्यारा है और काँटे तीखे हैं",
        "नई दिल्ली भारत की राजधानी है और बड़ा शहर है",
        "थोड़ा पानी दे दो भाई बहुत प्यास लगी है",
    ],
    "te": [
        "నమస్కారం నా పేరు మనోజ్ మరియు నేను హైదరాబాద్ లో ఉంటాను",
        "ఈరోజు వాతావరణం చాలా బాగుంది మరియు ఆకాశం స్వచ్ఛంగా ఉంది",
        "టమాటా చాలా తీపిగా ఉంది మరియు మార్కెట్ లో దొరుకుతుంది",
        "డాక్టర్ మందు ఇచ్చారు మరియు విశ్రాంతి తీసుకోమని చెప్పారు",
        "కాఫీ తాగుతారా లేదా టీ తాగుతారా చెప్పండి",
        "పూలు చాలా అందంగా ఉన్నాయి మరియు సువాసన వస్తోంది",
        "వాళ్ళు ఇంటికి వెళ్ళారు చాలా దూరం నుండి వచ్చారు",
        "సూర్యుడు తూర్పున ఉదయిస్తాడు మరియు పడమటన అస్తమిస్తాడు",
        "చిన్న పిల్లలు ఆడుకుంటున్నారు మైదానంలో సంతోషంగా",
        "రాత్రి నక్షత్రాలు మెరుస్తాయి మరియు చంద్రుడు ఉదయిస్తాడు",
        "మా అమ్మ వంట చేస్తోంది మరియు వాసన చాలా బాగుంది",
        "ఇల్లు చాలా పెద్దది మరియు అందమైన తోట ఉంది",
        "నది ఒడ్డున కూర్చున్నాను మరియు చాలా సేపు ఆలోచించాను",
        "ఫలితాలు వచ్చాయి మరియు అందరూ సంతోషంగా ఉన్నారు",
        "యువకులు కష్టపడాలి అప్పుడే జీవితంలో విజయం వస్తుంది",
    ],
    "ta": [
        "வணக்கம் என் பெயர் மனோஜ் நான் ஹைதராபாத்தில் வசிக்கிறேன்",
        "இன்று வானிலை மிகவும் நன்றாக இருக்கிறது வானம் தெளிவாக உள்ளது",
        "தக்காளி மிகவும் இனிப்பாக இருக்கிறது சந்தையில் கிடைக்கிறது",
        "டாக்டர் மருந்து கொடுத்தார் ஓய்வு எடுக்கும்படி சொன்னார்",
        "ழகரம் தமிழின் தனிச்சிறப்பு உலகில் வேறெங்கும் இல்லை",
        "கடல் அலைகள் அழகாக இருக்கின்றன கரை மேல் மோதுகின்றன",
        "பூக்கள் மலர்ந்திருக்கின்றன நறுமணம் வீசுகிறது",
        "வீட்டிற்கு வாருங்கள் நாங்கள் காத்திருக்கிறோம்",
        "சிறு குழந்தைகள் விளையாடுகிறார்கள் மகிழ்ச்சியாக",
        "இரவில் நட்சத்திரங்கள் மினுமினுக்கின்றன நிலவு உதிக்கிறது",
        "அம்மா சமையல் செய்கிறார்கள் வாசனை நன்றாக வருகிறது",
        "நெல்லை மாவட்டம் தமிழ்நாட்டில் உள்ளது பலரும் அறிவார்கள்",
        "றகரம் ஒரு சிறப்பு எழுத்து தமிழில் மட்டும் உள்ளது",
        "கோவிலுக்கு போகலாம் வழிபாடு செய்யலாம் மனம் அமையும்",
        "யாரும் வரவில்லை ஆனால் நாங்கள் காத்திருந்தோம்",
    ],
}

RECORDING_INSTRUCTIONS = """
RECORDING INSTRUCTIONS
======================
- Sit facing the camera directly (no more than 20° angle)
- Ensure good lighting on your face (daylight or ring light)
- Keep background plain and light-colored
- Distance: 50-70cm from camera
- Speak at natural pace — not too fast, not too slow
- Record each sentence 3 times

Controls: SPACE=Record/Stop  N=Next  R=Redo  Q=Quit & Save
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--volunteer-id", required=True)
    parser.add_argument("--language", required=True, choices=list(SENTENCES.keys()))
    parser.add_argument("--output", default="./data/volunteers")
    args = parser.parse_args()

    sentences = SENTENCES[args.language]
    vol_dir = os.path.join(args.output, args.volunteer_id, args.language)
    os.makedirs(vol_dir, exist_ok=True)

    metadata = {
        "volunteer_id": args.volunteer_id,
        "language": args.language,
        "recordings": [],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    print(RECORDING_INSTRUCTIONS)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)

    sentence_idx = 0
    repeat_idx = 1
    is_recording = False
    writer = None
    recorded = {}

    print(f"\nStarting with volunteer {args.volunteer_id}, language: {args.language}")
    print(f"Total sentences: {len(sentences)}, 3 repeats each = {len(sentences) * 3} recordings\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()

        # Overlay UI
        h, w = display.shape[:2]
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)

        if sentence_idx < len(sentences):
            sentence = sentences[sentence_idx]
            status = "● RECORDING" if is_recording else "○ READY"
            color = (0, 0, 255) if is_recording else (0, 255, 0)

            cv2.putText(display, f"[{sentence_idx+1}/{len(sentences)}] Repeat {repeat_idx}/3",
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(display, status, (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Sentence (truncate if too long)
            display_sentence = sentence[:60] + "..." if len(sentence) > 60 else sentence
            cv2.putText(display, display_sentence, (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            progress_pct = len([k for k in recorded]) / (len(sentences) * 3)
            cv2.rectangle(display, (0, h-8), (int(w * progress_pct), h), (108, 99, 255), -1)

        else:
            cv2.putText(display, "All sentences recorded! Press Q to save.",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Nivima Dataset Collection", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord(' '):
            if not is_recording:
                rec_key = f"s{sentence_idx:02d}_r{repeat_idx}"
                video_path = os.path.join(vol_dir, f"{rec_key}.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                writer = cv2.VideoWriter(video_path, fourcc, 30,
                                         (int(cap.get(3)), int(cap.get(4))))
                is_recording = True
                print(f"  Recording: {rec_key}...")
            else:
                if writer:
                    writer.release()
                    writer = None
                is_recording = False
                rec_key = f"s{sentence_idx:02d}_r{repeat_idx}"
                recorded[rec_key] = {
                    "sentence_idx": sentence_idx,
                    "repeat": repeat_idx,
                    "language": args.language,
                    "sentence": sentences[sentence_idx] if sentence_idx < len(sentences) else ""
                }
                print(f"  ✓ Saved: {rec_key}")
                repeat_idx += 1
                if repeat_idx > 3:
                    repeat_idx = 1
                    sentence_idx += 1
                    if sentence_idx < len(sentences):
                        print(f"\n  Next sentence ({sentence_idx+1}/{len(sentences)})")

        elif key == ord('n'):
            if is_recording and writer:
                writer.release()
                writer = None
                is_recording = False
            sentence_idx = min(sentence_idx + 1, len(sentences) - 1)
            repeat_idx = 1
            print(f"  Skipped to sentence {sentence_idx+1}")

        elif key == ord('r'):
            if is_recording and writer:
                writer.release()
                writer = None
                is_recording = False
            print(f"  Redo sentence {sentence_idx+1}, repeat {repeat_idx}")

        elif key == ord('q'):
            if is_recording and writer:
                writer.release()
            break

        if is_recording and writer:
            writer.write(frame)

    cap.release()
    cv2.destroyAllWindows()

    metadata["recordings"] = list(recorded.values())
    metadata["total_recorded"] = len(recorded)
    metadata["total_expected"] = len(sentences) * 3
    metadata["completion_pct"] = round(len(recorded) / (len(sentences) * 3) * 100, 1)

    meta_path = os.path.join(vol_dir, "metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n=== Session Complete ===")
    print(f"Volunteer: {args.volunteer_id}")
    print(f"Recorded: {len(recorded)}/{len(sentences) * 3} ({metadata['completion_pct']}%)")
    print(f"Saved to: {vol_dir}")
    print(f"Metadata: {meta_path}")


if __name__ == "__main__":
    main()
