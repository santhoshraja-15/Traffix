"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, Play, AlertTriangle, Crosshair, RotateCcw } from "lucide-react";
import { SimulationScenario } from "@/types/simulation";

interface AccidentSimulatorProps {
  scenario: SimulationScenario;
  isRunning: boolean;
  currentStep: number;
}

interface InjectionEvent {
  id: string;
  step: number;
  road: string;
  severity: "low" | "medium" | "high";
  vehiclesAffected: number;
  resolved: boolean;
}

const ROAD_OPTIONS = [
  "Anna Salai — Teynampet Junction",
  "Mount Flyover — OMR Junction",
  "Guindy Ring Road — Gate 3",
  "Nungambakkam High Rd — Spencer Jn",
];

export default function AccidentSimulator({
  scenario,
  isRunning,
  currentStep,
}: AccidentSimulatorProps) {
  const [selectedRoad, setSelectedRoad] = useState(ROAD_OPTIONS[0]);
  const [severity, setSeverity] = useState<"low" | "medium" | "high">("medium");
  const [events, setEvents] = useState<InjectionEvent[]>([]);
  const [injecting, setInjecting] = useState(false);

  const handleInject = () => {
    if (!isRunning) return;
    setInjecting(true);
    setTimeout(() => {
      const newEvent: InjectionEvent = {
        id: `evt-${Date.now()}`,
        step: currentStep,
        road: selectedRoad,
        severity,
        vehiclesAffected: severity === "high" ? 12 : severity === "medium" ? 6 : 2,
        resolved: false,
      };
      setEvents((prev) => [newEvent, ...prev]);
      setInjecting(false);
    }, 1200);
  };

  const handleResolve = (id: string) => {
    setEvents((prev) =>
      prev.map((e) => (e.id === id ? { ...e, resolved: true } : e))
    );
  };

  const SEVERITY_COLORS = {
    low: "bg-emerald-100 text-emerald-700 border-emerald-200",
    medium: "bg-amber-100 text-amber-700 border-amber-200",
    high: "bg-red-100 text-red-700 border-red-200",
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-red-50 text-red-600 flex items-center justify-center border border-red-100">
          <ShieldAlert className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Accident Injection Engine</h3>
          <p className="text-xs text-slate-500">Inject bottleneck events into the live SUMO simulation</p>
        </div>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-slate-700">Road Segment</label>
            <select
              value={selectedRoad}
              onChange={(e) => setSelectedRoad(e.target.value)}
              className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800"
            >
              {ROAD_OPTIONS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-slate-700">Severity</label>
            <div className="flex gap-2">
              {(["low", "medium", "high"] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setSeverity(s)}
                  className={`flex-1 py-2 rounded-xl border text-xs font-bold capitalize transition-all ${
                    severity === s ? SEVERITY_COLORS[s] : "bg-slate-50 border-slate-200 text-slate-500 hover:border-slate-300"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleInject}
            disabled={!isRunning || injecting}
            className="py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white text-xs font-extrabold rounded-xl shadow-sm flex items-center justify-center gap-2 transition-all"
          >
            {injecting ? (
              <>
                <Crosshair className="w-3.5 h-3.5 animate-spin" />
                Injecting…
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                Inject Accident
              </>
            )}
          </button>
        </div>

        {!isRunning && (
          <p className="text-xs text-center text-amber-600 font-semibold">
            ⚠ Start simulation to enable accident injection
          </p>
        )}

        {/* Event log */}
        {events.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-bold text-slate-700">Injection Log:</p>
            {events.map((ev) => (
              <div
                key={ev.id}
                className={`flex items-center justify-between p-3 rounded-xl border text-xs ${
                  ev.resolved
                    ? "bg-slate-50 border-slate-200 opacity-60"
                    : SEVERITY_COLORS[ev.severity]
                }`}
              >
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-1.5 font-bold">
                    <AlertTriangle className="w-3 h-3" />
                    {ev.road}
                  </div>
                  <div className="opacity-70">
                    Step {ev.step.toLocaleString()} · {ev.vehiclesAffected} vehicles affected ·{" "}
                    <span className="capitalize">{ev.severity}</span>
                  </div>
                </div>
                {!ev.resolved && (
                  <button
                    onClick={() => handleResolve(ev.id)}
                    className="flex items-center gap-1 px-2 py-1 bg-white/60 hover:bg-white rounded-lg border border-current/20 font-bold transition-all"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Clear
                  </button>
                )}
                {ev.resolved && (
                  <span className="px-2 py-0.5 bg-white/60 rounded-full border border-slate-300 text-slate-500 font-bold">
                    Resolved
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
