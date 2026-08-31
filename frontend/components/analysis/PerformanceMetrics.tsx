"use client";

import { useEffect, useMemo, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useTraffixContext } from "@/context/TraffixContext";
import { loadRealLocations } from "@/services/navigationApi";

const CONGESTION_COLORS: Record<string, string> = {
  free_flow: "bg-emerald-100 text-emerald-700 border-emerald-200",
  light: "bg-sky-100 text-sky-700 border-sky-200",
  moderate: "bg-amber-100 text-amber-700 border-amber-200",
  heavy: "bg-orange-100 text-orange-700 border-orange-200",
  severe: "bg-red-100 text-red-700 border-red-200",
};

const MAX_ROWS = 30;

/**
 * Real live per-edge metrics table — replaces the old "Full Metrics Table",
 * which was an entirely fabricated before/after comparison (fake travel
 * times, fake fuel index, a "Signal Cycle Waste" row for signal control
 * that doesn't exist in this deployment). This shows the real network's
 * highest-risk edges right now, straight from the live WebSocket stream.
 */
export default function PerformanceMetrics() {
  const { edges } = useTraffixContext();
  const [nameByEdge, setNameByEdge] = useState<Map<string, string>>(new Map());

  useEffect(() => {
    loadRealLocations()
      .then((locs) => setNameByEdge(new Map(locs.map((l) => [l.edge_id, l.name]))))
      .catch(() => {
        /* honest fallback: table still works with raw edge_ids */
      });
  }, []);

  const rows = useMemo(
    () =>
      [...edges]
        .sort((a, b) => b.risk_score - a.risk_score)
        .slice(0, MAX_ROWS),
    [edges]
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Live Edge Metrics — Highest Risk First</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Real per-edge state from the current WebSocket stream, top {MAX_ROWS} of {edges.length} edges
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left px-5 py-3 text-slate-500 font-bold uppercase tracking-wider">Road / Edge</th>
              <th className="text-left px-4 py-3 text-slate-500 font-bold uppercase tracking-wider">Congestion</th>
              <th className="text-right px-4 py-3 text-slate-500 font-bold uppercase tracking-wider">Speed</th>
              <th className="text-right px-4 py-3 text-slate-500 font-bold uppercase tracking-wider">Vehicles</th>
              <th className="text-right px-5 py-3 text-slate-500 font-bold uppercase tracking-wider">Risk (V15/V16)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                  No live edge data yet — start a simulation to populate this table.
                </td>
              </tr>
            )}
            {rows.map((row) => {
              const riskPct = Math.round(row.risk_score * 100);
              const trend = riskPct >= 60 ? "up" : riskPct <= 20 ? "down" : "flat";
              return (
                <tr key={row.edge_id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3 font-semibold text-slate-800">
                    {nameByEdge.get(row.edge_id) ?? row.edge_id}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full border font-bold ${
                        CONGESTION_COLORS[row.congestion] ?? "bg-slate-100 text-slate-600 border-slate-200"
                      }`}
                    >
                      {row.congestion.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700 font-medium">
                    {row.speed.toFixed(1)} km/h
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700 font-medium">{row.vehicle_count}</td>
                  <td className="px-5 py-3 text-right">
                    <span
                      className={`inline-flex items-center gap-1 font-extrabold ${
                        trend === "up" ? "text-red-600" : trend === "down" ? "text-emerald-600" : "text-slate-500"
                      }`}
                    >
                      {trend === "up" ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : trend === "down" ? (
                        <TrendingDown className="w-3 h-3" />
                      ) : (
                        <Minus className="w-3 h-3" />
                      )}
                      {riskPct}%
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
