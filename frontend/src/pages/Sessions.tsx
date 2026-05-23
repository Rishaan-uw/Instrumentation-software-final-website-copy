import { useEffect, useState } from "react";
import { api } from "../api/client";
import { SessionDetail, SessionSummary } from "../types";

export default function Sessions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SessionDetail | null>(null);

  useEffect(() => {
    api
      .get<{ sessions: SessionSummary[] }>("/api/sessions")
      .then((res) => setSessions(res.sessions))
      .catch(() => setSessions([]));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api
      .get<SessionDetail>(`/api/sessions/${selectedId}`)
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selectedId]);

  const exportSession = (id: string) => {
    const a = document.createElement("a");
    a.href = `/api/sessions/${id}/export`;
    a.click();
  };

  return (
    <div className="stagger grid grid-cols-1 lg:grid-cols-12 gap-5" style={{ ["--stagger" as string]: "70ms" }}>
      <div
        style={{ ["--i" as string]: 0 }}
        className="panel p-5 lg:col-span-4 min-h-[420px]"
      >
        <div className="flex items-end justify-between mb-4">
          <div>
            <div className="eyebrow">Log / Sessions</div>
            <h2 className="display text-bone text-2xl mt-1">Mission Log</h2>
          </div>
          <span className="mono text-[10.5px] tracking-[0.22em] uppercase text-ash">
            {sessions.length} entries
          </span>
        </div>
        <div className="tick-rule mb-3" />

        {sessions.length === 0 ? (
          <p className="mono text-xs text-ash tracking-wider">
            No sessions recorded. Engage the pipeline to start one.
          </p>
        ) : (
          <ul className="space-y-0">
            {sessions.map((s, idx) => (
              <li key={s.session_id}>
                <button
                  onClick={() => setSelectedId(s.session_id)}
                  className={`w-full text-left py-3 px-2 flex items-start gap-3 transition-colors ${
                    selectedId === s.session_id
                      ? "bg-rock/60"
                      : "hover:bg-rock/30"
                  } ${idx !== 0 ? "border-t border-dusk" : ""}`}
                >
                  <span className="mono text-[10px] tracking-[0.22em] text-ash pt-1 w-7 shrink-0">
                    {(idx + 1).toString().padStart(2, "0")}
                  </span>
                  <span className="flex-1">
                    <span className="block mono text-sm text-bone">
                      {s.session_id}
                    </span>
                    <span className="block mono text-[10.5px] tracking-wider text-sand mt-1">
                      {s.measurement_count} samples
                      {s.end_time ? " / closed" : " / open"}
                    </span>
                  </span>
                  {selectedId === s.session_id && (
                    <span className="text-rust mono text-lg leading-none">&rarr;</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div
        style={{ ["--i" as string]: 1 }}
        className="panel p-5 lg:col-span-8 min-h-[420px]"
      >
        {!detail ? (
          <div className="h-full grid place-items-center">
            <p className="display-italic text-sand text-3xl opacity-60">
              Select a session.
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="eyebrow">Session Detail</div>
                <h2 className="display text-bone text-3xl mt-1 mono">
                  {detail.session_id}
                </h2>
                <div className="mono text-[11px] tracking-wider text-sand mt-1">
                  {detail.start_time}
                  {detail.end_time && ` - ${detail.end_time}`}
                </div>
              </div>
              <button
                className="btn btn-ghost"
                onClick={() => exportSession(detail.session_id)}
              >
                Download archive
              </button>
            </div>

            <div className="tick-rule my-4" />

            <div className="overflow-auto max-h-[60vh]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left eyebrow-dim">
                    <th className="py-2 pr-4">Sample</th>
                    <th className="py-2 pr-4">Time</th>
                    <th className="py-2 pr-4 text-right">Peaks</th>
                    <th className="py-2 pr-4">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.measurements.map((m) => (
                    <tr
                      key={m.measurement_id}
                      className="border-t border-dusk hover:bg-rock/40"
                    >
                      <td className="py-2 pr-4 mono text-bone">{m.sample_id}</td>
                      <td className="py-2 pr-4 mono text-sand text-xs">
                        {m.timestamp}
                      </td>
                      <td className="py-2 pr-4 text-right mono text-bone">
                        {m.peaks_detected.toString().padStart(2, "0")}
                      </td>
                      <td className="py-2 pr-4 mono tracking-wider uppercase text-xs">
                        <ConfTag conf={m.biosignature_analysis.confidence} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ConfTag({ conf }: { conf: "none" | "low" | "medium" | "high" }) {
  const color =
    conf === "high"
      ? "text-sage"
      : conf === "medium" || conf === "low"
        ? "text-amber"
        : "text-ash";
  return <span className={`${color}`}>{conf}</span>;
}
