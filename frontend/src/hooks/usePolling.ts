import { useEffect, useState } from "react";

/**
 * Calls `fetcher` every `intervalMs`, returning the most recent result.
 * Stops on unmount. Errors are swallowed so a single failed poll doesn't
 * blank out the UI; the previous value sticks until the next success.
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  deps: unknown[] = [],
): T | null {
  const [value, setValue] = useState<T | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const v = await fetcher();
        if (!cancelled) setValue(v);
      } catch {
        // keep last value
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

  return value;
}
