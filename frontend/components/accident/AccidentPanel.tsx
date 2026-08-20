"use client";

import { useState } from "react";
import { ShieldAlert, MapPin, Play, CheckCircle2 } from "lucide-react";
import { AccidentSeverity } from "@/types/accident";
import AccidentMapSelector from "./AccidentMapSelector";

interface AccidentPanelProps {
  onSimulateAccident: (roadId: string, roadName: string, severity: AccidentSeverity) => void;
  activeAccidentRoadName?: string | null;
}

export default function AccidentPanel({
  onSimulateAccident,
  activeAccidentRoadName,
}: AccidentPanelProps) {
  const [isMapSelectorOpen, setIsMapSelectorOpen] = useState(false);
  const [selectedRoadId, setSelectedRoadId] = useState("road_anna_2");
  const [selectedRoadName, setSelectedRoadName] = useState("Anna Salai Sec 2 (Teynampet)");
  const [severity, setSeverity] = useState<AccidentSeverity>("high");

  const handleSelectRoad = (id: string, name: string) => {
    setSelectedRoadId(id);
    setSelectedRoadName(name);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col gap-3">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-600" />
          <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wide">
            ACCIDENT SIMULATION CONTROL
          </h3>
        </div>
        <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200">
          Simulation Trigger
        </span>
      </div>

      {/* Target Location Selector */}
      <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded-lg border border-slate-200">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-red-500 shrink-0" />
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Selected Road:</span>
            <span className="text-xs font-extrabold text-slate-800">{selectedRoadName}</span>
          </div>
        </div>
        <button
          onClick={() => setIsMapSelectorOpen(true)}
          className="px-3 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-bold rounded-md shadow-2xs transition-all"
        >
          Choose on Map
        </button>
      </div>

      {/* Severity Control */}
      <div className="flex items-center justify-between text-xs">
        <span className="font-bold text-slate-700">Severity:</span>
        <div className="flex gap-1">
          {(["low", "medium", "high", "critical"] as AccidentSeverity[]).map((s) => (
            <button
              key={s}
              onClick={() => setSeverity(s)}
              className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase transition-all ${
                severity === s
                  ? "bg-red-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={() => onSimulateAccident(selectedRoadId, selectedRoadName, severity)}
        className="w-full py-2.5 bg-red-600 hover:bg-red-700 active:bg-red-800 text-white text-xs font-extrabold rounded-lg shadow-sm flex items-center justify-center gap-2 transition-all"
      >
        <Play className="w-3.5 h-3.5" />
        <span>SIMULATE ACCIDENT</span>
      </button>

      {/* Map Selector Modal */}
      <AccidentMapSelector
        isOpen={isMapSelectorOpen}
        onClose={() => setIsMapSelectorOpen(false)}
        onSelectRoad={handleSelectRoad}
      />
    </div>
  );
}
