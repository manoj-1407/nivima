import os
import tempfile
from datetime import UTC, datetime

import structlog

from src.alignment.audio_adjuster import adjust_segment_timing, combine_dubbed_segments
from src.audio.separator import fallback_silence_background, separate_audio
from src.ingestion.extractor import extract_audio, merge_audio_video
from src.ingestion.validator import validate_and_extract_metadata
from src.storage.db import Chunk, ChunkStatus, Job, JobStatus, SessionLocal, VoiceClone
from src.storage.s3 import download_file, upload_file
from src.transcription.asr import segments_to_dict, transcribe_audio
from src.transcription.chunker import chunk_audio_by_scenes
from src.translation.domain_adapter import detect_domain
from src.translation.rewriter import rewrite_segments
from src.translation.translator import translate_segments
from src.tts.synthesizer import synthesize_segments
from src.worker.celery_app import app
from src.worker.tasks.notify import notify_job_complete, notify_job_failed

log = structlog.get_logger()


@app.task(bind=True, max_retries=2, default_retry_delay=120, name="pipeline.process_job")
def process_job(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            log.error("job_not_found", job_id=job_id)
            return
        job.started_at = datetime.now(UTC)
        db.commit()
        with tempfile.TemporaryDirectory() as tmpdir:
            _run_pipeline(self, db, job, tmpdir)
    except Exception as exc:
        log.error("job_failed", job_id=job_id, error=str(exc))
        _mark_failed(db, job_id, str(exc))
        notify_job_failed.delay(job_id, str(exc))
        raise self.retry(exc=exc)
    finally:
        db.close()


def _run_pipeline(task, db, job, tmpdir):
    job_id = str(job.id)
    log.info("pipeline_start", job_id=job_id, targets=job.target_languages)

    # Stage 1: Download + Validate
    _update(db, job, JobStatus.extracting, 5, "extracting")
    video_path = os.path.join(tmpdir, "source.mp4")
    download_file(job.source_file_path, video_path)
    metadata = validate_and_extract_metadata(video_path)
    job.source_duration_seconds = int(metadata.duration_seconds)
    job.source_resolution = metadata.resolution
    job.source_fps = str(metadata.fps)
    db.commit()

    # Stage 2: Audio separation
    audio_path = extract_audio(video_path, os.path.join(tmpdir, "audio"))
    try:
        speech_path, bg_path = separate_audio(audio_path, os.path.join(tmpdir, "separated"))
    except Exception as e:
        log.warning("demucs_failed_using_fallback", error=str(e))
        speech_path = audio_path
        bg_path = fallback_silence_background(tmpdir, metadata.duration_seconds)

    # Stage 3: Chunk + Transcribe
    chunk_dir = os.path.join(tmpdir, "chunks")
    chunks = chunk_audio_by_scenes(speech_path, video_path, chunk_dir)
    job.chunks_total = len(chunks)
    db.commit()
    _save_chunks_to_db(db, job, chunks)

    _update(db, job, JobStatus.transcribing, 20, "transcribing")
    all_segments = []
    full_transcript = ""
    for chunk in chunks:
        segs = transcribe_audio(chunk.audio_path, language=job.source_language,
                                chunk_offset_ms=chunk.start_ms)
        all_segments.extend(segs)
        full_transcript += " ".join(s.text for s in segs) + " "

    # Detect domain for content-aware translation
    domain_ctx = detect_domain(full_transcript)
    log.info("content_domain_detected",
             domain=domain_ctx.domain,
             confidence=domain_ctx.confidence)

    # Stage 4-7: Per-language processing
    for target_lang in job.target_languages:
        lang_dir = os.path.join(tmpdir, target_lang)
        os.makedirs(lang_dir, exist_ok=True)

        _update(db, job, JobStatus.translating, 35, "translating")
        seg_dicts = segments_to_dict(all_segments)
        translated = translate_segments(seg_dicts, job.source_language, target_lang)
        rewritten = rewrite_segments(translated, job.source_language, target_lang)

        _update(db, job, JobStatus.synthesizing, 55, "synthesizing")
        clone_path = _get_clone_path(db, job, tmpdir)
        synthesized = synthesize_segments(
            rewritten, target_lang,
            os.path.join(lang_dir, "audio"),
            voice_clone_path=clone_path
        )

        _update(db, job, JobStatus.aligning, 70, "aligning")
        adjusted = _adjust_all_timings(synthesized, lang_dir)
        combined_audio = combine_dubbed_segments(
            adjusted, os.path.join(lang_dir, "dubbed_combined.wav")
        )

        # Phase 2: Selective reanimation (if GPU available + MuseTalk present)
        _update(db, job, JobStatus.reanimating, 80, "reanimating")
        output_video_path = _maybe_reanimate(
            video_path=video_path,
            dubbed_audio_path=combined_audio,
            bg_audio_path=bg_path,
            lang_dir=lang_dir,
            target_lang=target_lang,
            job=job,
            metadata=metadata,
            tmpdir=tmpdir
        )

        _update(db, job, JobStatus.assembling, 90, "assembling")
        s3_key = f"jobs/{job_id}/output_{target_lang}.mp4"
        upload_file(output_video_path, s3_key)
        job.output_paths = {**(job.output_paths or {}), target_lang: s3_key}
        db.commit()

        log.info("language_complete", job_id=job_id, lang=target_lang)

    _update(db, job, JobStatus.completed, 100, "completed")
    job.completed_at = datetime.now(UTC)
    db.commit()
    notify_job_complete.delay(job_id)
    log.info("pipeline_complete", job_id=job_id)


def _maybe_reanimate(
    video_path, dubbed_audio_path, bg_audio_path,
    lang_dir, target_lang, job, metadata, tmpdir
) -> str:
    """
    Phase 2: attempt selective lip reanimation.
    Falls back to audio-only merge if GPU unavailable or MuseTalk not installed.
    """
    from src.config import get_settings
    from src.reanimation.musetalk import is_available as musetalk_available
    settings = get_settings()

    output_path = os.path.join(lang_dir, f"output_{target_lang}.mp4")

    if not settings.gpu_available or not musetalk_available():
        # Phase 1 fallback: audio-only merge
        log.info("reanimation_skipped_audio_only",
                 reason="GPU unavailable" if not settings.gpu_available else "MuseTalk not installed")
        merge_audio_video(video_path, dubbed_audio_path, bg_audio_path, output_path)
        return output_path

    try:
        from src.qc.quality_gate import evaluate_job_gate
        from src.qc.scorer import score_chunk
        from src.reanimation.musetalk import reanimate_chunk
        from src.scene.classifier import classify_chunk

        # Extract frames for scene classification
        frames_dir = os.path.join(tmpdir, "frames")
        _extract_frames(video_path, frames_dir, metadata.fps)

        # Classify scene
        classification = classify_chunk(frames_dir)
        log.info("scene_classified",
                 decision=classification.decision.value,
                 quality=classification.expected_quality,
                 reanimate=classification.should_reanimate)

        if not classification.should_reanimate:
            log.info("scene_skipped_audio_only",
                     reason=classification.decision.value)
            merge_audio_video(video_path, dubbed_audio_path, bg_audio_path, output_path)
            return output_path

        # Reanimate
        reanimated_path = os.path.join(lang_dir, f"reanimated_{target_lang}.mp4")
        reanimated, sync_conf = reanimate_chunk(
            video_path, dubbed_audio_path, reanimated_path, fps=metadata.fps
        )

        # Quality gate
        reanimated_frames_dir = os.path.join(tmpdir, "reanimated_frames")
        _extract_frames(reanimated, reanimated_frames_dir, metadata.fps)
        score = score_chunk(frames_dir, reanimated_frames_dir, dubbed_audio_path)
        gate = evaluate_job_gate([score])

        if gate["action"] == "deliver_audio_only":
            log.warning("quality_gate_blocked_reverting_to_audio_only",
                        syncnet=score.syncnet_score)
            merge_audio_video(video_path, dubbed_audio_path, bg_audio_path, output_path)
        else:
            # Deliver reanimated version
            merge_audio_video(reanimated, dubbed_audio_path, bg_audio_path, output_path)
            log.info("reanimated_video_assembled",
                     gate_decision=gate["decision"],
                     syncnet=score.syncnet_score)

        return output_path

    except Exception as e:
        log.error("reanimation_failed_fallback_audio_only", error=str(e))
        merge_audio_video(video_path, dubbed_audio_path, bg_audio_path, output_path)
        return output_path


def _extract_frames(video_path: str, frames_dir: str, fps: float):
    import subprocess
    os.makedirs(frames_dir, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps={min(fps, 25)}",
        "-q:v", "2",
        os.path.join(frames_dir, "%06d.jpg")
    ], capture_output=True)


def _adjust_all_timings(segments: list[dict], output_dir: str) -> list[dict]:
    adjusted = []
    adj_dir = os.path.join(output_dir, "adjusted")
    os.makedirs(adj_dir, exist_ok=True)
    for i, seg in enumerate(segments):
        dubbed = seg.get("dubbed_audio_path", "")
        duration = seg.get("end_ms", 0) - seg.get("start_ms", 0)
        if not dubbed or not os.path.exists(dubbed) or duration <= 0:
            adjusted.append(seg)
            continue
        out_path = os.path.join(adj_dir, f"adj_{i:04d}.wav")
        adjusted_path, info = adjust_segment_timing(dubbed, duration, out_path)
        adjusted.append({**seg, "dubbed_audio_path": adjusted_path, "timing_info": info})
    return adjusted


def _get_clone_path(db, job, tmpdir) -> str | None:
    if not job.voice_clone_id:
        return None
    clone = db.query(VoiceClone).filter(VoiceClone.id == job.voice_clone_id).first()
    if not clone:
        return None
    local = os.path.join(tmpdir, "clone_ref.wav")
    download_file(clone.reference_audio_path, local)
    return local


def _save_chunks_to_db(db, job, chunks):
    for chunk in chunks:
        db_chunk = Chunk(
            job_id=job.id,
            chunk_index=chunk.index,
            start_ms=chunk.start_ms,
            end_ms=chunk.end_ms,
            status=ChunkStatus.pending
        )
        db.add(db_chunk)
    db.commit()


def _update(db, job, status, progress: int, stage: str):
    job.status = status
    job.progress_pct = progress
    job.current_stage = stage
    db.commit()
    log.info("job_stage", job_id=str(job.id), stage=stage, pct=progress)


def _mark_failed(db, job_id: str, error: str):
    db2 = SessionLocal()
    try:
        job = db2.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.failed
            job.error_message = error[:1000]
            db2.commit()
    finally:
        db2.close()
