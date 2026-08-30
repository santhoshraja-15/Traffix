"use client";

interface HospitalLayerProps {
  name: string;
}

/** One real hospital marker — see services/ambulanceApi.ts /
 * app/integrations/osm_poi_loader.py for the real source data. */
export default function HospitalLayer({ name }: HospitalLayerProps) {
  return (
    <div className="flex items-center gap-1 bg-rose-950/90 text-rose-200 border border-rose-700/60 px-2 py-0.5 rounded text-[10px] font-bold shadow-md whitespace-nowrap">
      <span>🏥</span>
      <span>{name}</span>
    </div>
  );
}
