"use client";

import { Activity, Car, Gauge, AlertTriangle, Network, Cpu } from "lucide-react";

interface SimulationStatusProps {
  isRunning: boolean;
  currentStep: number;
  speedMultiplier: number;
  scenario: string;
  traciConnected: boolean;
}

interface StatItem {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  color: string;
}

export default function SimulationStatus({
  isRunning,
  currentStep,
  speedMultiplier,
  scenario,
  traciConnected,
}: SimulationStatusProps) {
  const vehicleCounts: Record<string, number> = {
    low: 128,
    medium: 347,
    high: 612,
    congested: 891,
  };

  const avgSpeeds: Record<string, number> = {
    low: 54.2,
    medium: 38.6,
    high: 22.1,
    congested: 8.4,
  };

  const densities: Record<string, number> = {
    low: 18,
    medium: 46,
    high: 73,
    congested: 94,
  };

  const activeVehicles = vehicleCounts[scenario] ?? 347;
  const avgSpeed = avgSpeeds[scenario] ?? 38.6;
  const density = densities[scenario] ?? 46;
  const simTimeSecs = currentStep;
  const simHH = String(Math.floor(simTimeSecs / 3600)).padStart(2, "0");
  const simMM = String(Math.floor((simTimeSecs % 3600) / 60)).padStart(2, "0");
  const simSS = String(simTimeSecs % 60).padStart(2, "0");

  const stats: StatItem[] = [
    {
      label: "Active Vehicles",
      value: activeVehicles.toLocaleString(),
      icon: <Car className="w-4 h-4" />,
      color: "text-sky-600",
    },
    {
      label: "Avg Network Speed",
      value: avgSpeed,
      unit: "km/h",
      icon: <Gauge className="w-4 h-4" />,
      color: avgSpeed > 30 ? "text-emerald-600" : avgSpeed > 15 ? "text-amber-600" : "text-red-600",
    },
    {
      label: "Network Density",
      value: `${density}%`,
      icon: <Activity className="w-4 h-4" />,
      color: density < 40 ? "text-emerald-600" : density < 70 ? "text-amber-600" : "text-red-600",
    },
    {
      label: "Active Incidents",
      value: scenario === "congested" ? 3 : scenario === "high" ? 1 : 0,
      icon: <AlertTriangle className="w-4 h-4" />,
      color: scenario === "congested" ? "text-red-600" : "text-slate-500",
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center border ${
              traciConnected
                ? "bg-emerald-50 text-emerald-600 border-emerald-100"
                : "bg-amber-50 text-amber-600 border-amber-100"
            }`}
          >
            <Network className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">SUMO Network Statistics</h3>
            <p className="text-xs text-slate-500">
              TraCI:{" "}
              <span
                className={`font-bold ${
                  traciConnected ? "text-emerald-600" : "text-amber-600"
                }`}
              >
                {traciConnected ? "Connected (Mock)" : "Disconnected"}
              </span>
            </p>
          </div>
        </div>

        {/* Simulation clock */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-extrabold tabular-nums ${
              isRunning
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-slate-50 border-slate-200 text-slate-600"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isRunning ? "bg-emerald-500 animate-pulse" : "bg-slate-300"
              }`}
            />
            {simHH}:{simMM}:{simSS}
          </div>
        </div>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* KPI grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="flex flex-col gap-2 p-3 bg-slate-50 rounded-xl border border-slate-200"
            >
              <div className={`${stat.color}`}>{stat.icon}</div>
              <div>
                <div className={`text-xl font-black ${stat.color} tabular-nums`}>
                  {stat.value}
                  {stat.unit && (
                    <span className="text-xs font-bold text-slate-400 ml-0.5">{stat.unit}</span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Network density bar */}
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-bold text-slate-700">Network Load</span>
            <span className="text-slate-500">{density}% occupancy</span>
          </div>
          <div className="h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                density < 40
                  ? "bg-gradient-to-r from-emerald-400 to-emerald-500"
                  : density < 70
                  ? "bg-gradient-to-r from-amber-400 to-amber-500"
                  : "bg-gradient-to-r from-red-400 to-red-600"
              }`}
              style={{ width: `${density}%` }}
            />
          </div>
        </div>

        {/* SUMO engine info */}
        <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600">
          <Cpu className="w-3.5 h-3.5 text-sky-500 flex-shrink-0" />
          <span>
            SUMO v1.18.0 · Anna Salai OSM Network · TraCI Port 8813 ·{" "}
            <span className="font-bold text-slate-800">{speedMultiplier}× realtime</span>
          </span>
        </div>
      </div>
    </div>
  );
}
