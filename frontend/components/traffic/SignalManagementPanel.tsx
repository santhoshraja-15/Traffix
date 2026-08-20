"use client";

import { useState } from "react";
import { TrafficCone, Zap, ShieldAlert, CheckCircle2, Sliders } from "lucide-react";
import { TrafficSignal } from "@/types/traffic";
import { MOCK_TRAFFIC_SNAPSHOT } from "@/lib/mockData";

interface SignalManagementPanelProps {
  signals?: TrafficSignal[];
}

export default function SignalManagementPanel({
  signals = MOCK_TRAFFIC_SNAPSHOT.signals,
}: SignalManagementPanelProps) {
  const [greenWaveActive, setGreenWaveActive] = useState(false);
  const [adaptiveMode, setAdaptiveMode] = useState(true);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col gap-3">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-2">
          <TrafficCone className="w-4 h-4 text-sky-500" />
          <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wide">
            TRAFFIC SIGNAL & ADAPTIVE TIMING
          </h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-bold">
          <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            {signals.length} Junctions Active
          </span>
        </div>
      </div>

      {/* Control Toggles: Adaptive AI & Emergency Green Corridor */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        {/* Adaptive Timing */}
        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
          <div>
            <span className="font-extrabold text-slate-900 block text-xs">Adaptive AI Cycle</span>
            <span className="text-[10px] text-slate-500">Auto-adjust by queue</span>
          </div>
          <input
            type="checkbox"
            checked={adaptiveMode}
            onChange={(e) => setAdaptiveMode(e.target.checked)}
            className="w-4 h-4 text-sky-600 rounded focus:ring-sky-500 accent-sky-500 cursor-pointer"
          />
        </div>

        {/* Emergency Green Wave */}
        <div className={`p-2.5 rounded-lg border flex items-center justify-between transition-all ${
          greenWaveActive
            ? "bg-emerald-50 border-emerald-300 text-emerald-950 shadow-xs"
            : "bg-slate-50 border-slate-200 text-slate-900"
        }`}>
          <div>
            <span className="font-extrabold text-xs block">Emergency Green Wave</span>
            <span className="text-[10px] text-slate-500">Force green corridor</span>
          </div>
          <button
            onClick={() => setGreenWaveActive(!greenWaveActive)}
            className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase transition-all ${
              greenWaveActive
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-slate-200 text-slate-700 hover:bg-slate-300"
            }`}
          >
            {greenWaveActive ? "ACTIVE" : "OVERRIDE"}
          </button>
        </div>
      </div>

      {/* Signal Status List */}
      <div className="flex flex-col gap-2">
        {signals.map((sig) => (
          <div
            key={sig.id}
            className="p-3 rounded-lg bg-slate-50/80 border border-slate-200 flex items-center justify-between text-xs"
          >
            <div className="flex items-center gap-2.5">
              <span
                className={`w-3 h-3 rounded-full ${
                  greenWaveActive
                    ? "bg-emerald-500 animate-ping"
                    : sig.state === "green"
                    ? "bg-emerald-500 animate-pulse"
                    : sig.state === "red"
                    ? "bg-red-500"
                    : "bg-amber-400"
                }`}
              />
              <div>
                <span className="font-extrabold text-slate-900 block text-xs">{sig.name}</span>
                <span className="text-[10px] text-slate-500 font-mono">
                  Cycle: {sig.cycleTimeSec}s | Phase: {greenWaveActive ? "FORCED GREEN" : sig.state.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="text-right">
              <span className="text-sm font-extrabold text-slate-900 font-mono">
                {greenWaveActive ? "HOLD" : `${sig.remainingPhaseSec}s`}
              </span>
              <span className="text-[10px] text-slate-400 block">Remaining</span>
            </div>
          </div>
        ))}
      </div>

      {/* Adaptive Recommendation Note */}
      {adaptiveMode && (
        <div className="bg-sky-50 border border-sky-200 p-2.5 rounded-lg text-[11px] text-sky-900 flex items-center gap-2">
          <Zap className="w-4 h-4 text-sky-600 shrink-0" />
          <span>
            <strong>AI Recommendation:</strong> Extended Teynampet green phase +12s to clear northbound queue.
          </span>
        </div>
      )}

    </div>
  );
}
