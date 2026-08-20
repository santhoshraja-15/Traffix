"use client";

import { ArrowRight, CornerUpRight, CornerUpLeft, ArrowUp } from "lucide-react";
import { TurnInstruction } from "../../types/navigation";

interface NavigationBarProps {
  instruction?: TurnInstruction;
  areaName?: string;
}

export default function NavigationBar({
  instruction = {
    instruction: "Turn right onto Anna Salai Direct",
    distanceMeters: 250,
    timeSeconds: 30,
    turnType: "right",
    roadName: "Anna Salai Direct",
  },
  areaName = "Anna Salai Corridor",
}: NavigationBarProps) {
  
  const getTurnIcon = (type: string) => {
    switch (type) {
      case "left":
        return <CornerUpLeft className="w-5 h-5 text-sky-400" />;
      case "right":
        return <CornerUpRight className="w-5 h-5 text-sky-400" />;
      default:
        return <ArrowUp className="w-5 h-5 text-sky-400" />;
    }
  };

  return (
    <div className="bg-slate-900/90 text-white backdrop-blur-md px-4 py-2.5 rounded-t-xl border-b border-slate-700/50 flex items-center justify-between gap-4 z-20">
      
      {/* Area Name Header */}
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        <h2 className="font-bold text-xs tracking-wide text-slate-200">
          Route Map — <span className="text-white font-extrabold">{areaName}</span>
        </h2>
      </div>

      {/* Directions Panel Banner */}
      <div className="flex items-center gap-3 bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700">
        <div className="p-1 rounded bg-sky-500/20">
          {getTurnIcon(instruction.turnType)}
        </div>
        <div>
          <div className="font-bold text-xs text-white">
            {instruction.instruction}
          </div>
          <div className="text-[10px] text-slate-400 flex items-center gap-2">
            <span>in {instruction.distanceMeters} m</span>
            <span>•</span>
            <span>~{instruction.timeSeconds} sec</span>
          </div>
        </div>
      </div>

    </div>
  );
}
