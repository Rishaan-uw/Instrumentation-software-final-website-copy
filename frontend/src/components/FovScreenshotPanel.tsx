import { useEffect, useRef, useState } from "react";
import { ApiError, fetchCameraSnapshot } from "../api/client";
import { CameraInfo } from "../types";

interface Props {
  cameras: CameraInfo[];
}

export default function FovScreenshotPanel({ cameras }: Props) {
  const [selectedId, setSelectedId] = useState("");
  const [preview, setPreview] = useState<{ url: string; filenameBase: string } | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const replacePreview = (url: string | null, filenameBase: string) => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    if (url) previewUrlRef.current = url;
    setPreview(url ? { url, filenameBase } : null);
  };

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (cameras.length === 0) {
      setSelectedId("");
      return;
    }
    setSelectedId((prev) =>
      prev && cameras.some((c) => c.id === prev) ? prev : cameras[0].id,
    );
  }, [cameras]);

  const selected = cameras.find((c) => c.id === selectedId);

  const capture = async () => {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const blob = await fetchCameraSnapshot(selectedId);
      const url = URL.createObjectURL(blob);
      const base = (selected?.label ?? selectedId)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "") || "camera";
      replacePreview(url, base);
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Capture failed";
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  const download = () => {
    if (!preview) return;
    const a = document.createElement("a");
    a.href = preview.url;
    a.download = `fov-${preview.filenameBase}-${Date.now()}.jpg`;
    a.rel = "noopener";
    a.click();
  };

  const hasCameras = cameras.length > 0;

  return (
    <section className="panel p-4 md:p-5 h-full flex flex-col">
      <div className="eyebrow">Capture / Export</div>
      <h2 className="display text-bone text-xl mt-1 mb-4">Screenshots</h2>

      <p className="mono text-[11px] text-ash tracking-wider leading-relaxed mb-4">
        Grab the current frame from a live channel and save it as a JPEG.
      </p>

      {hasCameras ? (
        <label className="block mb-3">
          <span className="mono text-[10px] tracking-[0.2em] uppercase text-sand block mb-1.5">
            Channel
          </span>
          <select
            className="w-full bg-rock border border-hair rounded px-3 py-2 text-bone text-sm font-sans outline-none focus:border-rust/60"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
                {!c.available ? " (offline)" : ""}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <p className="mono text-xs text-ash mb-4">No optical channels bound.</p>
      )}

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          className="btn btn-primary"
          disabled={!hasCameras || busy}
          onClick={() => void capture()}
        >
          {busy ? "Capturing…" : "Capture frame"}
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={!preview || busy}
          onClick={download}
        >
          Download JPEG
        </button>
      </div>

      {error ? (
        <p className="mono text-xs text-blood mb-3" role="alert">
          {error}
        </p>
      ) : null}

      <div className="flex-1 min-h-[140px] rounded border border-hair bg-umbra overflow-hidden flex items-center justify-center">
        {preview ? (
          <img
            src={preview.url}
            alt="Last capture"
            className="max-w-full max-h-[220px] object-contain"
          />
        ) : (
          <span className="mono text-[10px] tracking-widest uppercase text-ash px-4 text-center">
            Preview appears after capture
          </span>
        )}
      </div>
    </section>
  );
}
