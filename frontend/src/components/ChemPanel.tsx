import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";
import { ChemReading } from "../types";

interface Props {
  latest: ChemReading | null;
  history: ChemReading[];
}

const FIELDS: Array<{
  key: keyof Omit<ChemReading, "timestamp">;
  label: string;
  unit: string;
  digits: number;
  code: string;
}> = [
  { key: "ph", label: "Acidity", unit: "pH", digits: 2, code: "A1" },
  { key: "conductivity_us_cm", label: "Conductivity", unit: "µS/cm", digits: 0, code: "C1" },
  { key: "temperature_c", label: "Temperature", unit: "°C", digits: 1, code: "T1" },
  { key: "moisture_pct", label: "Moisture", unit: "% vol", digits: 1, code: "M1" },
  { key: "organic_index", label: "Organic Index", unit: "rel", digits: 2, code: "O1" },
];

export default function ChemPanel({ latest, history }: Props) {
  return (
    <section className="panel p-5">
      <header className="mb-4">
        <div className="eyebrow">CHEM / IN SITU</div>
        <h2 className="display text-bone text-2xl mt-1">Soil Chemistry</h2>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-0 border-t border-dusk">
        {FIELDS.map(({ key, label, unit, digits, code }, idx) => {
          const value = latest?.[key];
          const series = history.map((h) => ({ t: h.timestamp, v: h[key] }));
          return (
            <div
              key={key}
              className={`px-4 py-4 border-b border-dusk ${
                idx !== FIELDS.length - 1 ? "xl:border-r" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="eyebrow-dim">{code}</span>
                <span className="mono text-[19px] tracking-[0.12em] text-ash">
                  {unit}
                </span>
              </div>
              <div
                className="display text-bone text-3xl mt-2 flicker-on-change"
                key={value ?? "empty"}
              >
                {value === undefined ? "---" : value.toFixed(digits)}
              </div>
              <div className="mono text-[10.5px] tracking-wider text-sand mt-0.5">
                {label}
              </div>
              <div className="h-8 -mx-1 mt-2 opacity-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={series}>
                    <YAxis hide domain={["auto", "auto"]} />
                    <Line
                      type="monotone"
                      dataKey="v"
                      stroke="#7C5CFF"
                      dot={false}
                      strokeWidth={1.25}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
