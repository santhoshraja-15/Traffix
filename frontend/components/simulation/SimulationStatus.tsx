"use client";

import { Activity, Car, Gauge, AlertTriangle, Network } from "lucide-react";

interface SimulationStatusProps {
  wsConnected: boolean;
  dataSource: string | undefined;
  tick: number;
  activeVehicles: number;
  avgSpeedKmh: number;
  networkHealthPct: number;
  activeIncidents: number;
  networkEdgeCount: number | null;
  networkArea: string | null;
}

interface StatItem {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  color: string;
}

/**
 * Real simulation engine status — replaces a component that displayed four
 * hardcoded per-scenario lookup tables (vehicle count/speed/density keyed
 * by scenario name, none of it measured) and a static "SUMO v1.18.0 · Anna
 * Salai OSM Network · TraCI Port 8813" string (wrong network name too —
 * this deployment's real network is Anna Nagar). Every number here comes
 * from the real WebSocket stream (see app/core/simulation_manager.py) or
 * the real network topology metadata.
 */
export default function SimulationStatus({
  wsConnected,
  dataSource,
  tick,
  activeVehicles,
  avgSpeedKmh,
  networkHealthPct,
  activeIncidents,
  networkEdgeCount,
  networkArea,
}: SimulationStatusProps) {
  const simHH = String(Math.floor(tick / 3600)).padStart(2, "0");
  const simMM = String(Math.floor((tick % 3600) / 60)).padStart(2, "0");
  const simSS = String(tick % 60).padStart(2, "0");

  const stats: StatItem[] = [
    {
      label: "Active Vehicles",
      value: activeVehicles.toLocaleString(),
      icon: <Car className="w-4 h-4" />,
      color: "text-sky-400",
    },
    {
      label: "Avg Network Speed",
      value: avgSpeedKmh.toFixed(1),
      unit: "km/h",
      icon: <Gauge className="w-4 h-4" />,
      color: avgSpeedKmh > 30 ? "text-emerald-400" : avgSpeedKmh > 15 ? "text-amber-400" : "text-red-400",
    },
    {
      label: "Network Health",
      value: `${networkHealthPct}%`,
      icon: <Activity className="w-4 h-4" />,
      color: networkHealthPct > 60 ? "text-emerald-400" : networkHealthPct > 30 ? "text-amber-400" : "text-red-400",
    },
    {
      label: "Active Incidents",
      value: activeIncidents,
      icon: <AlertTriangle className="w-4 h-4" />,
      color: activeIncidents > 0 ? "text-red-400" : "text-slate-400",
    },
  ];

  const sourceLabel = !wsConnected
    ? "Disconnected"
    : dataSource === "sumo"
    ? "TraCI Connected (Real SUMO)"
    : dataSource === "mock"
    ? "Mock Sensor Mode"
    : "Connecting…";

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-lg overflow-hidden text-white">
      {/* Header — dark, premium treatment matching the map's own HUD/
          NavigationBar aesthetic (TrafficMap.tsx), the one place a dark
          UI language is already established in this app. */}
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center border ${
              wsConnected
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : "bg-amber-500/10 text-amber-400 border-amber-500/30"
            }`}
          >
            <Network className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold">Simulation Engine</h3>
            <p className="text-xs text-slate-400">
              {sourceLabel}
            </p>
          </div>
        </div>

        {/* Simulation clock — real tick count from the WebSocket stream */}
        <div
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-extrabold tabular-nums ${
            wsConnected
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-slate-800 border-slate-700 text-slate-400"
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
          {simHH}:{simMM}:{simSS}
        </div>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* KPI grid — real, from the live WebSocket edge stream */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {stats.map((stat) => (
            <div key={stat.label} className="flex flex-col gap-2 p-3 bg-slate-800/60 rounded-xl border border-slate-700">
              <div className={stat.color}>{stat.icon}</div>
              <div>
                <div className={`text-xl font-black ${stat.color} tabular-nums`}>
                  {stat.value}
                  {stat.unit && <span className="text-xs font-bold text-slate-500 ml-0.5">{stat.unit}</span>}
                </div>
                <div className="text-xs text-slate-400 mt-0.5">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Real network info — no fabricated version/port numbers */}
        <div className="flex items-center gap-2 p-3 bg-slate-800/60 rounded-xl border border-slate-700 text-xs text-slate-400">
          <Network className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
          <span>
            {networkEdgeCount !== null && networkArea ? (
              <>
                Real {networkArea} network ·{" "}
                <span className="font-bold text-slate-200">{networkEdgeCount.toLocaleString()} road segments</span>
              </>
            ) : (
              "Loading real network metadata…"
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
