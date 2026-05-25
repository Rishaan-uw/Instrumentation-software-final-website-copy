import { useState } from "react";
import { api } from "../api/client";
import ActionPanel from "../components/ActionPanel";
import CameraFeed from "../components/CameraFeed";
import CameraSelector from "../components/CameraSelector";
import FovScreenshotPanel from "../components/FovScreenshotPanel";
import ConfidenceBadge from "../components/ConfidenceBadge";
import ControlBar from "../components/ControlBar";
import SpectrumChart from "../components/SpectrumChart";
import TempHumidityPanel from "../components/TempHumidityPanel";
import { usePolling } from "../hooks/usePolling";
import { usePollingEnvelope } from "../hooks/usePollingEnvelope";
import { CameraInfo, ColorReadReading, SpectrumPayload, SystemStatus, TempHumidityReading } from "../types";

export default function Dashboard() {
  const [chemBump, setChemBump] = useState(0);
  const [spectrumBump, setSpectrumBump] = useState(0);
  const [tempBump, setTempBump] = useState(0);

  const cameras =
    usePolling(() => api.get<{ cameras: CameraInfo[] }>("/api/cameras"), 10_000) ?? {
      cameras: [],
    };

  const status = usePolling<SystemStatus>(() => api.get<SystemStatus>("/api/status"), 2_000);

  const { data: colorRead, error: chemServiceError } = usePollingEnvelope<ColorReadReading>(
    "/api/chem/latest",
    1_000,
    [chemBump],
  );

  const { data: spectrum, error: spectrumServiceError } = usePollingEnvelope<SpectrumPayload>(
    "/api/spectrum/latest",
    1_000,
    [spectrumBump],
  );

  const { data: tempReading, error: tempServiceError } = usePollingEnvelope<TempHumidityReading>(
    "/api/sensors/temp_humidity/latest",
    1_000,
    [tempBump],
  );

  const refreshChem = () => {
    setChemBump((n) => n + 1);
    window.setTimeout(() => setChemBump((n) => n + 1), 500);
  };

  const refreshSpectrum = () => {
    setSpectrumBump((n) => n + 1);
    window.setTimeout(() => setSpectrumBump((n) => n + 1), 500);
  };

  const refreshTemp = () => {
    setTempBump((n) => n + 1);
    window.setTimeout(() => setTempBump((n) => n + 1), 500);
  };

  return (
    <div className="stagger flex flex-col gap-5" style={{ ["--stagger" as string]: "70ms" }}>
      <div style={{ ["--i" as string]: 0 }}>
        <ControlBar status={status} />
      </div>

      <div style={{ ["--i" as string]: 1 }}>
        <ActionPanel />
      </div>

      <div
        className="grid grid-cols-1 lg:grid-cols-12 gap-5"
        style={{ ["--i" as string]: 2 }}
      >
        <div className="lg:col-span-4 flex flex-col gap-5">
          <ConfidenceBadge
            reading={colorRead}
            serviceError={chemServiceError}
            onSampleComplete={refreshChem}
          />
          <TempHumidityPanel
            reading={tempReading}
            serviceError={tempServiceError}
            onSampleComplete={refreshTemp}
          />
        </div>
        <div className="lg:col-span-8">
          <SpectrumChart
            spectrum={spectrum}
            serviceError={spectrumServiceError}
            onSampleComplete={refreshSpectrum}
          />
        </div>
      </div>

      <div style={{ ["--i" as string]: 3 }}>
        <div className="flex flex-col lg:flex-row gap-6 lg:items-start">
          <div className="min-w-0 w-full lg:grow-[2] lg:basis-0">
            <div className="flex items-end justify-between mb-3 gap-4 flex-wrap">
              <SectionHeader eyebrow="Optical / Live" title="Field of View" noMargin />
              <CameraSelector />
            </div>
            {cameras.cameras.length === 0 ? (
              <EmptyCameras />
            ) : (
              <div className="grid grid-cols-1 gap-6">
                {cameras.cameras.map((c, i) => (
                  <CameraFeed key={c.id} camera={c} index={i} />
                ))}
              </div>
            )}
          </div>
          <aside className="w-full lg:grow lg:basis-0 lg:max-w-[min(280px,32vw)] shrink-0 lg:sticky lg:top-4 self-stretch">
            <FovScreenshotPanel cameras={cameras.cameras} />
          </aside>
        </div>
      </div>
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
  noMargin,
}: {
  eyebrow: string;
  title: string;
  noMargin?: boolean;
}) {
  return (
    <div className={noMargin ? undefined : "mb-3"}>
      <div className="eyebrow">{eyebrow}</div>
      <h2 className="display text-bone text-2xl mt-1">{title}</h2>
    </div>
  );
}

function EmptyCameras() {
  return (
    <div className="panel p-6 text-sand">
      <div className="flex items-start gap-4">
        <div className="mono text-rust text-xl leading-none pt-1">[ ]</div>
        <div>
          <p className="display text-bone text-xl">No optical channels bound.</p>
          <p className="mono text-xs text-ash mt-2 tracking-wider">
            Set <code className="text-sand">HUSKY_CAMERAS</code> in{" "}
            <code className="text-sand">.env</code>
            , for example{" "}
            <code className="text-sand">microscope:0,overview:1</code>, then restart
            uvicorn.
          </p>
        </div>
      </div>
    </div>
  );
}
