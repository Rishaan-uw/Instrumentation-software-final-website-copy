import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SpectrumPayload } from "../types";

interface Props {
  spectrum: SpectrumPayload | null;
}

// Fixed 6-channel definitions — display order Red → Blue,
// wlMin/wlMax used to look up values from the wavelength array.
const BANDS = [
  { name: "Red",    range: "620–750 nm", wlMin: 620, wlMax: 750, fill: "#EF4444" },
  { name: "Orange", range: "590–620 nm", wlMin: 590, wlMax: 620, fill: "#F97316" },
  { name: "Yellow", range: "570–590 nm", wlMin: 570, wlMax: 590, fill: "#EAB308" },
  { name: "Green",  range: "495–570 nm", wlMin: 495, wlMax: 570, fill: "#22C55E" },
  { name: "Cyan",   range: "485–500 nm", wlMin: 485, wlMax: 500, fill: "#06B6D4" },
  { name: "Blue",   range: "450–495 nm", wlMin: 450, wlMax: 495, fill: "#3B82F6" },
];

export default function SpectrumChart({ spectrum }: Props) {
  // Extract one intensity value per band from the wavelength/intensity arrays.
  // The backend generates a flat segment of points per band; any wavelength
  // inside the band's range carries the same intensity, so we just find the
  // first wavelength that falls inside each band's range.
  const data = BANDS.map((band) => {
    let raw: number | null = null;
    if (spectrum) {
      const idx = spectrum.wavelengths.findIndex(
        (wl) => wl >= band.wlMin && wl <= band.wlMax,
      );
      if (idx !== -1) {
        const v = spectrum.intensities[idx];
        raw = typeof v === "number" && isFinite(v) ? v : null;
      }
    }
    return {
      name: band.name,
      range: band.range,
      fill: band.fill,
      value: raw,
    };
  });

  return (
    <section className="panel p-5 md:p-6 flex flex-col gap-4 h-full min-h-[360px]">
      <header>
        <div className="eyebrow">SPEC / 6-CHANNEL VISIBLE</div>
        <h2 className="display text-bone text-3xl md:text-4xl mt-2">
          Spectrometer Test
        </h2>
        <p className="mono text-[11px] tracking-wider text-ash mt-1">
          {spectrum
            ? `Sample ${spectrum.sample_id}`
            : "Awaiting first acquisition"}
        </p>
      </header>

      <div className="tick-rule" />

      {!spectrum ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="mono text-[11px] tracking-widest uppercase text-ash">
            No data yet
          </span>
        </div>
      ) : (
        <div className="flex-1 min-h-0" key={spectrum.sample_id}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 12, right: 16, bottom: 8, left: 0 }}
              barCategoryGap="30%"
            >
              <CartesianGrid
                stroke="#1F1F23"
                strokeDasharray="2 6"
                vertical={false}
              />
              <XAxis
                dataKey="name"
                stroke="#8A8A92"
                tick={{ fontFamily: "JetBrains Mono", fontSize: 11, fill: "#D4D4D8" }}
                tickLine={false}
                axisLine={{ stroke: "#1F1F23" }}
              />
              <YAxis
                stroke="#8A8A92"
                tick={{ fontFamily: "JetBrains Mono", fontSize: 10, fill: "#D4D4D8" }}
                tickFormatter={(v: number) => v.toFixed(1)}
                tickLine={{ stroke: "#2A2A30" }}
                axisLine={{ stroke: "#1F1F23" }}
                width={52}
              />
              <Tooltip
                cursor={{ fill: "rgba(255,255,255,0.04)" }}
                contentStyle={{
                  background: "#000000",
                  border: "1px solid #2A2A30",
                  borderRadius: 2,
                  fontFamily: "JetBrains Mono",
                  fontSize: 11,
                }}
                labelStyle={{ color: "#D4D4D8", marginBottom: 4 }}
                itemStyle={{ color: "#FFFFFF" }}
                labelFormatter={(_: unknown, payload: unknown[]) => {
                  if (!payload?.length) return "";
                  const d = (payload[0] as { payload: typeof data[0] }).payload;
                  return `${d.name}  ·  ${d.range}`;
                }}
                formatter={(v: unknown) =>
                  v === null ? ["—", "Intensity"] : [(v as number).toFixed(5), "Intensity"]
                }
              />
              <ReferenceLine y={0} stroke="#8A8A92" strokeWidth={1} strokeDasharray="3 3" />
              <Bar dataKey="value" isAnimationActive={false} radius={[4, 4, 0, 0]}>
                {data.map((d, i) => (
                  <Cell
                    key={i}
                    fill={d.value === null ? "#2A2A30" : d.fill}
                    fillOpacity={d.value === null ? 0.3 : 0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
