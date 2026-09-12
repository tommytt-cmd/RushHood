from __future__ import annotations

from typing import Dict, Tuple


class LineCounter:
    def __init__(self, lines: Dict[str, Dict[str, int]]):
        # lines: id -> {x1,y1,x2,y2}
        self.lines = lines
        # track_id -> set of line_ids already counted
        self.counted: Dict[int, set] = {}
        # cumulative counts per line
        self.cumulative: Dict[str, int] = {lid: 0 for lid in lines.keys()}

    @staticmethod
    def _centroid(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @staticmethod
    def _on_segment(a, b, p) -> bool:
        # check if point p crosses the horizontal line between a and b
        (ax, ay), (bx, by) = a, b
        px, py = p
        # simple check for crossing when line is horizontal-ish
        if min(ay, by) <= py <= max(ay, by):
            return True
        return False

    def process(self, track_id: int, prev_bbox: Tuple[int, int, int, int] | None, bbox: Tuple[int, int, int, int]) -> list[dict]:
        events = []
        centroid = self._centroid(bbox)
        prev_centroid = self._centroid(prev_bbox) if prev_bbox is not None else None
        for lid, coords in self.lines.items():
            a = (coords["x1"], coords["y1"])
            b = (coords["x2"], coords["y2"])
            if prev_centroid is None:
                continue
            # if previously on one side and now on other side -> crossing
            was_on = self._on_segment(a, b, prev_centroid)
            now_on = self._on_segment(a, b, centroid)
            if not was_on and now_on:
                if track_id not in self.counted:
                    self.counted[track_id] = set()
                if lid not in self.counted[track_id]:
                    self.counted[track_id].add(lid)
                    self.cumulative[lid] += 1
                    events.append({"line_id": lid, "count": self.cumulative[lid]})
        return events
