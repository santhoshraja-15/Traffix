"use client";

import { Vehicle } from "../../types/traffic";

interface VehicleLayerProps {
  vehicles?: Vehicle[];
}

export default function VehicleLayer({ vehicles = [] }: VehicleLayerProps) {
  if (vehicles.length === 0) return null;

  return (
    <div className="contents">
      {vehicles.map((v) => (
        <div
          key={v.id}
          className="w-3 h-3 rounded-full bg-emerald-400 border border-slate-900 shadow-[0_0_8px_#34d399] flex items-center justify-center text-[8px] font-bold text-slate-950"
          title={`Vehicle ${v.id} - ${v.speedKmh.toFixed(1)} km/h`}
        />
      ))}
    </div>
  );
}
