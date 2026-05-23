"""Camera abstraction for microscope and overview feeds.

Local devices use OpenCV ``VideoCapture``. HTTP(S) MJPEG URLs use a
passthrough path (OpenCV often fails on ``?action=stream`` URLs).
"""

from __future__ import annotations

import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Union

import numpy as np

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore


@dataclass
class CameraInfo:
    id: str
    label: str
    device: str
    available: bool


class Camera:
    def __init__(self, cam_id: str, label: str, device: str) -> None:
        self.id = cam_id
        self.label = label
        self.device = device
        self._cap = None
        self._lock = threading.Lock()
        self._open()

    def _open(self) -> None:
        if cv2 is None:
            return
        try:
            device = self.device
            if device.isdigit():
                cap = cv2.VideoCapture(int(device))
            elif device.startswith(("http://", "https://")):
                cap = None
                if hasattr(cv2, "CAP_FFMPEG"):
                    cap = cv2.VideoCapture(device, cv2.CAP_FFMPEG)
                if cap is None or not cap.isOpened():
                    if cap is not None:
                        cap.release()
                    cap = cv2.VideoCapture(device)
            else:
                cap = cv2.VideoCapture(device)
            if cap.isOpened():
                self._cap = cap
            else:
                cap.release()
        except Exception:
            self._cap = None

    @property
    def available(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def info(self) -> CameraInfo:
        return CameraInfo(id=self.id, label=self.label, device=self.device, available=self.available)

    def read_jpeg(self, quality: int = 70) -> bytes:
        with self._lock:
            frame = None
            if self.available:
                ok, frame = self._cap.read()  # type: ignore[union-attr]
                if not ok:
                    frame = None
            if frame is None:
                frame = _placeholder_frame(self.label)
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])  # type: ignore[union-attr]
            if not ok:
                return b""
            return buf.tobytes()

    def stream(self, fps: int, quality: int) -> Iterator[bytes]:
        period = 1.0 / max(fps, 1)
        boundary = b"--frame"
        while True:
            jpeg = self.read_jpeg(quality)
            if jpeg:
                yield (
                    boundary
                    + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                    + str(len(jpeg)).encode()
                    + b"\r\n\r\n"
                    + jpeg
                    + b"\r\n"
                )
            time.sleep(period)

    def mjpeg_stream(self, fps: int, quality: int) -> tuple[str, Iterator[bytes]]:
        return ("multipart/x-mixed-replace; boundary=frame", self.stream(fps, quality))

    def release(self) -> None:
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None


def _placeholder_frame(label: str) -> np.ndarray:
    h, w = 360, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = (24, 24, 32)
    if cv2 is not None:
        text = f"{label}: no signal"
        size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        x = (w - size[0]) // 2
        y = (h + size[1]) // 2
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    return img


def _encode_placeholder_jpeg(label: str, quality: int) -> bytes:
    frame = _placeholder_frame(label)
    if cv2 is None:
        return b""
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return buf.tobytes() if ok else b""


def _http_user_agent() -> str:
    return "Mozilla/5.0 (compatible; HuskyScience/1.0)"


def _extract_first_jpeg_from_url(url: str, max_bytes: int = 2_000_000) -> bytes:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _http_user_agent()})
        with urllib.request.urlopen(req, timeout=10) as resp:
            buf = b""
            while len(buf) < max_bytes:
                chunk = resp.read(8192)
                if not chunk:
                    break
                buf += chunk
                start = buf.find(b"\xff\xd8")
                if start == -1:
                    continue
                end = buf.find(b"\xff\xd9", start + 2)
                if end != -1:
                    return buf[start : end + 1]
    except Exception:
        pass
    return b""


class HttpMjpegCamera:
    def __init__(self, cam_id: str, label: str, url: str) -> None:
        self.id = cam_id
        self.label = label
        self.device = url
        self._available = False
        # Probe in a background thread so a robot being offline never blocks startup.
        t = threading.Thread(target=self._probe_async, daemon=True)
        t.start()

    def _probe_async(self) -> None:
        try:
            req = urllib.request.Request(self.device, headers={"User-Agent": _http_user_agent()})
            with urllib.request.urlopen(req, timeout=3) as resp:
                chunk = resp.read(2048)
                self._available = len(chunk) > 0
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def info(self) -> CameraInfo:
        return CameraInfo(id=self.id, label=self.label, device=self.device, available=self.available)

    def _snapshot_substitute_url(self) -> Optional[str]:
        if "action=stream" in self.device:
            return self.device.replace("action=stream", "action=snapshot", 1)
        return None

    def read_jpeg(self, quality: int = 70) -> bytes:
        snap = self._snapshot_substitute_url()
        if snap:
            try:
                req = urllib.request.Request(snap, headers={"User-Agent": _http_user_agent()})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = resp.read()
                    if data.startswith(b"\xff\xd8"):
                        return data
            except Exception:
                pass
        jpeg = _extract_first_jpeg_from_url(self.device)
        if jpeg:
            return jpeg
        return _encode_placeholder_jpeg(self.label, quality)

    def mjpeg_stream(self, fps: int, quality: int) -> tuple[str, Iterator[bytes]]:
        del quality
        content_type = "multipart/x-mixed-replace; boundary=frame"

        # Try to connect to the robot stream with a short timeout so the
        # browser does not hang indefinitely when the robot is offline.
        try:
            req = urllib.request.Request(self.device, headers={"User-Agent": _http_user_agent()})
            resp = urllib.request.urlopen(req, timeout=4)
            detected_ct = resp.headers.get("Content-Type", content_type)

            def live_gen() -> Iterator[bytes]:
                try:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    resp.close()

            return detected_ct, live_gen()

        except Exception:
            # Robot offline — stream placeholder "no signal" frames so the
            # browser <img> gets a valid MJPEG response immediately.
            period = 1.0 / max(fps, 1)

            def placeholder_gen() -> Iterator[bytes]:
                boundary = b"--frame"
                while True:
                    jpeg = _encode_placeholder_jpeg(self.label, 70)
                    if jpeg:
                        yield (
                            boundary
                            + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                            + str(len(jpeg)).encode()
                            + b"\r\n\r\n"
                            + jpeg
                            + b"\r\n"
                        )
                    time.sleep(period)

            return content_type, placeholder_gen()

    def release(self) -> None:
        pass


def _parse_camera_spec(raw: str, index: int) -> tuple[str, str]:
    s = raw.strip()
    if not s:
        raise ValueError("empty camera spec")

    positions = [s.find(m) for m in ("https://", "http://")]
    positions = [p for p in positions if p != -1]
    url_start = min(positions) if positions else -1

    if url_start != -1:
        if url_start > 0 and s[url_start - 1] == ":":
            label = s[: url_start - 1].strip() or f"cam{index}"
            device = s[url_start:].strip()
        else:
            label = f"cam{index}"
            device = s.strip() if url_start == 0 else s[url_start:].strip()
        return label, device

    if ":" in s:
        label, device = s.split(":", 1)
    else:
        label, device = f"cam{index}", s
    return label.strip() or f"cam{index}", device.strip()


class CameraManager:
    def __init__(self, specs: Iterable[str]) -> None:
        self._cameras: Dict[str, Union[Camera, HttpMjpegCamera]] = {}
        for i, raw in enumerate(specs):
            label, device = _parse_camera_spec(raw, i)
            cam_id = label.lower().replace(" ", "_") or f"cam{i}"
            if device.startswith(("http://", "https://")):
                self._cameras[cam_id] = HttpMjpegCamera(cam_id, label or cam_id, device)
            else:
                self._cameras[cam_id] = Camera(cam_id, label or cam_id, device)

    def list(self) -> List[CameraInfo]:
        return [c.info() for c in self._cameras.values()]

    def get(self, cam_id: str) -> Optional[Union[Camera, HttpMjpegCamera]]:
        return self._cameras.get(cam_id)

    def release_all(self) -> None:
        for cam in self._cameras.values():
            cam.release()
