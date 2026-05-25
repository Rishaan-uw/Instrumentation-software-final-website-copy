"""Pi-side robot service — port 9001.

Owns whitelisted executables, CSV reads, and single-job concurrency.
Deploy to the Pi as /home/robot/robot_service.py

Run:
    cd /home/robot
    source csv-api-venv/bin/activate   # or your venv with fastapi/uvicorn
    ROBOT_SERVICE_TOKEN="" python3 -m uvicorn robot_service:app --host 0.0.0.0 --port 9001

Optional env:
    ROBOT_SERVICE_TOKEN  — if set, require X-Robot-Token or Bearer token on requests.
"""

from __future__ import annotations

import csv
import math
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# ── Whitelisted actions ───────────────────────────────────────────────────────

ACTIONS: Dict[str, dict] = {
    "fluids_processing": {
        "label": "Fluids Processing",
        "description": "Run centrifuge, pump, and fluid transfer process.",
        "command": ["/home/robot/HR-pi/C_Code/SystemsTesting/Automation/centrifugeFluids"],
        "timeout": 180,
    },
    "dirt_sample": {
        "label": "Dirt Sample",
        "description": "Collect and deposit dirt sample using augur/column.",
        "command": ["/home/robot/HR-pi/C_Code/SystemsTesting/Automation/dirtSample"],
        "timeout": 240,
    },
    "mixing_chamber": {
        "label": "Mixing Chamber",
        "description": "Run the mixing chamber automation sequence.",
        "command": ["/home/robot/HR-pi/C_Code/SystemsTesting/Automation/mixingChamberAutomation"],
        "timeout": 180,
    },
    "calibrate_spectrometer": {
        "label": "Calibrate Spectrometer",
        "description": "Run spectrometer calibration.",
        "command": ["/home/robot/HR-pi/Executables/calibrate_spectrometer"],
        "timeout": 180,
    },
}

PEAK_COLOR_COLUMNS = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue"]
PEAK_RANGES_NM = {
    "Red": "~620-750 nm",
    "Orange": "~590-620 nm",
    "Yellow": "~570-590 nm",
    "Green": "~495-570 nm",
    "Cyan": "~485-500 nm",
    "Blue": "~450-495 nm",
}

SENSORS: Dict[str, dict] = {
    "color_read": {
        "label": "Color Read / Organics",
        "command": ["/home/robot/HR-pi/Executables/colorRead"],
        "csv_path": "/home/robot/HR-pi/output_data/colorReadTest.csv",
        "timeout": 120,
        "csv_timeout": 60,
    },
    "peaks_colors": {
        "label": "Peak Colors / Spectrometer",
        "command": ["/home/robot/HR-pi/Executables/stream_spec_final"],
        "csv_path": "/home/robot/HR-pi/output_data/peaks_colors.csv",
        "timeout": 180,
        "csv_timeout": 90,
    },
    "temp_humidity": {
        "label": "Temperature & Humidity",
        "command": ["/home/robot/HR-pi/Executables/tempSensorRead"],
        "csv_path": "/home/robot/HR-pi/output_data/TempAndHumidity.csv",
        "timeout": 60,
        "csv_timeout": 30,
    },
}

ROBOT_TOKEN = os.environ.get("ROBOT_SERVICE_TOKEN", "").strip()


# ── CSV helpers ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CsvMarker:
    exists: bool
    mtime: float
    size: int
    row_count: int


def csv_marker(path: str) -> CsvMarker:
    if not os.path.exists(path):
        return CsvMarker(False, 0.0, 0, 0)
    st = os.stat(path)
    return CsvMarker(True, st.st_mtime, st.st_size, _count_rows(path))


def _count_rows(path: str) -> int:
    try:
        with open(path, newline="") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def read_latest_csv_row(path: str) -> Optional[Dict[str, str]]:
    if not os.path.exists(path):
        return None

    # Standard comma-separated CSV with header.
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            last: Optional[Dict[str, str]] = None
            for row in reader:
                last = row
            if last is not None:
                return last
    except OSError:
        return None

    # Single-column files (e.g. colorReadTest: header + value, no commas).
    try:
        with open(path, newline="") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if len(lines) >= 2:
            header = lines[0]
            value = lines[-1]
            if "," not in header and "," not in value:
                return {header: value}
    except OSError:
        return None
    return None


def parse_number(value: str | None) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "-nan", "none", "null"}:
        return None
    try:
        num = float(text)
    except ValueError:
        return None
    if not math.isfinite(num):
        return None
    return num


def wait_for_csv_update(
    path: str,
    previous: CsvMarker,
    timeout: float,
    poll_interval: float = 0.25,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = csv_marker(path)
        if not current.exists:
            time.sleep(poll_interval)
            continue
        if not previous.exists:
            return True
        if current.mtime > previous.mtime + 1e-6:
            return True
        if current.size != previous.size:
            return True
        if current.row_count > previous.row_count:
            return True
        time.sleep(poll_interval)
    return False


def run_command_with_timeout(command: List[str], timeout: float) -> Tuple[int, str, str, Optional[str]]:
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout_b, stderr_b = proc.communicate(timeout=timeout)
        stdout = stdout_b.decode(errors="replace")
        stderr = stderr_b.decode(errors="replace")
        err: Optional[str] = None
        if proc.returncode != 0:
            err = f"Exited with code {proc.returncode}"
        return proc.returncode or 0, stdout, stderr, err
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout_b, stderr_b = proc.communicate()
        return (
            -1,
            stdout_b.decode(errors="replace"),
            stderr_b.decode(errors="replace"),
            f"Timed out after {timeout}s",
        )
    except FileNotFoundError:
        return -1, "", "", f"Executable not found: {command[0]}"


# ── Sensor parsers ────────────────────────────────────────────────────────────


def parse_color_read(path: str) -> Optional[dict]:
    row = read_latest_csv_row(path)
    if row is None:
        return None
    pct = parse_number(row.get("pct_diff"))
    if pct is None:
        return None
    return {"pct_diff": pct}


def parse_peaks_colors(path: str) -> Optional[dict]:
    row = read_latest_csv_row(path)
    if row is None:
        return None
    peaks: Dict[str, float] = {}
    for col in PEAK_COLOR_COLUMNS:
        val = parse_number(row.get(col, ""))
        if val is None:
            return None
        peaks[col] = val
    return {"peaks": peaks, "ranges_nm": dict(PEAK_RANGES_NM)}


def parse_temp_humidity(path: str) -> Optional[dict]:
    row = read_latest_csv_row(path)
    if row is None:
        return None
    temp = parse_number(row.get("Temperature", row.get("temperature", "")))
    hum = parse_number(row.get("Humidity", row.get("humidity", "")))
    if temp is None or hum is None:
        return None
    return {"temperature": temp, "humidity": hum}


SENSOR_PARSERS: Dict[str, Callable[[str], Optional[dict]]] = {
    "color_read": parse_color_read,
    "peaks_colors": parse_peaks_colors,
    "temp_humidity": parse_temp_humidity,
}


# ── Single global job runner ───────────────────────────────────────────────────


class JobRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.busy = False
        self.kind: Optional[str] = None  # "action" | "sensor"
        self.job_id: Optional[str] = None
        self.running = False
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.exit_code: Optional[int] = None
        self.stdout = ""
        self.stderr = ""
        self.error: Optional[str] = None
        self.result: Optional[dict] = None
        self._thread: Optional[threading.Thread] = None

    def _busy_conflict(self) -> None:
        if self.busy:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Robot busy ({self.kind}:{self.job_id})",
            )

    def start_action(self, action_id: str) -> None:
        if action_id not in ACTIONS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown action")
        with self._lock:
            self._busy_conflict()
            self._reset_job("action", action_id)
            self._thread = threading.Thread(
                target=self._run_action,
                args=(action_id,),
                daemon=True,
            )
            self._thread.start()

    def start_sensor_sample(self, sensor_id: str) -> None:
        if sensor_id not in SENSORS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown sensor")
        with self._lock:
            self._busy_conflict()
            self._reset_job("sensor", sensor_id)
            self._thread = threading.Thread(
                target=self._run_sensor_sample,
                args=(sensor_id,),
                daemon=True,
            )
            self._thread.start()

    def _reset_job(self, kind: str, job_id: str) -> None:
        self.busy = True
        self.kind = kind
        self.job_id = job_id
        self.running = True
        self.started_at = time.time()
        self.finished_at = None
        self.exit_code = None
        self.stdout = ""
        self.stderr = ""
        self.error = None
        self.result = None

    def _finish(self) -> None:
        with self._lock:
            if (
                self.kind == "sensor"
                and self.job_id
                and self.result
                and not self.error
            ):
                _sensor_cache[self.job_id] = self.result
            self.running = False
            self.finished_at = time.time()
            self.busy = False

    def _run_action(self, action_id: str) -> None:
        meta = ACTIONS[action_id]
        code, out, err, error = run_command_with_timeout(meta["command"], meta["timeout"])
        with self._lock:
            self.exit_code = code
            self.stdout = out
            self.stderr = err
            self.error = error
        self._finish()

    def _run_sensor_sample(self, sensor_id: str) -> None:
        meta = SENSORS[sensor_id]
        path = meta["csv_path"]
        before = csv_marker(path)
        code, out, err, error = run_command_with_timeout(meta["command"], meta["timeout"])
        with self._lock:
            self.exit_code = code
            self.stdout = out
            self.stderr = err

        if error:
            with self._lock:
                self.error = error
            self._finish()
            return

        if not wait_for_csv_update(path, before, meta["csv_timeout"]):
            with self._lock:
                self.error = f"CSV did not update within {meta['csv_timeout']}s: {path}"
            self._finish()
            return

        parser = SENSOR_PARSERS[sensor_id]
        parsed = parser(path)
        if parsed is None:
            with self._lock:
                self.error = f"Failed to parse CSV: {path}"
            self._finish()
            return

        with self._lock:
            self.result = parsed
        self._finish()

    def job_status(self) -> dict:
        with self._lock:
            elapsed = None
            if self.started_at is not None:
                end = self.finished_at or time.time()
                elapsed = round(end - self.started_at, 1)
            return {
                "busy": self.busy,
                "kind": self.kind,
                "id": self.job_id,
                "running": self.running,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "elapsed_s": elapsed,
                "exit_code": self.exit_code,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "error": self.error,
                "result": self.result,
            }

    def action_snapshot(self, action_id: str) -> dict:
        meta = ACTIONS[action_id]
        job = self.job_status()
        is_this = job["kind"] == "action" and job["id"] == action_id
        running = is_this and job["running"]
        return {
            "id": action_id,
            "label": meta["label"],
            "description": meta["description"],
            "running": running,
            "started_at": job["started_at"] if is_this else None,
            "finished_at": job["finished_at"] if is_this else None,
            "elapsed_s": job["elapsed_s"] if is_this else None,
            "exit_code": job["exit_code"] if is_this else None,
            "stdout": job["stdout"] if is_this else "",
            "stderr": job["stderr"] if is_this else "",
            "error": job["error"] if is_this else None,
        }


_runner = JobRunner()
_sensor_cache: Dict[str, dict] = {}


# ── Auth ──────────────────────────────────────────────────────────────────────


def require_robot_token(
    x_robot_token: Optional[str] = Header(None, alias="X-Robot-Token"),
    authorization: Optional[str] = Header(None),
) -> None:
    if not ROBOT_TOKEN:
        return
    token = x_robot_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token != ROBOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Robot Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/robot/health")
async def health(_: None = Depends(require_robot_token)) -> dict:
    return {"ok": True, "service": "robot-service", "port": 9001}


@app.get("/robot/job/status")
async def job_status(_: None = Depends(require_robot_token)) -> dict:
    return _runner.job_status()


@app.get("/robot/actions")
async def list_actions(_: None = Depends(require_robot_token)) -> list:
    return [_runner.action_snapshot(aid) for aid in ACTIONS]


@app.post("/robot/actions/{action_id}/start")
async def start_action(action_id: str, _: None = Depends(require_robot_token)) -> dict:
    _runner.start_action(action_id)
    return {"ok": True, "action_id": action_id, "started_at": time.time()}


@app.get("/robot/actions/{action_id}/status")
async def action_status(action_id: str, _: None = Depends(require_robot_token)) -> dict:
    if action_id not in ACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown action")
    return _runner.action_snapshot(action_id)


@app.get("/robot/sensors")
async def list_sensors(_: None = Depends(require_robot_token)) -> list:
    return [{"id": sid, "label": meta["label"]} for sid, meta in SENSORS.items()]


@app.post("/robot/sensors/{sensor_id}/sample")
async def sample_sensor(sensor_id: str, _: None = Depends(require_robot_token)) -> dict:
    _runner.start_sensor_sample(sensor_id)
    return {"ok": True, "sensor_id": sensor_id, "started_at": time.time()}


@app.get("/robot/sensors/{sensor_id}/latest")
async def sensor_latest(sensor_id: str, _: None = Depends(require_robot_token)) -> dict:
    if sensor_id not in SENSORS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown sensor")

    job = _runner.job_status()
    if job["kind"] == "sensor" and job["id"] == sensor_id and job["result"]:
        return {"status": "ok", "data": job["result"]}

    if sensor_id in _sensor_cache:
        return {"status": "ok", "data": _sensor_cache[sensor_id]}

    path = SENSORS[sensor_id]["csv_path"]
    parsed = SENSOR_PARSERS[sensor_id](path)
    if parsed is None:
        return {"status": "no_data"}
    _sensor_cache[sensor_id] = parsed
    return {"status": "ok", "data": parsed}
