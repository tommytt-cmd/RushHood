from __future__ import annotations

import time
from typing import List, Dict, Any

from app.ai.detector import Detector
from app.ai.tracker import SimpleTracker
from app.ai.counter import LineCounter
from app.ai.thumbnail import extract_thumbnail
from app.ai.exporter import export_timeline, export_metadata
from app.ai.timeline import build_timeline


class VideoProcessor:
    def __init__(self, model_path: str | None = None, conf: float = 0.3, lines: Dict[str, dict] | None = None):
        self.detector = Detector(model_path=model_path, conf=conf)
        self.tracker = SimpleTracker()
        self.lines = lines or {}
        self.counter = LineCounter(self.lines)

    def process(self, video_path: str, out_dir: str) -> dict:
        start = time.time()
        try:
            import cv2
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("OpenCV (cv2) is required for video processing") from exc

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("Unable to open video")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        events: List[dict] = []
        prev_bboxes: Dict[int, tuple] = {}

        frame_no = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            detections = self.detector.detect(frame)
            # convert to simple tuples
            dets = [(d.x1, d.y1, d.x2, d.y2, d.class_name) for d in detections]
            tracks = self.tracker.update(dets, frame_no)
            for t in tracks:
                prev = prev_bboxes.get(t.track_id)
                evs = self.counter.process(t.track_id, prev, t.bbox)
                for e in evs:
                    events.append({
                        "timestamp": frame_no / fps,
                        "vehicle_id": f"veh_{t.track_id:06d}",
                        "vehicle_type": t.class_name,
                        "direction": "unknown",
                        "line_id": e["line_id"],
                        "count": e["count"],
                        "event_id": f"evt_{len(events)+1:06d}",
                    })
                prev_bboxes[t.track_id] = t.bbox
            frame_no += 1

        cap.release()

        # generate thumbnail
        thumb_path = f"{out_dir}/thumbnail.jpg"
        try:
            extract_thumbnail(video_path, thumb_path)
        except Exception:
            thumb_path = ""

        timeline = build_timeline(events)
        timeline_path = f"{out_dir}/timeline.json"
        export_timeline(timeline, timeline_path)
        metadata = {
            "duration": total / (fps or 1),
            "fps": fps,
            "total_frames": total,
            "total_vehicles": sum(self.counter.cumulative.values()),
            "counts_by_type": {},
            "processing_time": time.time() - start,
            "model_version": self.detector.model_path or "none",
        }
        metadata_path = f"{out_dir}/metadata.json"
        export_metadata(metadata, metadata_path)

        return {"timeline": timeline_path, "metadata": metadata_path, "thumbnail": thumb_path}
