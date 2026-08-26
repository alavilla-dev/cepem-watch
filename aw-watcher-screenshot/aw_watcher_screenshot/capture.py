"""Screen capture + on-disk storage.

Images are written under the CEPEM Watch data dir; only their path + metadata go
into ActivityWatch events (never the image bytes, which would bloat the DB).
"""
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

import mss
from aw_core.dirs import get_data_dir
from PIL import Image

logger = logging.getLogger(__name__)


def images_root() -> str:
    return os.path.join(get_data_dir("aw-watcher-screenshot"), "images")


def _select_monitor_indices(sct, monitors_cfg: str) -> List[int]:
    # sct.monitors[0] is the "all monitors" virtual screen; 1..n are physical.
    n = len(sct.monitors)
    cfg = (monitors_cfg or "all").strip().lower()
    if cfg in ("", "all"):
        return list(range(1, n))
    try:
        idx = int(cfg)
        if 1 <= idx < n:
            return [idx]
    except ValueError:
        pass
    logger.warning("Invalid 'monitors' config %r; capturing all", monitors_cfg)
    return list(range(1, n))


def _downscale(img: Image.Image, max_width: int) -> Image.Image:
    if max_width and img.width > max_width:
        h = round(img.height * max_width / img.width)
        return img.resize((max_width, h), Image.LANCZOS)
    return img


def capture(
    monitors_cfg: str,
    image_format: str = "jpeg",
    jpeg_quality: int = 60,
    max_width: int = 1920,
    now: Optional[datetime] = None,
) -> List[dict]:
    """Capture the configured monitor(s), save to disk, return per-image metadata."""
    now = now or datetime.now(timezone.utc)
    fmt = (image_format or "jpeg").lower()
    ext = "jpg" if fmt in ("jpg", "jpeg") else "png"
    day_dir = os.path.join(images_root(), now.strftime("%Y-%m-%d"))
    os.makedirs(day_dir, exist_ok=True)

    results: List[dict] = []
    with mss.mss() as sct:
        for idx in _select_monitor_indices(sct, monitors_cfg):
            shot = sct.grab(sct.monitors[idx])
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            img = _downscale(img, max_width)

            ts = now.strftime("%Y-%m-%dT%H-%M-%S")
            fname = f"{ts}_mon{idx}.{ext}"
            path = os.path.join(day_dir, fname)
            if ext == "jpg":
                img.save(path, "JPEG", quality=int(jpeg_quality), optimize=True)
            else:
                img.save(path, "PNG", optimize=True)

            results.append(
                {
                    "path": os.path.relpath(path, images_root()).replace("\\", "/"),
                    "monitor": idx,
                    "width": img.width,
                    "height": img.height,
                    "bytes": os.path.getsize(path),
                    "format": ext,
                }
            )
    logger.debug("Captured %d screenshot(s)", len(results))
    return results
