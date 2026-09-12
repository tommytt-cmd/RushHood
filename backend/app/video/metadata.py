from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class VideoMetadataError(RuntimeError):
    pass


def extract_metadata(file_path: str) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration",
        "-of",
        "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VideoMetadataError(result.stderr or "ffprobe failed")

    data = json.loads(result.stdout)
    stream = data.get("streams", [{}])[0]
    duration = float(stream.get("duration", 0) or 0)
    width = int(stream.get("width", 0) or 0)
    height = int(stream.get("height", 0) or 0)
    fps = 0.0
    frame_rate = stream.get("r_frame_rate")
    if isinstance(frame_rate, str) and "/" in frame_rate:
        numerator, denominator = frame_rate.split("/", 1)
        try:
            fps = float(numerator) / float(denominator) if float(denominator) else 0.0
        except ValueError:
            fps = 0.0

    return {
        "duration_seconds": round(duration, 3),
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "filesize": Path(file_path).stat().st_size,
    }
