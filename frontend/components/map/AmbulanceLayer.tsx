"use client";

import { Ambulance } from "../../types/ambulance";

interface AmbulanceLayerProps {
  ambulance?: Ambulance | null;
}

export default function AmbulanceLayer({ ambulance }: AmbulanceLayerProps) {
  if (!ambulance || ambulance.status === "idle") return null;

  return (
    <div className="flex flex-col items-center">
      <div className="w-6 h-6 rounded-full bg-sky-500 text-white flex items-center justify-center font-bold text-xs shadow-[0_0_15px_#0ea5e9] animate-pulse-emergency">
        🚑
      </div>
      <span className="text-[10px] font-bold bg-sky-950 text-sky-200 px-2 py-0.5 rounded border border-sky-800 mt-1">
        {ambulance.callSign} ({ambulance.status.replace(/_/g, " ")})
      </span>
    </div>
  );
}
