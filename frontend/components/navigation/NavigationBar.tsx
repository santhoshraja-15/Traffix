"use client";

import { CornerUpRight, CornerUpLeft, ArrowUp, MapPin, Compass } from "lucide-react";
import { TurnInstruction } from "../../types/navigation";

interface NavigationBarProps {
  /** Real, computed from the active route's own geometry — see
   * lib/turnInstructions.ts. Undefined (not a fake default) when no route
   * is active yet. */
  instruction?: TurnInstruction;
  areaName?: string;
}

export default function NavigationBar({ instruction, areaName = "Anna Nagar, Chennai" }: NavigationBarProps) {
  const getTurnIcon = (type: string) => {
    switch (type) {
      case "left":
        return <CornerUpLeft className="w-5 h-5 text-sky-400" />;
      case "right":
        return <CornerUpRight className="w-5 h-5 text-sky-400" />;
      case "destination":
        return <MapPin className="w-5 h-5 text-sky-400" />;
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

      {/* Directions Panel Banner — real, derived from the active route's own
          geometry (lib/turnInstructions.ts), or an honest empty state when
          no route is active. Never a placeholder pretending to be a turn. */}
      {instruction ? (
        <div className="flex items-center gap-3 bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700">
          <div className="p-1 rounded bg-sky-500/20">{getTurnIcon(instruction.turnType)}</div>
          <div>
            <div className="font-bold text-xs text-white">{instruction.instruction}</div>
            <div className="text-[10px] text-slate-400 flex items-center gap-2">
              <span>in {instruction.distanceMeters} m</span>
              {instruction.timeSeconds > 0 && (
                <>
                  <span>•</span>
                  <span>~{instruction.timeSeconds} sec</span>
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-2 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/60 text-slate-500">
          <Compass className="w-4 h-4" />
          <span className="text-[11px] font-semibold">Search a route to see directions</span>
        </div>
      )}
    </div>
  );
}
