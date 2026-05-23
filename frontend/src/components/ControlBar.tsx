import { useState } from "react";
import { api } from "../api/client";
import { SystemStatus } from "../types";

export type ControlAction = "start" | "stop" | "sample";

interface Props {
  status: SystemStatus | null;
  onChanged: (action: ControlAction) => void;
}

export default function ControlBar({ status, onChanged }: Props) {
  const [busy, setBusy] = useState(false);

  const run = async (path: string, action: ControlAction) => {
    setBusy(true);
    try {
      await api.post(path);
      onChanged(action);
    } finally {
      setBusy(false);
    }
  };

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
          <KV
            label="Last"
            value={status?.last_sample_id ?? "none"}
            muted
          />
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <button
            className="btn btn-primary"
            disabled={busy || isRunning}
            onClick={() => run("/api/start", "start")}
          >
            <Glyph>&#9654;</Glyph>
            Engage
          </button>
          <button
            className="btn btn-ghost"
            disabled={busy}
            onClick={() => run("/api/sample", "sample")}
          >
            <Glyph>&#9673;</Glyph>
            Sample
          </button>
          <button
            className="btn btn-danger"
            disabled={busy || !isRunning}
            onClick={() => run("/api/stop", "stop")}
          >
            <Glyph>&#9632;</Glyph>
            Halt
          </button>
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

function Glyph({ children }: { children: React.ReactNode }) {
  return <span className="text-[10px] opacity-80">{children}</span>;
}
