"use client";

import { Accident } from "../../types/accident";

interface AccidentZoneProps {
  accident?: Accident | null;
}

export default function AccidentZone({ accident }: AccidentZoneProps) {
  if (!accident) return null;

  return (
    <div className="flex flex-col items-center">
      <div className="w-6 h-6 rounded-full bg-red-600 text-white flex items-center justify-center font-bold text-xs shadow-lg animate-pulse">
        ⚠
      </div>
      <span className="text-[10px] font-bold bg-red-950 text-red-200 px-2 py-0.5 rounded border border-red-800 mt-1">
        {accident.roadName}
      </span>
    </div>
  );
}
