"use client";

import { TrendingDown, TrendingUp, Minus } from "lucide-react";

interface MetricRow {
  metric: string;
  before: string;
  after: string;
  change: string;
  direction: "up" | "down" | "neutral";
  better: "down" | "up";
  category: string;
}

const METRICS: MetricRow[] = [
  {
    metric: "Average Travel Time",
    before: "24.0 min",
    after: "14.0 min",
    change: "−41.6%",
    direction: "down",
    better: "down",
    category: "Routing",
  },
  {
    metric: "Average Network Speed",
    before: "22.0 km/h",
    after: "38.5 km/h",
    change: "+75.0%",
    direction: "up",
    better: "up",
    category: "Routing",
  },
  {
    metric: "High-Risk Segment Exposure",
    before: "65.0%",
    after: "12.0%",
    change: "−81.5%",
    direction: "down",
    better: "down",
    category: "Safety",
  },
  {
    metric: "Ambulance ETA",
    before: "12.0 min",
    after: "3.5 min",
    change: "−70.8%",
    direction: "down",
    better: "down",
    category: "Emergency",
  },
  {
    metric: "Network Throughput",
    before: "1,240 veh/hr",
    after: "2,105 veh/hr",
    change: "+69.8%",
    direction: "up",
    better: "up",
    category: "Efficiency",
  },
  {
    metric: "Fuel Consumption Index",
    before: "100 (baseline)",
    after: "72",
    change: "−28.0%",
    direction: "down",
    better: "down",
    category: "Sustainability",
  },
  {
    metric: "Signal Cycle Waste",
    before: "38%",
    after: "9%",
    change: "−76.3%",
    direction: "down",
    better: "down",
    category: "Signals",
  },
  {
    metric: "Incident Detection Latency",
    before: "4.2 min",
    after: "0.8 min",
    change: "−81.0%",
    direction: "down",
    better: "down",
    category: "IoT",
  },
];

const CATEGORY_COLORS: Record<string, string> = {
  Routing: "bg-sky-100 text-sky-700 border-sky-200",
  Safety: "bg-red-100 text-red-700 border-red-200",
  Emergency: "bg-amber-100 text-amber-700 border-amber-200",
  Efficiency: "bg-emerald-100 text-emerald-700 border-emerald-200",
  Sustainability: "bg-teal-100 text-teal-700 border-teal-200",
  Signals: "bg-violet-100 text-violet-700 border-violet-200",
  IoT: "bg-indigo-100 text-indigo-700 border-indigo-200",
};

export default function PerformanceMetrics() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Full Performance Metrics Table</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Before vs After TRAFFIX — SUMO Medium Scenario · Anna Salai Network
          </p>
        </div>
        <span className="text-xs font-bold text-slate-500">{METRICS.length} metrics</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left px-5 py-3 text-slate-500 font-bold uppercase tracking-wider">Metric</th>
              <th className="text-left px-4 py-3 text-slate-500 font-bold uppercase tracking-wider">Category</th>
              <th className="text-right px-4 py-3 text-slate-500 font-bold uppercase tracking-wider">Before</th>
              <th className="text-right px-4 py-3 text-slate-500 font-bold uppercase tracking-wider">After</th>
              <th className="text-right px-5 py-3 text-slate-500 font-bold uppercase tracking-wider">Change</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {METRICS.map((row) => {
              const improved = row.direction === row.better;
              return (
                <tr key={row.metric} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3.5 font-semibold text-slate-800">{row.metric}</td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`px-2 py-0.5 rounded-full border font-bold ${
                        CATEGORY_COLORS[row.category] ?? "bg-slate-100 text-slate-600 border-slate-200"
                      }`}
                    >
                      {row.category}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-right text-slate-400 font-medium">{row.before}</td>
                  <td className="px-4 py-3.5 text-right font-bold text-slate-900">{row.after}</td>
                  <td className="px-5 py-3.5 text-right">
                    <span
                      className={`inline-flex items-center gap-1 font-extrabold ${
                        improved ? "text-emerald-600" : "text-red-600"
                      }`}
                    >
                      {row.direction === "down" ? (
                        <TrendingDown className="w-3 h-3" />
                      ) : row.direction === "up" ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <Minus className="w-3 h-3" />
                      )}
                      {row.change}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
