import { useSensorSample } from "../hooks/useSensorSample";
import { ColorReadReading } from "../types";

interface Props {
  reading: ColorReadReading | null;
  serviceError: string | null;
  onSampleComplete: () => void;
}

export default function ConfidenceBadge({
  reading,
  serviceError,
  onSampleComplete,
}: Props) {
  const { sample, busy, error } = useSensorSample("color_read", onSampleComplete);
  const pct = reading?.pct_diff ?? null;
  const detected = reading?.organics_detected ?? false;
  const displayError = error ?? serviceError;

  return (
    <section className="panel p-6 md:p-8 h-full flex flex-col overflow-hidden relative">
      <div className="eyebrow">COLOR TEST / SOIL</div>
      <h2 className="display text-bone text-lg md:text-xl tracking-tight mt-1">
        Organic Analysis
      </h2>
      <div className="tick-rule mt-3 mb-5" />

      <div className="flex items-end gap-3 mb-4">
        <span
          className={`display leading-none ${
            pct === null
              ? "text-ash text-5xl"
              : detected
              ? "text-sage text-6xl"
              : "text-bone text-6xl"
          }`}
        >
          {pct === null ? "---" : `${pct.toFixed(1)}`}
        </span>
        {pct !== null && (
          <span className="mono text-[18px] tracking-wider text-ash mb-1">%</span>
        )}
      </div>

      <div className="mono text-[10px] tracking-wider text-ash mb-5">
        Organic matter — colorReadTest pct_diff
      </div>

      <div className="flex flex-col gap-1 mb-4">
        <span
          className={`mono text-[10px] tracking-[0.25em] uppercase ${
            detected ? "text-sage" : "text-ash"
          }`}
        >
          {pct === null
            ? "\u25cb AWAITING TEST"
            : detected
            ? "\u25cf ORGANICS DETECTED"
            : "\u25cb NOT DETECTED"}
        </span>
        {reading?.interpretation && (
          <span className="mono text-[10px] tracking-wider text-sand mt-1">
            {reading.interpretation}
          </span>
        )}
      </div>

      {displayError && (
        <p className="mono text-[10px] text-blood tracking-wider mb-3">{displayError}</p>
      )}

      <button
        type="button"
        disabled={busy}
        onClick={() => void sample()}
        className={`btn text-xs px-4 py-2 self-start ${
          busy ? "btn-ghost opacity-50 cursor-not-allowed" : "btn-primary"
        }`}
      >
        {busy ? "Sampling…" : "Sample Color Read"}
      </button>
    </section>
  );
}
