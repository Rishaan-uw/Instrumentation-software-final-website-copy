import { useState } from "react";
import { snapshotUrl, streamUrl } from "../api/client";
import { CameraInfo } from "../types";
import Reticle from "./deco/Reticle";

interface Props {
  camera: CameraInfo;
  index: number;
}

export default function CameraFeed({ camera, index }: Props) {
  const [errored, setErrored] = useState(false);
  const url = errored ? snapshotUrl(camera.id) : streamUrl(camera.id);
  const optical = String(index + 1).padStart(2, "0");

  return (
    <div className="panel p-4">
      {/* Upper rail */}
      <div className="flex items-center justify-between pb-2">
        <div className="flex items-baseline gap-3">
          <span className="eyebrow">OPT/{optical}</span>
          <span className="display text-bone text-base tracking-tight">
            {camera.label}
          </span>
        </div>
        <span
          className={`mono text-[10px] tracking-[0.25em] uppercase ${
            camera.available ? "text-rust" : "text-ash"
          }`}
        >
          {camera.available ? "\u25cf LIVE" : "\u25cb OFFLINE"}
        </span>
      </div>

      <div className="reticle-shell relative w-full min-h-[220px] h-[min(62vh,820px)] max-h-[85vh] bg-black overflow-hidden rounded-sm">
        <img
          key={url}
          src={url}
          alt={camera.label}
          className="w-full h-full object-cover"
          onError={() => setErrored(true)}
        />
        <div className="scanline" />
        <Reticle />

        {/* Device readout in the corner, like a viewfinder overlay. */}
        <div className="absolute bottom-2 right-2 mono text-[10px] tracking-[0.2em] uppercase text-bone/70 bg-umbra/60 px-1.5 py-0.5">
          {camera.device}
        </div>
      </div>
    </div>
  );
}
