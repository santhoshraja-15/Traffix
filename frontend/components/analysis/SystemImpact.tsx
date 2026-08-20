"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";

const IMPACT_DATA = [
  { week: "W1", incidents: 18, resolved: 14, avgETA: 11.2, throughput: 1240 },
  { week: "W2", incidents: 21, resolved: 17, avgETA: 10.5, throughput: 1290 },
  { week: "W3", incidents: 16, resolved: 15, avgETA: 8.8, throughput: 1380 },
  { week: "W4", incidents: 14, resolved: 13, avgETA: 7.1, throughput: 1510 },
  // TRAFFIX goes live
  { week: "W5", incidents: 11, resolved: 11, avgETA: 5.4, throughput: 1680 },
  { week: "W6", incidents: 9,  resolved: 9,  avgETA: 4.2, throughput: 1820 },
  { week: "W7", incidents: 7,  resolved: 7,  avgETA: 3.8, throughput: 1970 },
  { week: "W8", incidents: 6,  resolved: 6,  avgETA: 3.5, throughput: 2105 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-xs rounded-xl px-4 py-3 shadow-xl border border-slate-700">
      <p className="font-bold text-slate-300 mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400">{p.name}:</span>
          <span className="font-bold">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

const IMPACT_CARDS = [
  { label: "Incidents Prevented (W5–W8)", value: "−48%", sub: "vs W1–W4 baseline", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  { label: "Avg Resolution Rate", value: "100%", sub: "All incidents resolved in W5+", color: "text-sky-700 bg-sky-50 border-sky-200" },
  { label: "Throughput Gain", value: "+69.8%", sub: "1,240 → 2,105 veh/hr", color: "text-violet-700 bg-violet-50 border-violet-200" },
  { label: "Avg ETA Improvement", value: "−68.8%", sub: "11.2 → 3.5 min", color: "text-amber-700 bg-amber-50 border-amber-200" },
];

export default function SystemImpact() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100">
        <h3 className="text-sm font-extrabold text-slate-900">System Impact Over Time</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          8-week longitudinal analysis — before and after TRAFFIX deployment (W5 onward)
        </p>
      </div>

      <div className="p-5 flex flex-col gap-5">
        {/* Impact summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {IMPACT_CARDS.map((c) => (
            <div key={c.label} className={`p-3 rounded-xl border ${c.color}`}>
              <p className="text-[10px] font-bold uppercase tracking-wider opacity-70">{c.label}</p>
              <p className="text-xl font-black mt-0.5">{c.value}</p>
              <p className="text-[10px] opacity-60 mt-0.5">{c.sub}</p>
            </div>
          ))}
        </div>

        {/* Incident trend line chart */}
        <div>
          <p className="text-xs font-bold text-slate-700 mb-3">Incident Count & Network Throughput — 8-Week Trend</p>
          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={IMPACT_DATA} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="week" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis
                  yAxisId="left"
                  stroke="#94a3b8"
                  fontSize={10}
                  tickLine={false}
                  domain={[0, 25]}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#94a3b8"
                  fontSize={10}
                  tickLine={false}
                  domain={[1000, 2200]}
                  tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine
                  yAxisId="left"
                  x="W5"
                  stroke="#0ea5e9"
                  strokeDasharray="4 3"
                  label={{ value: "TRAFFIX Live", position: "top", fontSize: 10, fill: "#0ea5e9", fontWeight: 700 }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="incidents"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#ef4444" }}
                  name="Incidents"
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="resolved"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#22c55e" }}
                  strokeDasharray="5 3"
                  name="Resolved"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="throughput"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#8b5cf6" }}
                  name="Throughput (veh/hr)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
