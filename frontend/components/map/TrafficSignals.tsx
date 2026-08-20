"use client";

import { TrafficSignal } from "../../types/traffic";

interface TrafficSignalsProps {
  signals?: TrafficSignal[];
}

export default function TrafficSignals({ signals = [] }: TrafficSignalsProps) {
  if (signals.length === 0) return null;

  return (
    <div className="contents">
      {signals.map((sig) => (
        <div
          key={sig.id}
          className="flex items-center gap-1 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700 text-[10px] text-white shadow-sm"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              sig.state === "green"
                ? "bg-emerald-400 animate-pulse"
                : sig.state === "red"
                ? "bg-red-500"
                : "bg-amber-400"
            }`}
          />
          <span className="font-bold">{sig.name}:</span>
          <span className="text-slate-300">{sig.remainingPhaseSec}s</span>
        </div>
      ))}
    </div>
  );
}
