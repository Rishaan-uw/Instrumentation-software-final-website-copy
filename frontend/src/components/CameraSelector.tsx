/**
 * Two-button camera switcher that calls POST /api/cameras/{id}/activate.
 * Renders only when the camera switching service is reachable
 * (i.e. HUSKY_CAM_SVC_URL is set in camera.env).
 */

import { useEffect, useState } from "react";
import { api } from "../api/client";

interface SwitcherStatus {
  configured: boolean;
  active_camera?: string | null;
  running?: boolean;
  error?: string;
}

const CAMERA_OPTIONS = [
  { id: "video0", label: "Video 0" },
  { id: "video2", label: "Video 2" },
  { id: "video4", label: "Video 4" },
] as const;

interface Props {
  onActiveCameraChanged?: (cameraId: string | null) => void;
}

export default function CameraSelector({ onActiveCameraChanged }: Props) {
  const [status, setStatus] = useState<SwitcherStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null); // id of camera being activated
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const s = await api.get<SwitcherStatus>("/api/cameras/switcher/status");
      setStatus(s);
      onActiveCameraChanged?.(s.running ? s.active_camera ?? null : null);
    } catch {
      /* keep last known status */
    }
  };

  useEffect(() => {
    fetchStatus();
    const id = window.setInterval(fetchStatus, 5_000);
    return () => window.clearInterval(id);
  }, [onActiveCameraChanged]);

  if (!status?.configured) return null;

  const activate = async (cameraId: string) => {
    setBusy(cameraId);
    setError(null);
    try {
      await api.post(`/api/cameras/${encodeURIComponent(cameraId)}/activate`);
      await fetchStatus();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Switch failed";
      setError(msg);
    } finally {
      setBusy(null);
    }
  };

  const activeId = status.running ? status.active_camera : null;

  return (
    <div className="flex flex-col gap-2">
      <div className="eyebrow">Camera</div>
      <div className="flex gap-2 flex-wrap">
        {CAMERA_OPTIONS.map((cam) => {
          const isActive = activeId === cam.id;
          const isBusy = busy === cam.id;
          return (
            <button
              key={cam.id}
              type="button"
              disabled={isBusy || isActive}
              onClick={() => void activate(cam.id)}
              className={[
                "btn text-xs px-3 py-1.5 transition-colors",
                isActive
                  ? "btn-primary opacity-100 cursor-default"
                  : "btn-ghost",
              ].join(" ")}
            >
              {isBusy ? "Switching…" : cam.label}
            </button>
          );
        })}
      </div>
      {error && (
        <p className="mono text-[10px] text-blood" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
