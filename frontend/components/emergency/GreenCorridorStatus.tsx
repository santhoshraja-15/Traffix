"use client";

import { Zap, ArrowRight, CheckCircle2, Clock } from "lucide-react";

interface CorridorSegment {
  id: string;
  road: string;
  junction: string;
  signalOverride: "green-wave" | "pending" | "cleared";
  clearedAt: string | null;
}

const CORRIDOR_SEGMENTS: CorridorSegment[] = [
  {
    id: "seg-1",
    road: "Anna Salai (Nungambakkam → Teynampet)",
    junction: "Gemini Flyover",
    signalOverride: "green-wave",
    clearedAt: "17:51:02",
  },
  {
    id: "seg-2",
    road: "Teynampet Junction",
    junction: "MRTS Underpass Signal",
    signalOverride: "green-wave",
    clearedAt: "17:51:05",
  },
  {
    id: "seg-3",
    road: "Spurtank Rd Cross",
    junction: "Cenotaph Rd Signal",
    signalOverride: "pending",
    clearedAt: null,
  },
  {
    id: "seg-4",
    road: "Apollo Hospital Approach",
    junction: "Greams Rd Entry",
    signalOverride: "pending",
    clearedAt: null,
  },
];

const OVERRIDE_STYLES: Record<CorridorSegment["signalOverride"], string> = {
  "green-wave": "bg-emerald-100 text-emerald-700 border-emerald-200",
  pending: "bg-amber-100 text-amber-700 border-amber-200",
  cleared: "bg-slate-100 text-slate-500 border-slate-200",
};

const OVERRIDE_LABELS: Record<CorridorSegment["signalOverride"], string> = {
  "green-wave": "GREEN WAVE",
  pending: "PENDING",
  cleared: "CLEARED",
};

interface GreenCorridorStatusProps {
  active: boolean;
}

export default function GreenCorridorStatus({ active }: GreenCorridorStatusProps) {
  if (!active) return null;

  return (
    <div className="bg-white rounded-xl border border-emerald-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-emerald-100 bg-emerald-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center border border-emerald-200">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-emerald-900">Emergency Green Corridor</h3>
            <p className="text-xs text-emerald-700 font-medium">All signals on route overridden — ACTIVE</p>
          </div>
        </div>
        <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 text-white text-xs font-bold rounded-full animate-pulse">
          <span className="w-2 h-2 rounded-full bg-white inline-block" />
          LIVE
        </span>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Route Summary */}
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700 flex-wrap">
          <span className="px-2 py-1 bg-slate-100 rounded-lg border border-slate-200">Nungambakkam Station</span>
          {CORRIDOR_SEGMENTS.map((seg, idx) => (
            <span key={seg.id} className="flex items-center gap-2">
              <ArrowRight className="w-3 h-3 text-slate-400" />
              <span className="px-2 py-1 bg-slate-100 rounded-lg border border-slate-200">
                {seg.junction}
              </span>
            </span>
          ))}
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded-lg border border-emerald-200">
            Apollo Hospital
          </span>
        </div>

        {/* Segment Table */}
        <div className="flex flex-col gap-2">
          <p className="text-xs font-bold text-slate-700">Signal Override Status:</p>
          {CORRIDOR_SEGMENTS.map((seg) => (
            <div
              key={seg.id}
              className="flex items-center justify-between px-3 py-2.5 bg-slate-50 rounded-xl border border-slate-200"
            >
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-semibold text-slate-800">{seg.road}</span>
                <span className="text-xs text-slate-500">{seg.junction}</span>
              </div>
              <div className="flex items-center gap-2">
                {seg.clearedAt && (
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <Clock className="w-3 h-3" />
                    <span>{seg.clearedAt}</span>
                  </div>
                )}
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full border font-bold ${OVERRIDE_STYLES[seg.signalOverride]}`}
                >
                  {OVERRIDE_LABELS[seg.signalOverride]}
                </span>
                {seg.signalOverride === "green-wave" && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Progress bar */}
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between text-xs text-slate-500">
            <span>Corridor Coverage</span>
            <span className="font-bold text-emerald-700">2 / 4 junctions cleared</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full transition-all duration-700"
              style={{ width: "50%" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
