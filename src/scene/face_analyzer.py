from dataclasses import dataclass

import cv2
import numpy as np
import structlog

log = structlog.get_logger()

_face_detection = None
_face_mesh = None


def _get_face_detection():
    global _face_detection
    if _face_detection is None:
        import mediapipe as mp
        _face_detection = mp.solutions.face_detection.FaceDetection(
            min_detection_confidence=0.5,
            model_selection=1
        )
    return _face_detection


def _get_face_mesh():
    global _face_mesh
    if _face_mesh is None:
        import mediapipe as mp
        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    return _face_mesh


@dataclass
class FaceAnalysis:
    face_count: int
    confidence: float
    yaw_deg: float
    pitch_deg: float
    roll_deg: float
    occlusion_score: float
    face_area_pct: float
    face_bbox: tuple | None
    mouth_landmarks: list


# Mouth landmark indices in MediaPipe FaceMesh (468 landmarks)
MOUTH_UPPER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409]
MOUTH_LOWER = [146, 91, 181, 84, 17, 314, 405, 321, 375, 291]
MOUTH_ALL = MOUTH_UPPER + MOUTH_LOWER


def analyze_frame(frame: np.ndarray) -> FaceAnalysis:
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    detection = _get_face_detection()
    det_results = detection.process(rgb)

    if not det_results.detections:
        return FaceAnalysis(
            face_count=0, confidence=0.0,
            yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0,
            occlusion_score=0.0, face_area_pct=0.0,
            face_bbox=None, mouth_landmarks=[]
        )

    face_count = len(det_results.detections)
    best = det_results.detections[0]
    conf = best.score[0]
    bbox = best.location_data.relative_bounding_box
    area = bbox.width * bbox.height

    mesh = _get_face_mesh()
    mesh_results = mesh.process(rgb)

    yaw, pitch, roll = 0.0, 0.0, 0.0
    occlusion = 0.0
    mouth_lms = []

    if mesh_results.multi_face_landmarks:
        lms = mesh_results.multi_face_landmarks[0].landmark
        yaw, pitch, roll = _estimate_head_pose(lms, w, h)
        occlusion = _estimate_mouth_occlusion(lms, w, h)
        mouth_lms = [
            (int(lms[i].x * w), int(lms[i].y * h))
            for i in MOUTH_ALL
        ]

    return FaceAnalysis(
        face_count=face_count,
        confidence=round(conf, 3),
        yaw_deg=round(yaw, 1),
        pitch_deg=round(pitch, 1),
        roll_deg=round(roll, 1),
        occlusion_score=round(occlusion, 3),
        face_area_pct=round(area, 4),
        face_bbox=(bbox.xmin, bbox.ymin, bbox.width, bbox.height),
        mouth_landmarks=mouth_lms
    )


def _estimate_head_pose(landmarks, w: int, h: int) -> tuple[float, float, float]:
    # 3D model points for standard face
    model_points = np.array([
        (0.0, 0.0, 0.0),          # Nose tip — landmark 1
        (0.0, -330.0, -65.0),     # Chin — landmark 152
        (-225.0, 170.0, -135.0),  # Left eye corner — landmark 263
        (225.0, 170.0, -135.0),   # Right eye corner — landmark 33
        (-150.0, -150.0, -125.0), # Left mouth — landmark 287
        (150.0, -150.0, -125.0),  # Right mouth — landmark 57
    ], dtype=np.float64)

    key_indices = [1, 152, 263, 33, 287, 57]
    image_points = np.array([
        (landmarks[i].x * w, landmarks[i].y * h)
        for i in key_indices
    ], dtype=np.float64)

    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1))

    success, rotation_vec, _ = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0.0, 0.0, 0.0

    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    pose_mat = cv2.hconcat([rotation_mat, np.zeros((3, 1))])
    _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)

    pitch = float(euler[0])
    yaw = float(euler[1])
    roll = float(euler[2])

    return yaw, pitch, roll


def _estimate_mouth_occlusion(landmarks, w: int, h: int) -> float:
    visibilities = [landmarks[i].visibility for i in MOUTH_ALL
                    if hasattr(landmarks[i], 'visibility')]

    if visibilities:
        avg_vis = np.mean(visibilities)
        return round(max(0.0, 1.0 - avg_vis), 3)

    return 0.0


def sample_frames(frames_dir: str, max_samples: int = 8) -> list[np.ndarray]:
    import os
    files = sorted([
        f for f in os.listdir(frames_dir)
        if f.endswith((".jpg", ".png"))
    ])
    if not files:
        return []
    step = max(1, len(files) // max_samples)
    sampled = files[::step][:max_samples]
    frames = []
    for f in sampled:
        img = cv2.imread(os.path.join(frames_dir, f))
        if img is not None:
            frames.append(img)
    return frames
