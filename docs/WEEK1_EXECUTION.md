# Week 1 Execution — VoxBridge Phase 1

## Goal By End Of Week 1
Take a Hindi YouTube video.
Get a Telugu audio-dubbed version merged back into the original video.
No lip sync. No visual changes. Just audio. Prove the pipeline works end to end.

---

## Day 1-2: Environment + Transcription

```bash
conda create -n voxbridge python=3.11
conda activate voxbridge

pip install faster-whisper
pip install ffmpeg-python
pip install requests

# Test faster-whisper on a Hindi video
python -c "
from faster_whisper import WhisperModel
model = WhisperModel('large-v3', device='cpu', compute_type='int8')
segments, info = model.transcribe('test_hindi.mp4', language='hi')
for segment in segments:
    print(f'[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}')
"
```

**Test video:** Download any 2-3 minute Hindi educational YouTube video.
Tools: `yt-dlp` — `pip install yt-dlp`

```bash
yt-dlp -f mp4 "YOUTUBE_URL" -o test_hindi.mp4
```

**What to verify:**
- Transcription accuracy on Hindi — should be > 90% correct
- Word-level timestamps present
- Language auto-detected correctly

---

## Day 3: Translation

```bash
pip install ctranslate2 sentencepiece
# IndicTrans2 via HuggingFace
pip install transformers

python -c "
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

model_name = 'ai4bharat/indictrans2-indic-indic-dist-200M'
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)

# Test: Hindi to Telugu
text = 'नमस्कार, आज हम गणित के बारे में पढ़ेंगे'
inputs = tokenizer(text, return_tensors='pt', src_lang='hin_Deva')
outputs = model.generate(**inputs, tgt_lang='tel_Telu', max_length=256)
translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(translation)
"
```

**What to verify:**
- Translation is semantically correct (ask a Telugu speaker or use back-translation)
- SOV structure is preserved in Telugu output

---

## Day 4-5: TTS + Audio Generation

```bash
pip install TTS  # Coqui TTS (includes XTTS-v2)

# Option A: Generic Telugu TTS (no voice clone)
python -c "
from TTS.api import TTS
tts = TTS('tts_models/te/cv/vits')  # Telugu model
tts.tts_to_file(
    text='నమస్కారం, ఈరోజు మనం గణితం గురించి చదువుతాం',
    file_path='output_telugu.wav'
)
"

# Option B: XTTS-v2 voice clone (Hindi voice → Telugu)
python -c "
from TTS.api import TTS
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
tts.tts_to_file(
    text='నమస్కారం, ఈరోజు మనం గణితం గురించి చదువుతాం',
    speaker_wav='reference_hindi_voice.wav',  # 6s clip of original speaker
    language='hi',  # closest supported language
    file_path='output_cloned.wav'
)
"
```

**Reality check on XTTS-v2:**
Telugu is NOT natively supported. Use Hindi phoneme approximation.
Quality will be 60-70% voice match. Acceptable for demo. Disclose to users.

---

## Day 6-7: Audio Merge + First Full Pipeline

```bash
pip install pydub

python pipeline_v1.py test_hindi.mp4 telugu
```

```python
# pipeline_v1.py — first working version
import subprocess
import sys
from faster_whisper import WhisperModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from TTS.api import TTS
import ffmpeg

LANG_MAP = {
    'telugu': {'indictrans': 'tel_Telu', 'tts': 'te'},
    'tamil':  {'indictrans': 'tam_Taml', 'tts': 'ta'},
    'kannada':{'indictrans': 'kan_Knda', 'tts': 'kn'},
}

def extract_audio(video_path):
    audio_path = video_path.replace('.mp4', '_audio.wav')
    ffmpeg.input(video_path).output(
        audio_path, acodec='pcm_s16le', ac=1, ar='16000'
    ).run(overwrite_output=True)
    return audio_path

def transcribe(audio_path):
    model = WhisperModel('large-v3', device='cpu', compute_type='int8')
    segments, info = model.transcribe(audio_path, language='hi', word_timestamps=True)
    return list(segments)

def translate(segments, target_lang):
    model_name = 'ai4bharat/indictrans2-indic-indic-dist-200M'
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
    
    translated = []
    for seg in segments:
        inputs = tokenizer(seg.text, return_tensors='pt', src_lang='hin_Deva')
        outputs = model.generate(
            **inputs,
            tgt_lang=LANG_MAP[target_lang]['indictrans'],
            max_length=512
        )
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        translated.append({'text': text, 'start': seg.start, 'end': seg.end})
    return translated

def synthesize(translated_segments, target_lang, output_path):
    tts = TTS(f"tts_models/{LANG_MAP[target_lang]['tts']}/cv/vits")
    full_text = ' '.join([s['text'] for s in translated_segments])
    tts.tts_to_file(text=full_text, file_path=output_path)

def merge_audio(video_path, dubbed_audio_path, output_path):
    video = ffmpeg.input(video_path)
    audio = ffmpeg.input(dubbed_audio_path)
    ffmpeg.output(
        video.video, audio.audio,
        output_path,
        vcodec='copy',
        acodec='aac'
    ).run(overwrite_output=True)

if __name__ == '__main__':
    video_path = sys.argv[1]
    target_lang = sys.argv[2]
    
    print(f'Extracting audio...')
    audio = extract_audio(video_path)
    
    print(f'Transcribing Hindi...')
    segments = transcribe(audio)
    
    print(f'Translating to {target_lang}...')
    translated = translate(segments, target_lang)
    
    print(f'Synthesizing {target_lang} speech...')
    dubbed_audio = f'dubbed_{target_lang}.wav'
    synthesize(translated, target_lang, dubbed_audio)
    
    print(f'Merging audio with video...')
    output = f'output_{target_lang}.mp4'
    merge_audio(video_path, dubbed_audio, output)
    
    print(f'Done: {output}')
```

---

## Week 2 Goals
- Add per-segment timing alignment (audio duration matching)
- FastAPI wrapper around the pipeline
- Redis job queue (async processing)
- Basic web UI: upload → status polling → download

## Week 3-4 Goals
- Force alignment (MFA) for phoneme timestamps
- Constrained translation prompt (LLM rewrite pass)
- 5 real test videos end-to-end
- First shareable demo link

---

## Known Issues To Expect In Week 1

**TTS duration mismatch:**
Telugu TTS will produce audio that's longer or shorter than original.
The merged video will have sync issues between dubbed audio and video events.
This is expected. Fix in Week 2 with time-stretching.

**Translation quality:**
IndicTrans2 is good but not perfect. Some sentences will be awkward.
This is expected. The constrained rewrite pass (Week 2) improves this.

**XTTS-v2 Telugu quality:**
Will sound like the original speaker speaking with a Hindi accent in Telugu.
This is expected and disclosed. Better with fine-tuning (Phase 2).

**Processing speed:**
On CPU: 10-minute video will take 20-40 minutes. Expected.
Get GPU access (Colab) for anything longer than 5 minutes.

---

## Hardware Requirements

**Minimum (CPU only):**
- 16GB RAM
- 50GB free disk (models are large)
- Any modern CPU

**Recommended:**
- Google Colab Pro+ (A100 access)
- Vast.ai A100 rental ($1.10/hr) for fine-tuning

**Model sizes:**
- Whisper large-v3: 3GB
- IndicTrans2 200M: 800MB  
- XTTS-v2: 1.8GB
- MuseTalk (Phase 2): 1.2GB
- LatentSync (Phase 2): 2.5GB
- Total Phase 1: ~6GB disk
- Total Phase 2: ~11GB disk
