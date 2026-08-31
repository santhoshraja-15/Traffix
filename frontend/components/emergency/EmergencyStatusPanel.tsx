"use client";

import { Ambulance, Hospital, Clock, ShieldAlert, ShieldOff } from "lucide-react";
import type { StreamMission, MissionState } from "@/hooks/useSimulationStream";

interface EmergencyStatusPanelProps {
  mission: StreamMission | null;
}

// One consistent badge treatment for the 8-state lifecycle (DESIGN_SYSTEM.md
// §7) — intensifying only at the states that matter most (corridor active
// through on-site response), everywhere else a calmer amber/sky tone.
const STATE_META: Record<MissionState, { label: string; className: string }> = {
  ambulance_dispatched: { label: "AMBULANCE DISPATCHED", className: "bg-amber-100 text-amber-800 border-amber-300" },
  green_corridor_active: { label: "GREEN CORRIDOR ACTIVE", className: "bg-emerald-600 text-white border-emerald-700 animate-pulse" },
  en_route_to_accident: { label: "EN ROUTE TO ACCIDENT", className: "bg-emerald-600 text-white border-emerald-700 animate-pulse" },
  ambulance_arrived: { label: "AMBULANCE ARRIVED", className: "bg-sky-600 text-white border-sky-700" },
  on_site_response: { label: "ON-SITE RESPONSE", className: "bg-red-600 text-white border-red-700 animate-pulse" },
  returning_to_hospital: { label: "RETURNING TO HOSPITAL", className: "bg-sky-100 text-sky-800 border-sky-300" },
  emergency_completed: { label: "MISSION COMPLETED", className: "bg-slate-200 text-slate-700 border-slate-300" },
};

function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export default function EmergencyStatusPanel({ mission }: EmergencyStatusPanelProps) {
  if (!mission) return null;

  const meta = STATE_META[mission.state];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Ambulance className="w-4 h-4 text-sky-600" />
          <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wide">
            Emergency Response
          </h3>
        </div>
        <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full border ${meta.className}`}>
          {meta.label}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-3 text-xs">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-1.5 text-slate-600">
            <Hospital className="w-3.5 h-3.5 text-rose-500" />
            <span className="font-semibold">{mission.hospital_name}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-600">
            <Ambulance className="w-3.5 h-3.5 text-sky-500" />
            <span className="font-semibold">{mission.unit_number}</span>
          </div>
        </div>

        {/* On-site countdown — driven entirely by the backend's own
            on_site_seconds_remaining (real simulation ticks), never a
            frontend setTimeout/wall-clock timer. */}
        {mission.state === "on_site_response" && mission.on_site_seconds_remaining !== null && (
          <div className="flex items-center justify-between p-2.5 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-1.5 text-red-800 font-bold">
              <Clock className="w-3.5 h-3.5" />
              <span>On-site response</span>
            </div>
            <span className="font-black text-red-700 tabular-nums text-sm">
              {formatCountdown(mission.on_site_seconds_remaining)}
            </span>
          </div>
        )}

        {/* Honest signal-priority state — MASTER_PROMPT.md: never claim
            traffic-light control that doesn't actually exist. */}
        <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
          {mission.signal_priority_available ? (
            <>
              <ShieldAlert className="w-3 h-3 text-emerald-500" />
              <span>Emergency signal priority active</span>
            </>
          ) : (
            <>
              <ShieldOff className="w-3 h-3" />
              <span>Signal priority unavailable in this simulation — corridor is route-priority only</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
