import cv2
import numpy as np
import structlog

log = structlog.get_logger()

PSNR_THRESHOLD_DB = 35.0
FEATHER_RADIUS = 21


def compute_psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse < 1e-10:
        return float("inf")
    return 20.0 * np.log10(255.0 / np.sqrt(mse))


def build_lip_mask(
    frame: np.ndarray,
    mouth_landmarks: list[tuple[int, int]],
    feather: int = FEATHER_RADIUS
) -> np.ndarray:
    h, w = frame.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    if not mouth_landmarks:
        return mask

    pts = np.array(mouth_landmarks, dtype=np.int32)
    hull = cv2.convexHull(pts)
    cv2.fillConvexPoly(mask, hull, 255)
    mask = cv2.GaussianBlur(mask, (feather | 1, feather | 1), feather // 3)
    return mask


def composite_frame(
    original: np.ndarray,
    reanimated: np.ndarray,
    lip_mask: np.ndarray,
    confidence: float = 1.0
) -> tuple[np.ndarray, bool, float]:
    """
    Returns (composited, quality_ok, psnr_non_lip)
    quality_ok=False means PSNR guard triggered — caller should revert.
    """
    alpha = (lip_mask.astype(np.float64) / 255.0) * np.clip(confidence, 0, 1)
    alpha_3 = np.stack([alpha, alpha, alpha], axis=2)

    orig_f = original.astype(np.float64)
    reanim_f = reanimated.astype(np.float64)
    composited = (reanim_f * alpha_3 + orig_f * (1.0 - alpha_3)).astype(np.uint8)

    non_lip = lip_mask < 10
    if non_lip.sum() > 100:
        psnr = compute_psnr(original[non_lip], composited[non_lip])
    else:
        psnr = float("inf")

    quality_ok = psnr >= PSNR_THRESHOLD_DB
    if not quality_ok:
        log.warning("psnr_guard_triggered",
                    psnr=round(psnr, 2),
                    threshold=PSNR_THRESHOLD_DB)

    return composited, quality_ok, round(psnr, 2)


def apply_temporal_smoothing(
    frames: list[np.ndarray],
    lip_masks: list[np.ndarray],
    window: int = 3
) -> list[np.ndarray]:
    if len(frames) <= 1:
        return frames

    smoothed = []
    for i, (frame, mask) in enumerate(zip(frames, lip_masks)):
        start = max(0, i - window // 2)
        end = min(len(frames), i + window // 2 + 1)

        weights = []
        neighbors = []
        for j in range(start, end):
            w = 1.0 / (abs(j - i) + 1)
            weights.append(w)
            neighbors.append(frames[j])

        total = sum(weights)
        blended = sum(
            (w / total) * f.astype(np.float64)
            for w, f in zip(weights, neighbors)
        ).astype(np.uint8)

        # Only smooth the lip region — leave rest untouched
        alpha = (mask.astype(np.float64) / 255.0)
        alpha_3 = np.stack([alpha, alpha, alpha], axis=2)
        result = (blended * alpha_3 + frame * (1.0 - alpha_3)).astype(np.uint8)
        smoothed.append(result)

    return smoothed


def composite_video_chunks(
    original_frames_dir: str,
    reanimated_frames_dir: str,
    mouth_landmarks_per_frame: dict[int, list],
    output_frames_dir: str,
    confidence: float = 0.9
) -> dict:
    import os

    os.makedirs(output_frames_dir, exist_ok=True)
    original_files = sorted(os.listdir(original_frames_dir))

    stats = {
        "frames_total": len(original_files),
        "frames_composited": 0,
        "frames_reverted": 0,
        "psnr_values": []
    }

    reverted_count = 0

    for idx, fname in enumerate(original_files):
        orig_path = os.path.join(original_frames_dir, fname)
        reanim_path = os.path.join(reanimated_frames_dir, fname)
        out_path = os.path.join(output_frames_dir, fname)

        orig = cv2.imread(orig_path)
        if orig is None:
            continue

        if not os.path.exists(reanim_path):
            cv2.imwrite(out_path, orig)
            continue

        reanim = cv2.imread(reanim_path)
        if reanim is None:
            cv2.imwrite(out_path, orig)
            continue

        lms = mouth_landmarks_per_frame.get(idx, [])
        mask = build_lip_mask(orig, lms)

        composited, quality_ok, psnr = composite_frame(orig, reanim, mask, confidence)

        if quality_ok:
            cv2.imwrite(out_path, composited)
            stats["frames_composited"] += 1
            stats["psnr_values"].append(psnr)
        else:
            cv2.imwrite(out_path, orig)
            stats["frames_reverted"] += 1
            reverted_count += 1

    if reverted_count > stats["frames_total"] * 0.3:
        log.warning("high_revert_rate",
                    reverted=reverted_count,
                    total=stats["frames_total"],
                    note="Consider marking entire scene as SKIP")

    stats["avg_psnr"] = (
        round(np.mean(stats["psnr_values"]), 2)
        if stats["psnr_values"] else 0.0
    )
    del stats["psnr_values"]

    return stats
