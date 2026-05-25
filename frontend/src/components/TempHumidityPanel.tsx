import { useSensorSample } from "../hooks/useSensorSample";
import { TempHumidityReading } from "../types";

interface Props {
  reading: TempHumidityReading | null;
  serviceError: string | null;
  onSampleComplete: () => void;
}

export default function TempHumidityPanel({
  reading,
  serviceError,
  onSampleComplete,
}: Props) {
  const { sample, busy, error } = useSensorSample("temp_humidity", onSampleComplete);
  const displayError = error ?? serviceError;

  return (
    <section className="panel p-6 md:p-8 h-full flex flex-col">
      <div className="eyebrow">ENVIRONMENT / SOIL</div>
      <h2 className="display text-bone text-lg md:text-xl tracking-tight mt-1">
        Temperature &amp; Humidity
      </h2>
      <div className="tick-rule mt-3 mb-5" />

      <div className="grid grid-cols-2 gap-6 mb-5">
        <Metric label="Temperature" value={reading?.temperature} unit="°C" />
        <Metric label="Humidity" value={reading?.humidity} unit="%" />
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
        {busy ? "Sampling…" : "Sample Temp & Humidity"}
      </button>
    </section>
  );
}

function Metric({
  label,
  value,
  unit,
}: {
  label: string;
  value: number | undefined;
  unit: string;
}) {
  return (
    <div>
      <div className="eyebrow-dim">{label}</div>
      <div className="flex items-end gap-2 mt-1">
        <span className="display text-bone text-4xl leading-none">
          {value === undefined ? "---" : value.toFixed(2)}
        </span>
        <span className="mono text-[12px] text-ash mb-1">{unit}</span>
      </div>
    </div>
  );
}
