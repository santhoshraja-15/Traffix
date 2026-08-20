"use client";

import { PieChart, BarChart2 } from "lucide-react";

interface CongestionBreakdownProps {
  lowCount?: number;
  moderateCount?: number;
  highCount?: number;
  congestedCount?: number;
}

export default function CongestionBreakdown({
  lowCount = 26,
  moderateCount = 8,
  highCount = 3,
  congestedCount = 1,
}: CongestionBreakdownProps) {
  const total = lowCount + moderateCount + highCount + congestedCount;
  const lowPct = Math.round((lowCount / total) * 100);
  const modPct = Math.round((moderateCount / total) * 100);
  const highPct = Math.round((highCount / total) * 100);
  const congPct = Math.round((congestedCount / total) * 100);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex flex-col gap-2.5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <h3 className="font-extrabold text-xs tracking-wide text-slate-900 uppercase flex items-center gap-1.5">
          <BarChart2 className="w-3.5 h-3.5 text-sky-500" />
          <span>ROAD NETWORK CONGESTION</span>
        </h3>
        <span className="text-[10px] text-slate-400 font-semibold">
          {total} Segments Tracked
        </span>
      </div>

      {/* Stacked Progress Bar */}
      <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex shadow-inner">
        <div style={{ width: `${lowPct}%` }} className="bg-emerald-500 transition-all" title={`Low: ${lowPct}%`} />
        <div style={{ width: `${modPct}%` }} className="bg-amber-500 transition-all" title={`Moderate: ${modPct}%`} />
        <div style={{ width: `${highPct}%` }} className="bg-orange-500 transition-all" title={`High: ${highPct}%`} />
        <div style={{ width: `${congPct}%` }} className="bg-red-500 transition-all" title={`Congested: ${congPct}%`} />
      </div>

      {/* Legend list with counts */}
      <div className="grid grid-cols-2 gap-2 text-xs font-semibold pt-1">
        <div className="flex items-center justify-between p-1.5 bg-emerald-50/50 rounded-lg border border-emerald-100">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-slate-700 text-[11px]">Free Flow</span>
          </div>
          <span className="text-emerald-700 font-extrabold text-xs">{lowCount}</span>
        </div>

        <div className="flex items-center justify-between p-1.5 bg-amber-50/50 rounded-lg border border-amber-100">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-slate-700 text-[11px]">Moderate</span>
          </div>
          <span className="text-amber-700 font-extrabold text-xs">{moderateCount}</span>
        </div>

        <div className="flex items-center justify-between p-1.5 bg-orange-50/50 rounded-lg border border-orange-100">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-orange-500" />
            <span className="text-slate-700 text-[11px]">Heavy</span>
          </div>
          <span className="text-orange-700 font-extrabold text-xs">{highCount}</span>
        </div>

        <div className="flex items-center justify-between p-1.5 bg-red-50/50 rounded-lg border border-red-100">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-slate-700 text-[11px]">Bottleneck</span>
          </div>
          <span className="text-red-700 font-extrabold text-xs">{congestedCount}</span>
        </div>
      </div>
    </div>
  );
}
