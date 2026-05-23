import { Biosignatures } from "../types";

interface Props {
  bio: Biosignatures | null;
}

export default function ConfidenceBadge({ bio }: Props) {
  const pct = bio?.organic_pct ?? null;
  // Organics are detected when the color-test percentage is 50 % or above.
  const detected = pct !== null ? pct >= 50 : (bio?.organics ?? false);

  return (
    <section className="panel p-6 md:p-8 h-full flex flex-col overflow-hidden relative">
      <div className="eyebrow">COLOR TEST / SOIL</div>
      <h2 className="display text-bone text-lg md:text-xl tracking-tight mt-1">
        Organic Analysis
      </h2>
      <div className="tick-rule mt-3 mb-5" />

      {/* Percentage readout */}
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
        Organic matter — color test result
      </div>

      {/* Detection status */}
      <div className="flex flex-col gap-1">
        <span
          className={`mono text-[10px] tracking-[0.25em] uppercase ${
            detected ? "text-sage" : "text-ash"
          }`}
        >
          {detected ? "\u25cf ORGANICS DETECTED" : "\u25cb NOT DETECTED"}
        </span>
        {bio?.interpretation && (
          <span className="mono text-[10px] tracking-wider text-sand mt-1">
            {bio.interpretation}
          </span>
        )}
      </div>
    </section>
  );
}
