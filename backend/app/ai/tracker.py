from __future__ import annotations

from typing import Dict, List, Tuple
from dataclasses import dataclass
import math


@dataclass
class Track:
    track_id: int
    bbox: Tuple[int, int, int, int]
    class_name: str
    last_seen: int


class SimpleTracker:
    def __init__(self, max_lost: int = 30, iou_threshold: float = 0.3):
        self.next_id = 1
        self.tracks: Dict[int, Track] = {}
        self.max_lost = max_lost
        self.iou_threshold = iou_threshold

    def _iou(self, a, b):
        x1 = max(a[0], b[0])
        y1 = max(a[1], b[1])
        x2 = min(a[2], b[2])
        y2 = min(a[3], b[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0

    def update(self, detections: List[Tuple[int, int, int, int, str]], frame_no: int) -> List[Track]:
        # detections: list of (x1,y1,x2,y2,class_name)
        assigned = set()
        updated_tracks: Dict[int, Track] = {}
        for tid, t in list(self.tracks.items()):
            best_iou = 0
            best_det = None
            for i, d in enumerate(detections):
                if i in assigned:
                    continue
                iou = self._iou(t.bbox, d[:4])
                if iou > best_iou:
                    best_iou = iou
                    best_det = (i, d)
            if best_iou >= self.iou_threshold and best_det is not None:
                i, d = best_det
                assigned.add(i)
                t.bbox = d[:4]
                t.class_name = d[4]
                t.last_seen = frame_no
                updated_tracks[tid] = t
            else:
                # keep track but may expire
                if frame_no - t.last_seen <= self.max_lost:
                    updated_tracks[tid] = t

        # create new tracks for unassigned detections
        for i, d in enumerate(detections):
            if i in assigned:
                continue
            tid = self.next_id
            self.next_id += 1
            t = Track(track_id=tid, bbox=d[:4], class_name=d[4], last_seen=frame_no)
            updated_tracks[tid] = t

        self.tracks = updated_tracks
        return list(self.tracks.values())
