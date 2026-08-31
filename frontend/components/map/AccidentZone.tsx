"use client";

import type { StreamAccident } from "../../hooks/useSimulationStream";

interface AccidentZoneProps {
  accident: StreamAccident;
}

const SEVERITY_LABEL: Record<string, string> = {
  low: "LOW",
  minor: "LOW",
  medium: "MEDIUM",
  moderate: "MEDIUM",
  high: "HIGH",
  critical: "CRITICAL",
};

export default function AccidentZone({ accident }: AccidentZoneProps) {
  return (
    <div className="flex flex-col items-center">
      <div className="w-6 h-6 rounded-full bg-red-600 text-white flex items-center justify-center font-bold text-xs shadow-lg animate-pulse">
        ⚠
      </div>
      <span className="text-[10px] font-bold bg-red-950 text-red-200 px-2 py-0.5 rounded border border-red-800 mt-1 whitespace-nowrap">
        {accident.road_name || accident.edge_id} · {SEVERITY_LABEL[accident.severity] ?? accident.severity.toUpperCase()}
      </span>
    </div>
  );
}
