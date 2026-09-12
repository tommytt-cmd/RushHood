from __future__ import annotations

from pathlib import Path
from typing import Tuple


def extract_thumbnail(video_path: str, out_path: str, time_sec: float | None = None) -> Tuple[str, int]:
    try:
        import cv2
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("OpenCV (cv2) is required for thumbnail extraction") from exc

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Unable to open video for thumbnail extraction")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if time_sec is None:
        frame_no = max(0, total // 2)
    else:
        frame_no = int(time_sec * fps)
    frame_no = min(frame_no, total - 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    if not ret or frame is None:
        raise RuntimeError("Failed to read frame for thumbnail")
    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(out_path, frame)
    cap.release()
    if not ok:
        raise RuntimeError("Failed to write thumbnail image")
    return out_path, frame_no
