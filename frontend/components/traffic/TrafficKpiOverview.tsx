"use client";

import { Car, Gauge, Activity, ShieldAlert } from "lucide-react";

interface TrafficKpiOverviewProps {
  vehicleCount?: number;
  averageSpeedKmh?: number;
  stoppedVehicles?: number;
  networkHealthIndex?: number; // 0 to 100
  activeIncidentsCount?: number;
}

export default function TrafficKpiOverview({
  vehicleCount = 142,
  averageSpeedKmh = 36.2,
  stoppedVehicles = 12,
  networkHealthIndex = 88,
  activeIncidentsCount = 0,
}: TrafficKpiOverviewProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* KPI 1: Active Vehicles */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs card-hover flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100 shrink-0">
          <Car className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
            Active Vehicles
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-black text-slate-900 tabular-nums">
              {vehicleCount.toLocaleString()}
            </span>
            <span className="text-[10px] text-amber-600 font-bold">
              ({stoppedVehicles} stopped)
            </span>
          </div>
        </div>
      </div>

      {/* KPI 2: Average Speed */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs card-hover flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shrink-0">
          <Gauge className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
            Avg Network Speed
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-black text-emerald-700 tabular-nums">
              {averageSpeedKmh.toFixed(1)}
            </span>
            <span className="text-[10px] text-slate-500 font-bold">km/h</span>
          </div>
        </div>
      </div>

      {/* KPI 3: Network Health Index */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs card-hover flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100 shrink-0">
          <Activity className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
            Network Health
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-lg font-black text-indigo-700 tabular-nums">
              {networkHealthIndex}%
            </span>
            <span className={`text-[10px] font-extrabold ${networkHealthIndex > 75 ? "text-emerald-600" : networkHealthIndex > 50 ? "text-amber-600" : "text-red-600"}`}>
              {networkHealthIndex > 75 ? "Optimal" : networkHealthIndex > 50 ? "Moderate" : "Strained"}
            </span>
          </div>
        </div>
      </div>

      {/* KPI 4: Active Incidents */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs card-hover flex items-center gap-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center border shrink-0 ${
          (activeIncidentsCount || 0) > 0
            ? "bg-red-50 text-red-600 border-red-200 animate-pulse"
            : "bg-slate-50 text-slate-500 border-slate-200"
        }`}>
          <ShieldAlert className="w-4 h-4" />
        </div>
        <div>
          <span className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider block">
            Active Incidents
          </span>
          <div className="flex items-baseline gap-1.5">
            <span className={`text-lg font-black tabular-nums ${
              (activeIncidentsCount || 0) > 0 ? "text-red-600" : "text-slate-800"
            }`}>
              {Number.isNaN(activeIncidentsCount) ? 0 : activeIncidentsCount}
            </span>
            <span className="text-[10px] font-bold text-slate-400">
              {(activeIncidentsCount || 0) > 0 ? "Action Needed" : "All Clear"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
