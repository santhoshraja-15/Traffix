"use client";

export default function LegendPanel() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex flex-col gap-2">
      <h3 className="font-extrabold text-[11px] tracking-wide text-slate-900 uppercase border-b border-slate-100 pb-1">
        LEGEND
      </h3>
      
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] font-medium text-slate-700">
        {/* Traffic Densities */}
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span>Low Traffic</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>Moderate Traffic</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
          <span>Heavy Traffic</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <span>Congested / Risk</span>
        </div>

        {/* Incidents & Emergency */}
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping" />
          <span>Accident Zone</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
          <span>Ambulance Corridor</span>
        </div>
      </div>
    </div>
  );
}
