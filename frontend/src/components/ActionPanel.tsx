/**
 * Robot action panel.
 * Fetches the whitelisted action list from GET /api/actions,
 * renders one button per action, and polls status while an action runs.
 */

import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { RobotAction } from "../types";

const POLL_MS = 1_500;

export default function ActionPanel() {
  const [actions, setActions] = useState<RobotAction[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [serviceError, setServiceError] = useState<string | null>(null);

  const fetchAll = async () => {
    try {
      const data = await api.get<RobotAction[]>("/api/actions");
      setActions(data);
      setServiceError(null);
    } catch (e: unknown) {
      setServiceError(
        e instanceof ApiError ? e.message : "Robot service unavailable",
      );
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  // Poll more frequently while any action is running.
  useEffect(() => {
    const anyRunning = actions.some((a) => a.running);
    const interval = anyRunning ? POLL_MS : 5_000;
    const id = window.setInterval(fetchAll, interval);
    return () => window.clearInterval(id);
  }, [actions]);

  const trigger = async (actionId: string) => {
    try {
      await api.post(`/api/actions/${encodeURIComponent(actionId)}`);
      await fetchAll();
      setExpanded(actionId);
    } catch (e: unknown) {
      const msg = e instanceof ApiError ? e.message : "Failed to start action";
      alert(msg);
    }
  };

  return (
    <section className="panel p-5">
      <header className="mb-4">
        <div className="eyebrow">ROBOT / AUTOMATION</div>
        <h2 className="display text-bone text-2xl mt-1">Actions</h2>
        {serviceError && (
          <p className="mono text-[10px] text-blood tracking-wider mt-2">{serviceError}</p>
        )}
      </header>

      <div className="flex flex-col gap-3">
        {actions.map((action) => (
          <ActionRow
            key={action.id}
            action={action}
            isExpanded={expanded === action.id}
            onTrigger={() => void trigger(action.id)}
            onToggleExpand={() =>
              setExpanded((prev) => (prev === action.id ? null : action.id))
            }
          />
        ))}
      </div>
    </section>
  );
}

// ── Single action row ─────────────────────────────────────────────────────────

interface RowProps {
  action: RobotAction;
  isExpanded: boolean;
  onTrigger: () => void;
  onToggleExpand: () => void;
}

function ActionRow({ action, isExpanded, onTrigger, onToggleExpand }: RowProps) {
  const { running, exit_code, error, stdout, stderr, elapsed_s, finished_at } = action;

  const hasResult = finished_at !== null;
  const succeeded = hasResult && exit_code === 0 && !error;
  const failed = hasResult && (exit_code !== 0 || !!error);

  const statusLabel = running
    ? "RUNNING"
    : succeeded
    ? "DONE"
    : failed
    ? "ERROR"
    : "READY";

  const statusColor = running
    ? "text-lake"
    : succeeded
    ? "text-sage"
    : failed
    ? "text-blood"
    : "text-ash";

  const statusDot = running ? "◉" : succeeded ? "●" : failed ? "✕" : "○";

  return (
    <div className="border border-hair rounded bg-umbra/40">
      {/* Header row */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Status indicator */}
        <span className={`mono text-[11px] tracking-[0.2em] uppercase ${statusColor} w-24 shrink-0`}>
          {statusDot} {statusLabel}
        </span>

        {/* Label + description */}
        <div className="flex-1 min-w-0">
          <span className="display text-bone text-base">{action.label}</span>
          <span className="mono text-[10px] text-ash ml-3 tracking-wide">
            {action.description}
          </span>
        </div>

        {/* Elapsed */}
        {elapsed_s !== null && (
          <span className="mono text-[10px] text-ash shrink-0">
            {elapsed_s}s
          </span>
        )}

        {/* Run button */}
        <button
          type="button"
          disabled={running}
          onClick={onTrigger}
          className={`btn text-xs px-4 py-1.5 shrink-0 ${
            running ? "btn-ghost opacity-50 cursor-not-allowed" : "btn-primary"
          }`}
        >
          {running ? "Running…" : "Run"}
        </button>

        {/* Expand toggle (only if there's output) */}
        {hasResult && (stdout || stderr || error) && (
          <button
            type="button"
            onClick={onToggleExpand}
            className="mono text-[11px] text-ash hover:text-bone px-1"
            title="Toggle output"
          >
            {isExpanded ? "▲" : "▼"}
          </button>
        )}
      </div>

      {/* Expandable output */}
      {isExpanded && (
        <div className="border-t border-hair px-4 py-3 flex flex-col gap-2">
          {error && (
            <p className="mono text-[10px] text-blood">Error: {error}</p>
          )}
          {stdout && (
            <OutputBlock label="stdout" text={stdout} />
          )}
          {stderr && (
            <OutputBlock label="stderr" text={stderr} color="text-rust" />
          )}
        </div>
      )}
    </div>
  );
}

function OutputBlock({
  label,
  text,
  color = "text-sand",
}: {
  label: string;
  text: string;
  color?: string;
}) {
  return (
    <div>
      <div className={`mono text-[9px] tracking-[0.25em] uppercase mb-1 ${color}`}>
        {label}
      </div>
      <pre
        className={`mono text-[10px] leading-relaxed whitespace-pre-wrap break-all ${color} bg-black/40 rounded p-2 max-h-40 overflow-y-auto`}
      >
        {text.trim()}
      </pre>
    </div>
  );
}
