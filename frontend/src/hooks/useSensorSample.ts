import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import { RobotJobStatus } from "../types";

const POLL_MS = 1_500;

export function useSensorSample(sensorId: string, onComplete?: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<RobotJobStatus | null>(null);
  const pollRef = useRef<number | null>(null);

  const stopPoll = () => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const pollJob = useCallback(async () => {
    try {
      const status = await api.get<RobotJobStatus>("/api/sensors/job/status");
      setJob(status);
      if (!status.running && status.kind === "sensor" && status.id === sensorId) {
        stopPoll();
        setBusy(false);
        if (status.error) {
          setError(status.error);
        } else {
          setError(null);
          onComplete?.();
        }
      }
    } catch (e: unknown) {
      stopPoll();
      setBusy(false);
      setError(e instanceof ApiError ? e.message : "Failed to read job status");
    }
  }, [sensorId, onComplete]);

  useEffect(() => () => stopPoll(), []);

  const sample = async () => {
    setError(null);
    setBusy(true);
    try {
      await api.post(`/api/sensors/${encodeURIComponent(sensorId)}/sample`);
      await pollJob();
      pollRef.current = window.setInterval(() => void pollJob(), POLL_MS);
    } catch (e: unknown) {
      setBusy(false);
      setError(e instanceof ApiError ? e.message : "Failed to start sample");
    }
  };

  return { sample, busy, error, job };
}
