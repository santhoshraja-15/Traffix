"use client";

import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  Tooltip,
  Legend,
} from "recharts";

const RADAR_DATA = [
  { dimension: "Travel Time", TRAFFIX: 92, Standard: 55 },
  { dimension: "Risk Avoidance", TRAFFIX: 88, Standard: 40 },
  { dimension: "Emergency ETA", TRAFFIX: 95, Standard: 35 },
  { dimension: "Throughput", TRAFFIX: 84, Standard: 60 },
  { dimension: "Fuel Savings", TRAFFIX: 78, Standard: 48 },
  { dimension: "Signal Sync", TRAFFIX: 90, Standard: 42 },
];

const SCORE_CARDS = [
  { label: "TRAFFIX Composite Score", value: "88 / 100", delta: "+31 pts vs baseline", color: "text-sky-700 bg-sky-50 border-sky-200" },
  { label: "Standard Routing Score", value: "47 / 100", delta: "Baseline (Dijkstra)", color: "text-slate-600 bg-slate-50 border-slate-200" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-xs rounded-xl px-4 py-3 shadow-xl border border-slate-700">
      <p className="font-bold text-slate-300 mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400">{p.dataKey}:</span>
          <span className="font-bold">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function InterventionScore() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100">
        <h3 className="text-sm font-extrabold text-slate-900">Intervention Performance Radar</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          TRAFFIX XGBoost routing vs standard Dijkstra shortest path — 6-axis composite score
        </p>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Score pills */}
        <div className="flex gap-3 flex-wrap">
          {SCORE_CARDS.map((s) => (
            <div
              key={s.label}
              className={`flex-1 min-w-[160px] px-4 py-3 rounded-xl border ${s.color}`}
            >
              <p className="text-[10px] font-bold uppercase tracking-wider opacity-70">{s.label}</p>
              <p className="text-xl font-black mt-0.5">{s.value}</p>
              <p className="text-[10px] opacity-60 mt-0.5">{s.delta}</p>
            </div>
          ))}
        </div>

        {/* Radar chart */}
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={RADAR_DATA} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis
                dataKey="dimension"
                tick={{ fontSize: 11, fill: "#64748b", fontWeight: 600 }}
              />
              <Radar
                name="TRAFFIX"
                dataKey="TRAFFIX"
                stroke="#0ea5e9"
                fill="#0ea5e9"
                fillOpacity={0.18}
                strokeWidth={2}
              />
              <Radar
                name="Standard Routing"
                dataKey="Standard"
                stroke="#94a3b8"
                fill="#94a3b8"
                fillOpacity={0.1}
                strokeWidth={2}
                strokeDasharray="5 3"
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
