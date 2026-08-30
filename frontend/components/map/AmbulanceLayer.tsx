"use client";

import type { StreamMission } from "../../hooks/useSimulationStream";

interface AmbulanceLayerProps {
  mission: StreamMission;
}

const STATE_LABEL: Record<string, string> = {
  ambulance_dispatched: "DISPATCHED",
  green_corridor_active: "CORRIDOR ACTIVE",
  en_route_to_accident: "EN ROUTE",
  ambulance_arrived: "ARRIVED",
  on_site_response: "ON SITE",
  returning_to_hospital: "RETURNING",
  emergency_completed: "COMPLETED",
};

export default function AmbulanceLayer({ mission }: AmbulanceLayerProps) {
  return (
    <div className="flex flex-col items-center">
      <div className="w-6 h-6 rounded-full bg-sky-500 text-white flex items-center justify-center font-bold text-xs shadow-[0_0_15px_#0ea5e9] animate-pulse-emergency">
        🚑
      </div>
      <span className="text-[10px] font-bold bg-sky-950 text-sky-200 px-2 py-0.5 rounded border border-sky-800 mt-1 whitespace-nowrap">
        {mission.unit_number} · {STATE_LABEL[mission.state] ?? mission.state}
      </span>
    </div>
  );
}
