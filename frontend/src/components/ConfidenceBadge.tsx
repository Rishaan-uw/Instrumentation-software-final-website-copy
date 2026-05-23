import { ColorReadReading } from "../types";

interface Props {
  reading: ColorReadReading | null;
}

export default function ConfidenceBadge({ reading }: Props) {
  const pct = reading?.pct_diff ?? null;
  const detected = reading?.organics_detected ?? false;

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

      <div className="flex flex-col gap-1">
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
    </section>
  );
}
