"use client";

import { Wifi, WifiOff, Radio } from "lucide-react";

interface WsStatusBadgeProps {
  connected: boolean;
  mock?: boolean;
  step?: number;
}

export default function WsStatusBadge({ connected, mock, step }: WsStatusBadgeProps) {
  if (!connected) {
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 border border-red-200 text-xs font-bold text-red-700">
        <WifiOff className="w-3 h-3" />
        <span className="hidden sm:inline">WS Disconnected</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-700">
      {mock ? (
        <Radio className="w-3 h-3 text-emerald-500" />
      ) : (
        <Wifi className="w-3 h-3 text-emerald-500" />
      )}
      <span className="hidden sm:inline">
        {mock ? "Mock Feed" : "Live TraCI"}
      </span>
      {step !== undefined && (
        <span className="ml-1 font-mono text-[10px] text-emerald-600 tabular-nums">
          #{step}
        </span>
      )}
    </div>
  );
}
