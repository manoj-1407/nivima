import os

import ffmpeg
import structlog

log = structlog.get_logger()


def extract_audio(video_path: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "source_audio.wav")
    (
        ffmpeg
        .input(video_path)
        .output(output_path, acodec="pcm_s16le", ac=1, ar="16000")
        .run(overwrite_output=True, quiet=True)
    )
    log.info("audio_extracted", path=output_path)
    return output_path


def merge_audio_video(
    video_path: str,
    dubbed_audio_path: str,
    background_audio_path: str,
    output_path: str,
    speech_volume: float = 1.0,
    background_volume: float = 0.7
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    video = ffmpeg.input(video_path).video
    speech = ffmpeg.input(dubbed_audio_path)
    background = ffmpeg.input(background_audio_path)

    mixed = ffmpeg.filter(
        [speech, background],
        "amix",
        inputs=2,
        weights=f"{speech_volume} {background_volume}",
        duration="first"
    )

    (
        ffmpeg
        .output(
            video, mixed, output_path,
            vcodec="copy",
            acodec="aac",
            audio_bitrate="192k"
        )
        .run(overwrite_output=True, quiet=True)
    )

    log.info("video_merged", output=output_path)
    return output_path


def merge_audio_only(
    video_path: str,
    dubbed_audio_path: str,
    output_path: str
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    video = ffmpeg.input(video_path).video
    audio = ffmpeg.input(dubbed_audio_path)

    (
        ffmpeg
        .output(video, audio, output_path, vcodec="copy", acodec="aac", audio_bitrate="192k")
        .run(overwrite_output=True, quiet=True)
    )

    log.info("audio_merged", output=output_path)
    return output_path


def concatenate_chunks(chunk_paths: list[str], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    list_file = output_path + ".txt"
    with open(list_file, "w") as f:
        for p in chunk_paths:
            f.write(f"file '{p}'\n")

    (
        ffmpeg
        .input(list_file, format="concat", safe=0)
        .output(output_path, c="copy")
        .run(overwrite_output=True, quiet=True)
    )

    os.remove(list_file)
    log.info("chunks_concatenated", count=len(chunk_paths), output=output_path)
    return output_path


def get_duration_seconds(file_path: str) -> float:
    probe = ffmpeg.probe(file_path)
    return float(probe["format"]["duration"])
