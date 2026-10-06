import os
import json
import subprocess
import tempfile
import structlog

log = structlog.get_logger()

MFA_ACOUSTIC_MODELS = {
    "hi": "hindi_mfa",
    "te": "hindi_mfa",  # fallback — Telugu model not publicly available
    "ta": "hindi_mfa",
    "kn": "hindi_mfa",
    "ml": "hindi_mfa",
    "bn": "hindi_mfa",
    "mr": "hindi_mfa",
}

MFA_DICTIONARIES = {
    "hi": "hindi_mfa",
    "te": "hindi_mfa",
    "ta": "hindi_mfa",
    "kn": "hindi_mfa",
    "ml": "hindi_mfa",
    "bn": "hindi_mfa",
    "mr": "hindi_mfa",
}


def align_audio_to_transcript(
    audio_path: str,
    transcript: str,
    language: str,
    output_dir: str
) -> list[dict]:
    """
    Runs MFA forced alignment.
    Returns list of {phoneme, start_ms, end_ms, word} dicts.
    Falls back to Whisper-based alignment if MFA fails.
    """
    os.makedirs(output_dir, exist_ok=True)

    try:
        return _mfa_align(audio_path, transcript, language, output_dir)
    except Exception as e:
        log.warning("mfa_alignment_failed", error=str(e), fallback="whisper_alignment")
        return _whisper_fallback_align(audio_path, transcript, language)


def _mfa_align(
    audio_path: str,
    transcript: str,
    language: str,
    output_dir: str
) -> list[dict]:
    acoustic = MFA_ACOUSTIC_MODELS.get(language, "hindi_mfa")
    dictionary = MFA_DICTIONARIES.get(language, "hindi_mfa")

    corpus_dir = os.path.join(output_dir, "corpus")
    os.makedirs(corpus_dir, exist_ok=True)

    import shutil
    audio_dest = os.path.join(corpus_dir, "audio.wav")
    shutil.copy(audio_path, audio_dest)

    lab_path = os.path.join(corpus_dir, "audio.lab")
    with open(lab_path, "w", encoding="utf-8") as f:
        f.write(transcript)

    aligned_dir = os.path.join(output_dir, "aligned")

    result = subprocess.run([
        "mfa", "align",
        corpus_dir, dictionary, acoustic, aligned_dir,
        "--clean", "--quiet"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"MFA failed: {result.stderr[:300]}")

    return _parse_textgrid(aligned_dir)


def _parse_textgrid(aligned_dir: str) -> list[dict]:
    """Parse MFA TextGrid output into phoneme timestamp list."""
    import glob
    textgrids = glob.glob(os.path.join(aligned_dir, "**", "*.TextGrid"), recursive=True)
    if not textgrids:
        return []

    phonemes = []
    with open(textgrids[0], "r", encoding="utf-8") as f:
        content = f.read()

    # Simple TextGrid parser — extract phone tier
    lines = content.splitlines()
    in_phone_tier = False
    current_interval = {}

    for line in lines:
        line = line.strip()
        if '"phones"' in line or '"phone"' in line:
            in_phone_tier = True
        if in_phone_tier:
            if line.startswith("xmin"):
                current_interval["start_ms"] = int(float(line.split("=")[1].strip()) * 1000)
            elif line.startswith("xmax"):
                current_interval["end_ms"] = int(float(line.split("=")[1].strip()) * 1000)
            elif line.startswith("text"):
                text = line.split("=")[1].strip().strip('"')
                if text and text != "":
                    current_interval["phoneme"] = text
                    phonemes.append(dict(current_interval))
                current_interval = {}

    return phonemes


def _whisper_fallback_align(
    audio_path: str,
    transcript: str,
    language: str
) -> list[dict]:
    """
    Fallback: use Whisper word timestamps as approximate phoneme boundaries.
    Less accurate than MFA but always works.
    """
    from faster_whisper import WhisperModel

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True
    )

    phonemes = []
    for seg in segments:
        if seg.words:
            for w in seg.words:
                phonemes.append({
                    "phoneme": w.word.strip(),
                    "start_ms": int(w.start * 1000),
                    "end_ms": int(w.end * 1000),
                    "word": w.word.strip(),
                    "is_word_level": True
                })

    log.info("whisper_fallback_alignment_done", phonemes=len(phonemes))
    return phonemes
