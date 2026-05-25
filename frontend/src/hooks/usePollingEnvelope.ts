import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";

interface Envelope<T> {
  status: "ok" | "no_data";
  data?: T;
}

export function usePollingEnvelope<T>(
  path: string,
  intervalMs: number,
  deps: unknown[] = [],
): { data: T | null; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const env = await api.get<Envelope<T>>(path);
        if (cancelled) return;
        if (env.status === "ok" && env.data !== undefined) {
          setData(env.data);
          setError(null);
        } else {
          setData(null);
          setError(null);
        }
      } catch (e: unknown) {
        if (cancelled) return;
        setError(e instanceof ApiError ? e.message : "Robot service unavailable");
      }
    };
    tick();
    const id = window.setInterval(tick, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error };
}
