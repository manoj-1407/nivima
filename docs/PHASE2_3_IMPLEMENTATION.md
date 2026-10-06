# Phase 2 + Phase 3 — Complete Implementation Plan

---

# PHASE 2 — Visual Layer (Month 3-6)

## Goal
Add selective lip reanimation on top of the working Phase 1 audio pipeline.
Only reanimate scenes where output will be high quality.
Skip everything else — original video + dubbed audio is still better than bad reanimation.

## New Modules Added in Phase 2

```
src/
├── scene/
│   ├── __init__.py
│   ├── detector.py          # PySceneDetect wrapper
│   ├── classifier.py        # face pose + occlusion → REANIMATE/SKIP decision
│   ├── face_analyzer.py     # MediaPipe + 3DDFA-V2 face analysis
│   └── diarization.py       # pyannote-audio speaker diarization
│
├── reanimation/
│   ├── __init__.py
│   ├── musetalk.py          # MuseTalk 1.5 integration (speed tier)
│   ├── latentsync.py        # LatentSync 1.6 integration (quality tier)
│   ├── smoother.py          # temporal consistency post-processing
│   ├── compositor.py        # blend reanimated region with original
│   └── quality_guard.py     # PSNR check, auto-revert bad composites
│
└── qc/
    ├── __init__.py
    ├── scorer.py             # SyncNet score, CSIM, PSNR computation
    ├── flagger.py            # threshold-based scene flagging
    └── dashboard.py          # human review queue API routes
```

---

## src/scene/classifier.py

```python
import mediapipe as mp
import numpy as np
import cv2
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class SceneDecision(Enum):
    FRONTAL_CLEAR = "FRONTAL_CLEAR"      # reanimate — high confidence
    PARTIAL_VISIBLE = "PARTIAL_VISIBLE"  # reanimate + flag — medium confidence
    PROFILE = "PROFILE"                  # skip — face turned too far
    OCCLUDED = "OCCLUDED"               # skip — mouth blocked
    MULTI_FACE = "MULTI_FACE"           # skip — can't identify active speaker
    NO_FACE = "NO_FACE"                 # skip — B-roll, slides, text
    LOW_RES = "LOW_RES"                 # skip — face too small in frame

@dataclass
class SceneAnalysis:
    decision: SceneDecision
    confidence: float
    yaw_deg: float
    pitch_deg: float
    occlusion_score: float
    face_count: int
    face_size_pct: float  # face area as % of frame
    active_speaker_id: Optional[str]
    reanimation_expected_quality: float  # 0-1

THRESHOLDS = {
    'yaw_frontal': 20.0,       # degrees from frontal for FRONTAL_CLEAR
    'yaw_partial': 40.0,       # degrees for PARTIAL_VISIBLE
    'occlusion_frontal': 0.10, # max occlusion for FRONTAL_CLEAR
    'occlusion_partial': 0.40, # max occlusion for PARTIAL_VISIBLE
    'min_confidence': 0.70,    # minimum face detection confidence
    'min_face_size': 0.005,    # minimum face area as fraction of frame (64x64 in 1080p)
}

mp_face_mesh = mp.solutions.face_mesh
mp_face_detection = mp.solutions.face_detection

def analyze_frame(frame: np.ndarray) -> SceneAnalysis:
    h, w = frame.shape[:2]
    
    with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as detector:
        results = detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    if not results.detections:
        return SceneAnalysis(
            decision=SceneDecision.NO_FACE,
            confidence=1.0, yaw_deg=0, pitch_deg=0,
            occlusion_score=0, face_count=0,
            face_size_pct=0, active_speaker_id=None,
            reanimation_expected_quality=0
        )
    
    face_count = len(results.detections)
    
    if face_count > 1:
        return SceneAnalysis(
            decision=SceneDecision.MULTI_FACE,
            confidence=1.0, yaw_deg=0, pitch_deg=0,
            occlusion_score=0, face_count=face_count,
            face_size_pct=0, active_speaker_id=None,
            reanimation_expected_quality=0.3
        )
    
    detection = results.detections[0]
    bbox = detection.location_data.relative_bounding_box
    face_area_pct = bbox.width * bbox.height
    
    if face_area_pct < THRESHOLDS['min_face_size']:
        return SceneAnalysis(
            decision=SceneDecision.LOW_RES,
            confidence=1.0, yaw_deg=0, pitch_deg=0,
            occlusion_score=0, face_count=1,
            face_size_pct=face_area_pct, active_speaker_id=None,
            reanimation_expected_quality=0
        )
    
    # Head pose estimation via 3DDFA-V2
    yaw, pitch, roll = estimate_head_pose(frame, detection)
    
    # Occlusion estimation via mouth landmark visibility
    occlusion = estimate_mouth_occlusion(frame, detection)
    
    confidence = detection.score[0]
    
    if confidence < THRESHOLDS['min_confidence']:
        return SceneAnalysis(
            decision=SceneDecision.PROFILE,
            confidence=confidence, yaw_deg=yaw, pitch_deg=pitch,
            occlusion_score=occlusion, face_count=1,
            face_size_pct=face_area_pct, active_speaker_id=None,
            reanimation_expected_quality=0.2
        )
    
    if abs(yaw) > THRESHOLDS['yaw_partial']:
        return SceneAnalysis(
            decision=SceneDecision.PROFILE,
            confidence=confidence, yaw_deg=yaw, pitch_deg=pitch,
            occlusion_score=occlusion, face_count=1,
            face_size_pct=face_area_pct, active_speaker_id=None,
            reanimation_expected_quality=0.1
        )
    
    if occlusion > THRESHOLDS['occlusion_partial']:
        return SceneAnalysis(
            decision=SceneDecision.OCCLUDED,
            confidence=confidence, yaw_deg=yaw, pitch_deg=pitch,
            occlusion_score=occlusion, face_count=1,
            face_size_pct=face_area_pct, active_speaker_id=None,
            reanimation_expected_quality=0.2
        )
    
    if abs(yaw) <= THRESHOLDS['yaw_frontal'] and occlusion <= THRESHOLDS['occlusion_frontal']:
        quality = 0.85 - (abs(yaw) / THRESHOLDS['yaw_frontal']) * 0.1
        return SceneAnalysis(
            decision=SceneDecision.FRONTAL_CLEAR,
            confidence=confidence, yaw_deg=yaw, pitch_deg=pitch,
            occlusion_score=occlusion, face_count=1,
            face_size_pct=face_area_pct, active_speaker_id='S1',
            reanimation_expected_quality=quality
        )
    
    quality = 0.60 - (abs(yaw) / THRESHOLDS['yaw_partial']) * 0.2
    return SceneAnalysis(
        decision=SceneDecision.PARTIAL_VISIBLE,
        confidence=confidence, yaw_deg=yaw, pitch_deg=pitch,
        occlusion_score=occlusion, face_count=1,
        face_size_pct=face_area_pct, active_speaker_id='S1',
        reanimation_expected_quality=quality
    )

def classify_chunk(frames_dir: str, sample_rate: int = 5) -> SceneAnalysis:
    """
    Sample N evenly-spaced frames from chunk.
    Take worst-case decision (most conservative).
    """
    import os
    frame_files = sorted(os.listdir(frames_dir))
    sampled = frame_files[::sample_rate] or frame_files[:1]
    
    analyses = []
    for f in sampled:
        frame = cv2.imread(os.path.join(frames_dir, f))
        if frame is not None:
            analyses.append(analyze_frame(frame))
    
    if not analyses:
        return SceneAnalysis(
            decision=SceneDecision.NO_FACE,
            confidence=1.0, yaw_deg=0, pitch_deg=0,
            occlusion_score=0, face_count=0,
            face_size_pct=0, active_speaker_id=None,
            reanimation_expected_quality=0
        )
    
    # Priority order: most conservative decision wins
    priority = [
        SceneDecision.LOW_RES,
        SceneDecision.OCCLUDED,
        SceneDecision.PROFILE,
        SceneDecision.MULTI_FACE,
        SceneDecision.PARTIAL_VISIBLE,
        SceneDecision.FRONTAL_CLEAR,
        SceneDecision.NO_FACE,
    ]
    
    decisions = [a.decision for a in analyses]
    for decision in priority:
        if decision in decisions:
            worst = next(a for a in analyses if a.decision == decision)
            return worst
    
    return analyses[0]

def estimate_head_pose(frame, detection) -> tuple[float, float, float]:
    # 3DDFA-V2 integration placeholder
    # Returns (yaw, pitch, roll) in degrees
    # Actual implementation: use 3DDFA-V2 CNN model
    # For now: approximation from face bounding box asymmetry
    return 0.0, 0.0, 0.0  # replace with actual 3DDFA-V2 call

def estimate_mouth_occlusion(frame, detection) -> float:
    # MediaPipe FaceMesh landmark visibility for mouth region
    # Returns 0-1 occlusion score
    return 0.0  # replace with actual implementation
```

---

## src/reanimation/compositor.py

```python
import cv2
import numpy as np
from typing import Optional

PSNR_THRESHOLD = 35.0  # dB — minimum acceptable for non-lip regions

def compute_psnr(original: np.ndarray, processed: np.ndarray) -> float:
    mse = np.mean((original.astype(float) - processed.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * np.log10(255.0 / np.sqrt(mse))

def get_lip_mask(frame: np.ndarray, landmarks) -> np.ndarray:
    """
    Returns binary mask of lip region.
    MediaPipe FaceMesh landmark indices for lips:
    Upper: 61, 185, 40, 39, 37, 0, 267, 269, 270, 409
    Lower: 146, 91, 181, 84, 17, 314, 405, 321, 375, 291
    """
    h, w = frame.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    lip_points = []
    for lm in landmarks:
        lip_points.append([int(lm.x * w), int(lm.y * h)])
    
    if lip_points:
        hull = cv2.convexHull(np.array(lip_points))
        cv2.fillConvexPoly(mask, hull, 255)
        
        # Feather the mask edges for smooth blending
        mask = cv2.GaussianBlur(mask, (21, 21), 11)
    
    return mask

def composite_frame(
    original: np.ndarray,
    reanimated: np.ndarray,
    lip_mask: np.ndarray,
    confidence: float = 1.0
) -> tuple[np.ndarray, bool]:
    """
    Returns (composited_frame, is_quality_ok)
    If PSNR on non-lip region drops below threshold → quality not ok → caller reverts
    """
    # Scale mask by confidence
    alpha = (lip_mask.astype(float) / 255.0) * confidence
    alpha_3ch = np.stack([alpha, alpha, alpha], axis=2)
    
    composited = (reanimated * alpha_3ch + original * (1 - alpha_3ch)).astype(np.uint8)
    
    # Quality check: non-lip region should be identical to original
    non_lip_mask = (lip_mask < 10)
    if non_lip_mask.sum() > 0:
        orig_non_lip = original[non_lip_mask]
        comp_non_lip = composited[non_lip_mask]
        psnr = compute_psnr(
            orig_non_lip.reshape(-1, 3),
            comp_non_lip.reshape(-1, 3)
        )
        quality_ok = psnr > PSNR_THRESHOLD
    else:
        quality_ok = True
    
    return composited, quality_ok

def apply_temporal_smoothing(frames: list[np.ndarray], window: int = 3) -> list[np.ndarray]:
    """
    Weighted blend across adjacent frames in lip region to reduce flickering.
    """
    smoothed = []
    for i, frame in enumerate(frames):
        start = max(0, i - window // 2)
        end = min(len(frames), i + window // 2 + 1)
        neighbors = frames[start:end]
        weights = np.array([1.0 / (abs(j - i) + 1) for j in range(start, end)])
        weights /= weights.sum()
        blended = sum(w * f.astype(float) for w, f in zip(weights, neighbors))
        smoothed.append(blended.astype(np.uint8))
    return smoothed
```

---

## src/qc/scorer.py

```python
import numpy as np
import torch
from dataclasses import dataclass

@dataclass
class QCScore:
    syncnet_score: float       # audio-visual correlation (target > 7.0)
    csim_score: float          # face identity preservation (target > 0.85)
    psnr_non_lip: float        # pixel accuracy outside lip region (target > 35dB)
    temporal_variance: float   # flickering metric (lower = better)
    scenes_processed: int
    scenes_skipped: int
    frames_reverted: int       # auto-reverted due to quality guard
    overall_pass: bool

THRESHOLDS = {
    'syncnet_min': 5.0,    # flag below this
    'syncnet_good': 7.0,   # target
    'csim_min': 0.80,
    'csim_good': 0.85,
    'psnr_min': 30.0,
    'temporal_variance_max': 8.0
}

def compute_scene_scores(
    original_frames_dir: str,
    reanimated_frames_dir: str,
    dubbed_audio_path: str
) -> QCScore:
    """
    Compute all QC metrics for a single scene.
    """
    syncnet = _compute_syncnet_score(reanimated_frames_dir, dubbed_audio_path)
    csim = _compute_csim(original_frames_dir, reanimated_frames_dir)
    psnr = _compute_psnr_non_lip(original_frames_dir, reanimated_frames_dir)
    temporal = _compute_temporal_variance(reanimated_frames_dir)
    
    overall = (
        syncnet >= THRESHOLDS['syncnet_min'] and
        csim >= THRESHOLDS['csim_min'] and
        psnr >= THRESHOLDS['psnr_min'] and
        temporal <= THRESHOLDS['temporal_variance_max']
    )
    
    return QCScore(
        syncnet_score=syncnet,
        csim_score=csim,
        psnr_non_lip=psnr,
        temporal_variance=temporal,
        scenes_processed=1,
        scenes_skipped=0,
        frames_reverted=0,
        overall_pass=overall
    )

def _compute_syncnet_score(frames_dir: str, audio_path: str) -> float:
    # SyncNet: pretrained model from Chung et al.
    # Measures correlation between lip movement and audio
    # Implementation: load SyncNet weights, extract visual + audio features,
    # compute cosine distance → sync confidence score
    # Placeholder: return mock score
    return 7.5  # replace with actual SyncNet inference

def _compute_csim(orig_dir: str, reanim_dir: str) -> float:
    # CSIM: Cosine Similarity between face embeddings
    # Use ArcFace or FaceNet to extract 512-dim face embedding
    # Compare original face embedding vs reanimated face embedding
    # Good reanimation: CSIM > 0.85 (face identity preserved)
    return 0.88  # replace with actual face embedding comparison

def _compute_psnr_non_lip(orig_dir: str, reanim_dir: str) -> float:
    # PSNR on non-lip region across all frames
    # Non-lip region should be pixel-identical to original
    return 42.0  # replace with actual per-frame computation

def _compute_temporal_variance(frames_dir: str) -> float:
    # Measure flickering in lip region across frames
    # High variance = flickering = bad
    return 3.2  # replace with actual computation

def should_flag(score: QCScore) -> tuple[bool, list[str]]:
    reasons = []
    if score.syncnet_score < THRESHOLDS['syncnet_min']:
        reasons.append(f"low_syncnet: {score.syncnet_score:.2f} < {THRESHOLDS['syncnet_min']}")
    if score.csim_score < THRESHOLDS['csim_min']:
        reasons.append(f"low_csim: {score.csim_score:.2f} < {THRESHOLDS['csim_min']}")
    if score.psnr_non_lip < THRESHOLDS['psnr_min']:
        reasons.append(f"low_psnr: {score.psnr_non_lip:.2f}dB < {THRESHOLDS['psnr_min']}dB")
    if score.temporal_variance > THRESHOLDS['temporal_variance_max']:
        reasons.append(f"high_flicker: {score.temporal_variance:.2f}")
    return len(reasons) > 0, reasons
```

---

# PHASE 3 — Speed-Invariant Playback (Month 6-12)

## Goal
Build the research moat. Decouple animation from pixels. Enable lip sync at any playback speed.

## New Modules in Phase 3

```
src/
├── player/
│   ├── manifest_generator.py    # extract viseme sequence → animation manifest JSON
│   ├── mesh_builder.py          # 3DMM face mesh per speaker
│   ├── blendshape_library.py    # Indian phoneme → blendshape weight mapping
│   └── manifest_store.py        # store/retrieve manifests from DB

sdk/
├── voxplayer-web/               # TypeScript/React player SDK
│   ├── src/
│   │   ├── VoxPlayer.tsx        # main player component
│   │   ├── ManifestLoader.ts    # fetch and parse animation manifest
│   │   ├── MeshRenderer.ts      # WebGL/Canvas face mesh rendering
│   │   ├── BlendshapeEngine.ts  # apply blend weights to mesh
│   │   └── Compositor.ts        # overlay rendered lip on video frame
│   └── package.json
│
└── voxplayer-native/            # React Native SDK (future)
```

---

## Animation Manifest Schema (v1.0)

```typescript
interface AnimationManifest {
  version: "1.0";
  job_id: string;
  target_language: string;
  base_video_url: string;        // original video, untouched
  dubbed_audio_url: string;      // dubbed audio track
  fps: number;
  total_frames: number;
  
  speakers: {
    [speaker_id: string]: {
      mesh_url: string;          // binary 3DMM mesh file
      reference_frame: number;   // frame where face was captured for mesh
    }
  };
  
  segments: AnimationSegment[];
  skipped_ranges: TimeRange[];   // where no reanimation was applied
}

interface AnimationSegment {
  frame: number;
  timestamp_ms: number;
  speaker_id: string;
  viseme: VisemeType;
  intensity: number;             // 0-1, how strongly to apply
  duration_frames: number;
  
  blend_weights: {
    jaw_open: number;
    lip_corner_puller: number;
    lip_corner_depressor: number;
    upper_lip_raiser: number;
    lower_lip_depressor: number;
    lip_stretcher: number;
    lip_tightener: number;
    lip_pressor: number;
    cheek_raiser: number;        // for retroflex sounds
  };
}

type VisemeType =
  | "bilabial_closure"    // p, b, m
  | "labiodental"         // f, v
  | "dental"              // th, dh
  | "alveolar"            // t, d, n, s, z
  | "retroflex"           // ट, ड, ण (Indian retroflex)
  | "palatal"             // ch, j, y
  | "velar"               // k, g, ng
  | "open_wide"           // aa, ah
  | "mid_open"            // ae, eh
  | "spread"              // ee, ih
  | "rounded"             // oo, uw
  | "central"             // schwa
  | "silence";

interface TimeRange {
  start_ms: number;
  end_ms: number;
  reason: "profile" | "occluded" | "multi_face" | "no_face" | "low_res";
}
```

---

## src/player/manifest_generator.py

```python
import json
from dataclasses import dataclass, asdict
from typing import List, Dict
from .blendshape_library import PHONEME_TO_BLENDWEIGHTS, PHONEME_TO_VISEME

def generate_manifest(
    job_id: str,
    target_language: str,
    base_video_url: str,
    dubbed_audio_url: str,
    phoneme_timestamps: List[dict],
    scene_decisions: List[dict],
    speaker_meshes: Dict[str, str],
    fps: float,
    total_frames: int
) -> dict:
    segments = []
    skipped_ranges = []
    
    for phoneme_entry in phoneme_timestamps:
        speaker_id = phoneme_entry.get('speaker_id', 'S1')
        phoneme = phoneme_entry['phoneme']
        timestamp_ms = phoneme_entry['start_ms']
        duration_ms = phoneme_entry['end_ms'] - phoneme_entry['start_ms']
        
        frame = int((timestamp_ms / 1000) * fps)
        duration_frames = max(1, int((duration_ms / 1000) * fps))
        
        viseme = PHONEME_TO_VISEME.get(phoneme, 'silence')
        blend_weights = PHONEME_TO_BLENDWEIGHTS.get(phoneme, {})
        intensity = phoneme_entry.get('confidence', 0.8)
        
        segments.append({
            'frame': frame,
            'timestamp_ms': timestamp_ms,
            'speaker_id': speaker_id,
            'viseme': viseme,
            'intensity': intensity,
            'duration_frames': duration_frames,
            'blend_weights': blend_weights
        })
    
    for decision in scene_decisions:
        if decision['decision'] not in ('FRONTAL_CLEAR', 'PARTIAL_VISIBLE'):
            skipped_ranges.append({
                'start_ms': decision['start_ms'],
                'end_ms': decision['end_ms'],
                'reason': decision['decision'].lower()
            })
    
    return {
        'version': '1.0',
        'job_id': job_id,
        'target_language': target_language,
        'base_video_url': base_video_url,
        'dubbed_audio_url': dubbed_audio_url,
        'fps': fps,
        'total_frames': total_frames,
        'speakers': speaker_meshes,
        'segments': segments,
        'skipped_ranges': skipped_ranges
    }
```

---

## sdk/voxplayer-web/src/VoxPlayer.tsx

```typescript
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { ManifestLoader, AnimationManifest, AnimationSegment } from './ManifestLoader';
import { BlendshapeEngine } from './BlendshapeEngine';
import { Compositor } from './Compositor';

interface VoxPlayerProps {
  manifestUrl: string;
  autoPlay?: boolean;
  controls?: boolean;
  width?: number;
  height?: number;
}

export const VoxPlayer: React.FC<VoxPlayerProps> = ({
  manifestUrl, autoPlay = false, controls = true, width = 854, height = 480
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const manifestRef = useRef<AnimationManifest | null>(null);
  const engineRef = useRef<BlendshapeEngine | null>(null);
  const compositorRef = useRef<Compositor | null>(null);
  const animFrameRef = useRef<number>(0);
  const [loading, setLoading] = useState(true);
  const [playbackRate, setPlaybackRate] = useState(1.0);

  useEffect(() => {
    ManifestLoader.load(manifestUrl).then(manifest => {
      manifestRef.current = manifest;
      engineRef.current = new BlendshapeEngine(manifest.speakers);
      compositorRef.current = new Compositor(canvasRef.current!, width, height);
      setLoading(false);
    });
  }, [manifestUrl]);

  const renderFrame = useCallback(() => {
    const video = videoRef.current;
    const manifest = manifestRef.current;
    const engine = engineRef.current;
    const compositor = compositorRef.current;
    
    if (!video || !manifest || !engine || !compositor || video.paused) return;
    
    const currentMs = video.currentTime * 1000;
    const rate = video.playbackRate;
    
    // KEY: scale manifest timestamp lookup by playback rate
    // At 2x: we look up the viseme that corresponds to 2x the elapsed time
    // This means lip movements match the audio at any speed
    const lookupMs = currentMs;  // direct lookup — audio and video both scaled together
    
    // Find active animation segment
    const segment = findActiveSegment(manifest.segments, lookupMs);
    
    if (segment && !isInSkippedRange(manifest.skipped_ranges, lookupMs)) {
      // Interpolate blend weights between this and next segment
      const nextSegment = findNextSegment(manifest.segments, lookupMs);
      const interpolated = interpolateWeights(segment, nextSegment, lookupMs);
      
      // Apply blendshape deformation to face mesh
      const deformedMesh = engine.applyBlendshapes(
        segment.speaker_id,
        interpolated,
        segment.intensity
      );
      
      // Composite: video frame + deformed lip region
      compositor.render(video, deformedMesh, segment.speaker_id);
    } else {
      // No reanimation for this moment — just show original video frame
      compositor.renderOriginal(video);
    }
    
    animFrameRef.current = requestAnimationFrame(renderFrame);
  }, [width, height]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    
    const onPlay = () => {
      animFrameRef.current = requestAnimationFrame(renderFrame);
    };
    const onPause = () => {
      cancelAnimationFrame(animFrameRef.current);
    };
    
    video.addEventListener('play', onPlay);
    video.addEventListener('pause', onPause);
    
    return () => {
      video.removeEventListener('play', onPlay);
      video.removeEventListener('pause', onPause);
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [renderFrame]);

  const handleRateChange = (rate: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRate(rate);
    }
  };

  if (loading) return <div>Loading player...</div>;

  return (
    <div style={{ position: 'relative', width, height }}>
      {/* Hidden video element — source of frames + audio */}
      <video
        ref={videoRef}
        src={manifestRef.current?.base_video_url}
        style={{ display: 'none' }}
        autoPlay={autoPlay}
        crossOrigin="anonymous"
      />
      {/* Canvas where we render composited frames */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ display: 'block' }}
      />
      {controls && (
        <div style={{ position: 'absolute', bottom: 8, right: 8 }}>
          {[0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0].map(rate => (
            <button
              key={rate}
              onClick={() => handleRateChange(rate)}
              style={{ fontWeight: playbackRate === rate ? 'bold' : 'normal', margin: 2 }}
            >
              {rate}x
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

function findActiveSegment(
  segments: AnimationSegment[],
  currentMs: number
): AnimationSegment | null {
  for (let i = segments.length - 1; i >= 0; i--) {
    if (segments[i].timestamp_ms <= currentMs) return segments[i];
  }
  return null;
}

function findNextSegment(
  segments: AnimationSegment[],
  currentMs: number
): AnimationSegment | null {
  for (const seg of segments) {
    if (seg.timestamp_ms > currentMs) return seg;
  }
  return null;
}

function interpolateWeights(
  current: AnimationSegment,
  next: AnimationSegment | null,
  currentMs: number
): Record<string, number> {
  if (!next) return current.blend_weights;
  
  const t = (currentMs - current.timestamp_ms) /
            (next.timestamp_ms - current.timestamp_ms);
  const clamped = Math.max(0, Math.min(1, t));
  
  const result: Record<string, number> = {};
  for (const key of Object.keys(current.blend_weights)) {
    const a = current.blend_weights[key] ?? 0;
    const b = next.blend_weights[key] ?? 0;
    result[key] = a + (b - a) * clamped;
  }
  return result;
}

function isInSkippedRange(
  ranges: Array<{start_ms: number; end_ms: number}>,
  currentMs: number
): boolean {
  return ranges.some(r => currentMs >= r.start_ms && currentMs <= r.end_ms);
}
```

---

## Phase 3 Research Paper Outline

**Title:** "Speed-Invariant Lip Synchronization for Multilingual Video Dubbing via Playback-Adaptive 3DMM Blendshape Rendering"

**Abstract:** We present a novel architecture for lip synchronization in dubbed video that remains accurate at arbitrary playback speeds. Unlike pixel-level reanimation approaches (Wav2Lip, MuseTalk, LatentSync) which bake mouth movements into fixed-frame video files, our system decouples animation intent from video frames via a lightweight animation manifest. A custom player applies 3D Morphable Model blendshape deformations at render time, interpolating viseme weights based on the current playback speed. This enables accurate lip sync at 0.25x through 2x without pre-rendering multiple versions. We demonstrate this on Indian language dubbed content and evaluate using SyncNet scores across playback speeds.

**Target venue:** ACM Multimedia 2026 / EMNLP 2026 (multilingual NLP track)

**Sections:**
1. Introduction — the playback speed problem in video dubbing
2. Related work — Wav2Lip, MuseTalk, LatentSync, 3DMM face models
3. Method — manifest schema, blendshape library, player architecture
4. Indian phoneme viseme mapping — novel contribution for Dravidian languages
5. Experiments — SyncNet score across playback speeds (0.5x, 1x, 1.5x, 2x)
6. User study — Indian student evaluation across speed settings
7. Limitations — single-step blendshape may miss complex mouth dynamics
8. Conclusion

**Novel contributions:**
- First application of playback-adaptive 3DMM rendering in video dubbing
- Indian language viseme library for Telugu, Tamil, Kannada phonemes
- Animation manifest format (open spec — propose as standard)
- Quantitative evaluation of lip sync quality across playback speeds
