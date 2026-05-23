import { useEffect, useState } from "react";

/**
 * Live UTC clock + mission context strip. The kind of chrome NASA JPL
 * telemetry ops screens wear. Updates every second.
 */
export default function Callsign() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const utc = now
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d+Z$/, " UTC");

  return (
    <div className="mono text-[10.5px] tracking-[0.22em] uppercase text-ash flex items-center gap-4 flex-wrap">
      <span>URC 2025</span>
      <span className="text-lake">//</span>
      <span>MDRS Utah 38.927 N 110.793 W</span>
      <span className="text-lake">//</span>
      <span className="text-bone">{utc}</span>
    </div>
  );
}
