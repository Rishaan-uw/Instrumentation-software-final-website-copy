"""HTTP client for the Pi robot service (port 9001)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .config import Settings


class RobotServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class RobotClient:
    def __init__(self, settings: Settings) -> None:
        self._base = settings.robot_service_url.rstrip("/")
        self._token = settings.robot_service_token.strip()
        self._timeout = settings.robot_service_timeout

    def _headers(self) -> Dict[str, str]:
        if not self._token:
            return {}
        return {"X-Robot-Token": self._token}

    def _request(
        self,
        method: str,
        path: str,
        *,
        allow_connection_error: bool = False,
    ) -> Any:
        url = f"{self._base}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.request(method, url, headers=self._headers())
        except httpx.RequestError as exc:
            if allow_connection_error:
                return None
            raise RobotServiceError(f"Robot service unreachable at {self._base}: {exc}") from exc

        if resp.status_code >= 400:
            detail = resp.text
            try:
                body = resp.json()
                detail = body.get("detail", detail)
            except Exception:
                pass
            raise RobotServiceError(f"Robot service error ({resp.status_code}): {detail}", resp.status_code)

        if resp.status_code == 204:
            return None
        return resp.json()

    def health(self) -> dict:
        return self._request("GET", "/robot/health")

    def job_status(self) -> dict:
        return self._request("GET", "/robot/job/status")

    def list_actions(self) -> List[dict]:
        return self._request("GET", "/robot/actions")

    def start_action(self, action_id: str) -> dict:
        return self._request("POST", f"/robot/actions/{action_id}/start")

    def action_status(self, action_id: str) -> dict:
        return self._request("GET", f"/robot/actions/{action_id}/status")

    def list_sensors(self) -> List[dict]:
        return self._request("GET", "/robot/sensors")

    def start_sensor_sample(self, sensor_id: str) -> dict:
        return self._request("POST", f"/robot/sensors/{sensor_id}/sample")

    def sensor_latest_raw(self, sensor_id: str) -> Optional[dict]:
        """Return robot envelope {status, data?} or None if unreachable."""
        return self._request(
            "GET",
            f"/robot/sensors/{sensor_id}/latest",
            allow_connection_error=True,
        )


def get_robot_client(settings: Settings) -> RobotClient:
    return RobotClient(settings)
