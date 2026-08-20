"use client";

import { Hospital } from "../../types/ambulance";
import { MOCK_HOSPITALS } from "../../lib/mockData";

interface HospitalLayerProps {
  hospitals?: Hospital[];
}

export default function HospitalLayer({ hospitals = MOCK_HOSPITALS }: HospitalLayerProps) {
  return (
    <div className="contents">
      {hospitals.map((hosp) => (
        <div
          key={hosp.id}
          className="flex items-center gap-1 bg-rose-950/90 text-rose-200 border border-rose-700/60 px-2 py-0.5 rounded text-[10px] font-bold shadow-md"
        >
          <span>🏥</span>
          <span>{hosp.name}</span>
        </div>
      ))}
    </div>
  );
}
