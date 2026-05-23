"""Robot action endpoints.

Only commands in the ACTIONS whitelist can be triggered — the frontend
cannot send arbitrary shell commands.

Endpoints
---------
GET  /api/actions                       list all actions + current status
POST /api/actions/{action_id}           start an action (409 if already running)
GET  /api/actions/{action_id}/status    status + output for one action
"""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import require_token

router = APIRouter(
    prefix="/api/actions",
    tags=["actions"],
    dependencies=[Depends(require_token)],
)

# ── Whitelist ─────────────────────────────────────────────────────────────────
# Edit commands/timeouts here. Never interpolate user input into these lists.

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
}

# ── In-memory state ───────────────────────────────────────────────────────────

class ActionState:
    def __init__(self) -> None:
        self.running: bool = False
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.exit_code: Optional[int] = None
        self.stdout: str = ""
        self.stderr: str = ""
        self.error: Optional[str] = None
        self._process: Optional[subprocess.Popen] = None  # type: ignore[type-arg]
        self._lock = threading.Lock()

    def snapshot(self, action_id: str) -> dict:
        with self._lock:
            meta = ACTIONS[action_id]
            elapsed = None
            if self.started_at is not None:
                end = self.finished_at or time.time()
                elapsed = round(end - self.started_at, 1)
            return {
                "id": action_id,
                "label": meta["label"],
                "description": meta["description"],
                "running": self.running,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "elapsed_s": elapsed,
                "exit_code": self.exit_code,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "error": self.error,
            }


# One ActionState per whitelisted action, created at import time.
_states: Dict[str, ActionState] = {action_id: ActionState() for action_id in ACTIONS}


# ── Background runner ─────────────────────────────────────────────────────────

def _run_action(action_id: str, state: ActionState) -> None:
    """Execute the action in a background thread, capture output."""
    meta = ACTIONS[action_id]
    try:
        proc = subprocess.Popen(
            meta["command"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with state._lock:
            state._process = proc

        try:
            stdout_b, stderr_b = proc.communicate(timeout=meta["timeout"])
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_b, stderr_b = proc.communicate()
            with state._lock:
                state.stderr = stderr_b.decode(errors="replace")
                state.stdout = stdout_b.decode(errors="replace")
                state.error = f"Timed out after {meta['timeout']}s"
            return

        with state._lock:
            state.exit_code = proc.returncode
            state.stdout = stdout_b.decode(errors="replace")
            state.stderr = stderr_b.decode(errors="replace")
            if proc.returncode != 0:
                state.error = f"Exited with code {proc.returncode}"

    except FileNotFoundError:
        with state._lock:
            state.error = f"Executable not found: {meta['command'][0]}"
    except Exception as exc:
        with state._lock:
            state.error = str(exc)
    finally:
        with state._lock:
            state.running = False
            state.finished_at = time.time()
            state._process = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_actions() -> list:
    return [_states[aid].snapshot(aid) for aid in ACTIONS]


@router.post("/{action_id}")
def start_action(action_id: str) -> dict:
    if action_id not in ACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown action")

    state = _states[action_id]
    with state._lock:
        if state.running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Action '{action_id}' is already running.",
            )
        # Reset state for a fresh run.
        state.running = True
        state.started_at = time.time()
        state.finished_at = None
        state.exit_code = None
        state.stdout = ""
        state.stderr = ""
        state.error = None
        state._process = None

    t = threading.Thread(target=_run_action, args=(action_id, state), daemon=True)
    t.start()

    return {"ok": True, "action_id": action_id, "started_at": state.started_at}


@router.get("/{action_id}/status")
def action_status(action_id: str) -> dict:
    if action_id not in ACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown action")
    return _states[action_id].snapshot(action_id)
