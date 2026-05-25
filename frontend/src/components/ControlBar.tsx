import { SystemStatus } from "../types";

interface Props {
  status: SystemStatus | null;
}

/** Session telemetry only — Engage/Halt/Sample removed in favor of sensor sample buttons. */
export default function ControlBar({ status }: Props) {
  const statusKey = status?.status ?? "unknown";
  const isRunning = statusKey === "running";
  const isError = statusKey === "error";

  const pillClass = `status-pill ${
    isRunning ? "status-running" : isError ? "status-error" : ""
  }`;

  return (
    <section className="panel px-5 py-4 md:px-6 md:py-5">
      <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
        <div className="flex items-center gap-3 min-w-fit">
          <span className={pillClass}>
            <span className="status-dot" />
            <span>{statusKey}</span>
          </span>
        </div>

        <div className="flex items-center gap-8">
          <KV label="Session" value={status?.session_id ?? "----"} />
          <KV label="Samples" value={status?.sample_count ?? 0} accent />
          <KV label="Last" value={status?.last_sample_id ?? "none"} muted />
        </div>
      </div>

      {isError && status?.error_message && (
        <div className="mt-3 mono text-xs text-blood tracking-wider">
          FAULT / {status.error_message}
        </div>
      )}
    </section>
  );
}

function KV({
  label,
  value,
  accent,
  muted,
}: {
  label: string;
  value: string | number;
  accent?: boolean;
  muted?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="eyebrow-dim">{label}</span>
      <span
        className={`mono text-sm ${
          accent ? "text-rust" : muted ? "text-sand" : "text-bone"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
