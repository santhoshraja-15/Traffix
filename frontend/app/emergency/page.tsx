"use client";

import { useState } from "react";
import Header from "@/components/common/Header";
import { ApplicationMode } from "@/types/common";
import {
  ShieldAlert,
  Play,
  RotateCcw,
  Siren,
} from "lucide-react";
import AmbulancePanel from "@/components/emergency/AmbulancePanel";
import GreenCorridorStatus from "@/components/emergency/GreenCorridorStatus";
import EmergencyAlert from "@/components/emergency/EmergencyAlert";
import RescueStatus from "@/components/emergency/RescueStatus";

type IncidentSeverity = "low" | "medium" | "high";

const INCIDENT_ROADS = [
  { value: "road_anna_2", label: "Anna Salai Sec 2 (Teynampet Junction)" },
  { value: "road_mount_1", label: "Mount Flyover Junction (OMR North)" },
  { value: "road_ring_2", label: "Guindy Inner Ring Road (Industrial Gate)" },
];

const SEVERITIES: { value: IncidentSeverity; label: string; color: string }[] = [
  { value: "low", label: "Low", color: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  { value: "medium", label: "Medium", color: "bg-amber-100 text-amber-700 border-amber-200" },
  { value: "high", label: "High / Multi-vehicle", color: "bg-red-100 text-red-700 border-red-200" },
];

export default function EmergencyPage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const [selectedRoad, setSelectedRoad] = useState("road_anna_2");
  const [severity, setSeverity] = useState<IncidentSeverity>("high");
  const [incidentActive, setIncidentActive] = useState(false);
  const [dispatchedUnitId, setDispatchedUnitId] = useState<string | null>(null);
  const [dispatchTime, setDispatchTime] = useState<number | null>(null);

  const handleSimulateIncident = () => {
    setIncidentActive(true);
    setDispatchedUnitId(null);
    setDispatchTime(null);
  };

  const handleReset = () => {
    setIncidentActive(false);
    setDispatchedUnitId(null);
    setDispatchTime(null);
  };

  const handleDispatch = (unitId: string) => {
    setDispatchedUnitId(unitId);
    setDispatchTime(Date.now());
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header mode={mode} onModeChange={setMode} />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        {/* Page title */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Siren className="w-6 h-6 text-red-600" />
              Emergency Response Command
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Simulate traffic incidents, dispatch ambulances, activate green corridors, and track rescue lifecycle.
            </p>
          </div>

          {incidentActive && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl border border-slate-200 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Scenario
            </button>
          )}
        </div>

        {/* Incident Injection Controls */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-red-50 text-red-600 flex items-center justify-center border border-red-100">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">Incident Injection</h3>
              <p className="text-xs text-slate-500">Configure and trigger a traffic accident scenario</p>
            </div>
            {incidentActive && (
              <span className="ml-auto text-xs font-bold px-2.5 py-1 bg-red-600 text-white rounded-full animate-pulse">
                INCIDENT ACTIVE
              </span>
            )}
          </div>

          <div className="p-5 grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
            {/* Road selector */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-700">Target Road Segment</label>
              <select
                value={selectedRoad}
                onChange={(e) => setSelectedRoad(e.target.value)}
                disabled={incidentActive}
                className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 disabled:opacity-50"
              >
                {INCIDENT_ROADS.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Severity selector */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-700">Incident Severity</label>
              <div className="flex gap-2">
                {SEVERITIES.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => !incidentActive && setSeverity(s.value)}
                    disabled={incidentActive}
                    className={`flex-1 py-2 text-xs font-bold rounded-xl border transition-all disabled:opacity-50 ${
                      severity === s.value
                        ? s.color
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Trigger */}
            <button
              onClick={handleSimulateIncident}
              disabled={incidentActive}
              className="py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-sm font-extrabold rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all"
            >
              <Play className="w-4 h-4" />
              {incidentActive ? "Incident Running" : "Simulate Incident"}
            </button>
          </div>
        </div>

        {/* Alert Stream (renders only after incident) */}
        <EmergencyAlert
          incidentActive={incidentActive}
          dispatchActive={dispatchedUnitId !== null}
        />

        {/* Main 2-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Ambulance Dispatch */}
          <AmbulancePanel
            incidentActive={incidentActive}
            onDispatch={handleDispatch}
            dispatchedUnitId={dispatchedUnitId}
          />

          {/* Right: Rescue Status Lifecycle */}
          <RescueStatus
            dispatched={dispatchedUnitId !== null}
            etaSeconds={dispatchTime ? Math.max(0, 180 - Math.floor((Date.now() - dispatchTime) / 1000)) : null}
          />
        </div>

        {/* Green Corridor (renders only after dispatch) */}
        <GreenCorridorStatus active={dispatchedUnitId !== null} />
      </main>
    </div>
  );
}
