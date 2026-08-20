"use client";

import { Map, Layers, CheckCircle2 } from "lucide-react";
import { SimulationScenario } from "@/types/simulation";

interface ScenarioOption {
  value: SimulationScenario;
  label: string;
  subtitle: string;
  density: number;
  vehicles: number;
  color: string;
  activeColor: string;
}

const SCENARIOS: ScenarioOption[] = [
  {
    value: "low",
    label: "Low Traffic",
    subtitle: "Off-peak hours — early morning",
    density: 18,
    vehicles: 128,
    color: "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300",
    activeColor: "border-emerald-400 bg-emerald-50 text-emerald-800",
  },
  {
    value: "medium",
    label: "Medium Traffic",
    subtitle: "Midday steady flow",
    density: 46,
    vehicles: 347,
    color: "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300",
    activeColor: "border-sky-400 bg-sky-50 text-sky-800",
  },
  {
    value: "high",
    label: "High Traffic",
    subtitle: "Evening peak rush",
    density: 73,
    vehicles: 612,
    color: "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300",
    activeColor: "border-amber-400 bg-amber-50 text-amber-800",
  },
  {
    value: "congested",
    label: "Gridlock",
    subtitle: "Severe congestion scenario",
    density: 94,
    vehicles: 891,
    color: "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300",
    activeColor: "border-red-400 bg-red-50 text-red-800",
  },
];

const OSM_NETWORKS = [
  { id: "anna_salai", label: "Anna Salai Corridor", coords: "13.0482°N 80.2425°E", active: true },
  { id: "gstn_road", label: "GST Road (NH-45)", coords: "12.9700°N 80.1900°E", active: false },
  { id: "omr_north", label: "OMR North (IT Corridor)", coords: "12.9890°N 80.2470°E", active: false },
];

interface ScenarioSelectorProps {
  scenario: SimulationScenario;
  onSelect: (s: SimulationScenario) => void;
}

export default function ScenarioSelector({ scenario, onSelect }: ScenarioSelectorProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100">
          <Layers className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Traffic Scenario Loader</h3>
          <p className="text-xs text-slate-500">Select density scenario to inject into SUMO network</p>
        </div>
      </div>

      <div className="p-5 flex flex-col gap-5">
        {/* Scenario cards */}
        <div className="grid grid-cols-2 gap-3">
          {SCENARIOS.map((sc) => {
            const isActive = scenario === sc.value;
            return (
              <button
                key={sc.value}
                onClick={() => onSelect(sc.value)}
                className={`relative p-4 rounded-xl border text-left transition-all ${
                  isActive ? sc.activeColor : sc.color
                }`}
              >
                {isActive && (
                  <CheckCircle2 className="absolute top-3 right-3 w-4 h-4 text-current opacity-80" />
                )}
                <div className="text-sm font-extrabold mb-0.5">{sc.label}</div>
                <div className="text-[10px] opacity-70 mb-2">{sc.subtitle}</div>
                <div className="flex items-center gap-3 text-xs font-bold">
                  <span>{sc.vehicles} veh</span>
                  <span className="opacity-50">·</span>
                  <span>{sc.density}% density</span>
                </div>
                {/* Mini density bar */}
                <div className="mt-2 h-1.5 bg-black/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-current rounded-full opacity-60 transition-all"
                    style={{ width: `${sc.density}%` }}
                  />
                </div>
              </button>
            );
          })}
        </div>

        {/* OSM Network selector */}
        <div className="flex flex-col gap-2">
          <p className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <Map className="w-3.5 h-3.5 text-slate-500" />
            OSM Network
          </p>
          {OSM_NETWORKS.map((net) => (
            <div
              key={net.id}
              className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-all ${
                net.active
                  ? "border-sky-300 bg-sky-50 text-sky-800"
                  : "border-slate-200 bg-slate-50 text-slate-500 opacity-60"
              }`}
            >
              <div className="flex items-center gap-2">
                {net.active && <CheckCircle2 className="w-3.5 h-3.5 text-sky-600" />}
                <div>
                  <div className="font-bold">{net.label}</div>
                  <div className="text-[10px] opacity-70">{net.coords}</div>
                </div>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                  net.active
                    ? "bg-sky-100 text-sky-700 border-sky-200"
                    : "bg-slate-100 text-slate-500 border-slate-200"
                }`}
              >
                {net.active ? "LOADED" : "AVAILABLE"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
