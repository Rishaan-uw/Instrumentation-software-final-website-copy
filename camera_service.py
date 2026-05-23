#!/usr/bin/env python3
"""
Robot-side camera switching service.

Runs on the rover Pi, listens on port 9000.
Manages a single mjpg_streamer process that is swapped between cameras on demand.
The base-station website calls this service to switch the active camera; the MJPEG
stream URL (port 8080) stays constant so the browser's <img> never re-connects.

Run on the rover:
    uvicorn camera_service:app --host 0.0.0.0 --port 9000

Protect with a shared token by setting the environment variable:
    export CAMERA_SVC_TOKEN="your-secret-token"
Then the website backend must send header:  X-Camera-Token: your-secret-token
Leave unset to disable auth (dev/local testing).
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from threading import Lock

from fastapi import FastAPI, Header, HTTPException, status

app = FastAPI(title="Husky Camera Service", version="0.1.0")
lock = Lock()

# ── Config ────────────────────────────────────────────────────────────────────

STREAM_PORT = 8080
_TOKEN = os.environ.get("CAMERA_SVC_TOKEN", "")

# Edit these to match the exact mjpg_streamer commands used on the rover.
# Key = camera_id that the website sends, value = full argv list for Popen.
CAMERAS: dict[str, list[str]] = {
    "video0": [
        "mjpg_streamer",
        "-i", "input_uvc.so -d /dev/video0 -r 1280x720 -f 15",
        "-o", f"output_http.so -p {STREAM_PORT} -w /usr/local/www",
    ],
    "video2": [
        "mjpg_streamer",
        "-i", "input_uvc.so -d /dev/video2 -r 1280x720 -f 15",
        "-o", f"output_http.so -p {STREAM_PORT} -w /usr/local/www",
    ],
    "video4": [
        "mjpg_streamer",
        "-i", "input_uvc.so -d /dev/video4 -r 1280x720 -f 15",
        "-o", f"output_http.so -p {STREAM_PORT} -w /usr/local/www",
    ],
}

# ── Internal state ─────────────────────────────────────────────────────────────

current_camera: str | None = None
current_process: subprocess.Popen | None = None  # type: ignore[type-arg]

# ── Helpers ────────────────────────────────────────────────────────────────────


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait_port_closed(port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _port_is_open(port):
            return
        time.sleep(0.1)
    raise RuntimeError(f"port {port} did not close within {timeout}s")


def _wait_port_open(port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_is_open(port):
            return
        time.sleep(0.1)
    raise RuntimeError(f"port {port} did not open within {timeout}s")


def _stop_current() -> None:
    global current_camera, current_process
    if current_process is None:
        current_camera = None
        return
    current_process.terminate()
    try:
        current_process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        current_process.kill()
        current_process.wait(timeout=3)
    current_process = None
    current_camera = None
    _wait_port_closed(STREAM_PORT)


def _check_token(x_camera_token: str = Header(default="")) -> None:
    if _TOKEN and x_camera_token != _TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid token")


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.post("/camera/{camera_id}/activate")
def activate_camera(camera_id: str, x_camera_token: str = Header(default="")) -> dict:
    _check_token(x_camera_token)
    global current_camera, current_process

    if camera_id not in CAMERAS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown camera")

    with lock:
        if (
            current_camera == camera_id
            and current_process is not None
            and current_process.poll() is None
        ):
            return {"ok": True, "active_camera": current_camera, "changed": False}

        _stop_current()

        current_process = subprocess.Popen(CAMERAS[camera_id])
        current_camera = camera_id

        try:
            _wait_port_open(STREAM_PORT)
        except Exception:
            _stop_current()
            raise

        return {"ok": True, "active_camera": current_camera, "changed": True}


@app.post("/camera/stop")
def stop_camera(x_camera_token: str = Header(default="")) -> dict:
    _check_token(x_camera_token)
    with lock:
        _stop_current()
        return {"ok": True, "active_camera": None}


@app.get("/camera/status")
def camera_status() -> dict:
    running = current_process is not None and current_process.poll() is None
    return {
        "active_camera": current_camera if running else None,
        "running": running,
        "stream_url": f"http://<robot-ip>:{STREAM_PORT}/?action=stream" if running else None,
    }
