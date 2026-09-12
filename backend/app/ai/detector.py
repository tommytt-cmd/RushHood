from __future__ import annotations

from typing import List
from dataclasses import dataclass

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency
    YOLO = None


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    score: float
    class_name: str


class Detector:
    def __init__(self, model_path: str | None = None, conf: float = 0.3, device: str | None = None):
        self.model_path = model_path
        self.conf = conf
        self.device = device
        self._model = None
        if YOLO is not None and model_path is not None:
            self._model = YOLO(model_path)
            if device is not None:
                try:
                    self._model.to(device)
                except Exception:
                    pass

    def detect(self, frame) -> List[Detection]:
        if self._model is None:
            return []
        results = self._model.predict(source=frame, imgsz=640, conf=self.conf, verbose=False)
        detections: List[Detection] = []
        for r in results:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue
            for b in boxes:
                cls = int(b.cls.cpu().numpy()[0]) if hasattr(b, "cls") else 0
                conf = float(b.conf.cpu().numpy()[0]) if hasattr(b, "conf") else float(b.conf)
                xyxy = b.xyxy.cpu().numpy()[0] if hasattr(b, "xyxy") else b.xyxy
                x1, y1, x2, y2 = map(int, xyxy.tolist())
                # map classes to names via model.names if available
                name = str(getattr(self._model, "names", {}).get(cls, str(cls)))
                if name in ("car", "truck", "bus", "motorbike", "motorcycle"):
                    detections.append(Detection(x1, y1, x2, y2, conf, name if name != "motorbike" else "motorcycle"))
        return detections
