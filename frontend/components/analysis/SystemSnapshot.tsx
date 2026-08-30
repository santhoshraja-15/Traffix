"use client";

import { useEffect, useRef, useState } from "react";
import { Car, ShieldAlert, Siren, Gauge, History } from "lucide-react";
import { useTraffixContext } from "@/context/TraffixContext";
import { useLiveKpi } from "@/hooks/useLiveData";

interface SeenAccident {
  accident_id: string;
  road_name: string;
  severity: string;
  reported_at: string;
  resolved: boolean;
}

/**
 * Real current-state snapshot — replaces the old "System Impact" panel,
 * which fabricated an entire 8-week before/after deployment study that
 * never happened. Everything here is either the live network state right
 * now, or a real log of accidents/missions this browser has actually
 * observed in the current session (explicitly labeled as such — never
 * presented as a longitudinal study).
 */
export default function SystemSnapshot() {
  const { edges, accidents: liveAccidents, missions: liveMissions } = useTraffixContext();
  const { kpi } = useLiveKpi(edges);

  const seenRef = useRef<Map<string, SeenAccident>>(new Map());
  const [seenAccidents, setSeenAccidents] = useState<SeenAccident[]>([]);

  useEffect(() => {
    const seen = seenRef.current;
    const activeIds = new Set(liveAccidents.map((a) => a.accident_id));

    for (const a of liveAccidents) {
      if (!seen.has(a.accident_id)) {
        seen.set(a.accident_id, {
          accident_id: a.accident_id,
          road_name: a.road_name || a.edge_id,
          severity: a.severity,
          reported_at: a.reported_at,
          resolved: false,
        });
      }
    }
    // Mark anything previously seen but no longer active as resolved —
    // real state transition, not a guess.
    for (const entry of seen.values()) {
      if (!activeIds.has(entry.accident_id) && !entry.resolved) {
        entry.resolved = true;
      }
    }

    setSeenAccidents(
      Array.from(seen.values()).sort(
        (a, b) => new Date(b.reported_at).getTime() - new Date(a.reported_at).getTime()
      )
    );
  }, [liveAccidents]);

  return (
    <div className="flex flex-col gap-5">
      {/* Current totals */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <h3 className="text-sm font-extrabold text-slate-900 mb-3">Network Right Now</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <SnapshotCard icon={Car} label="Active Vehicles" value={kpi.activeVehicles.toLocaleString()} color="sky" />
          <SnapshotCard icon={Gauge} label="Avg Speed" value={`${kpi.avgSpeedKmh.toFixed(1)} km/h`} color="violet" />
          <SnapshotCard icon={Gauge} label="Network Health" value={`${kpi.networkHealthPct}%`} color="emerald" />
          <SnapshotCard
            icon={ShieldAlert}
            label="High-Risk Segments"
            value={String(kpi.highCount + kpi.congestedCount)}
            color="red"
          />
        </div>
      </div>

      {/* Active emergency missions */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <h3 className="text-sm font-extrabold text-slate-900 mb-3 flex items-center gap-2">
          <Siren className="w-4 h-4 text-amber-500" />
          Active Emergency Missions ({liveMissions.length})
        </h3>
        {liveMissions.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">No emergency missions active right now.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {liveMissions.map((m) => (
              <div
                key={m.mission_id}
                className="flex items-center justify-between p-2.5 rounded-lg border border-amber-200 bg-amber-50/60 text-xs"
              >
                <div>
                  <span className="font-bold text-slate-800">{m.unit_number}</span>
                  <span className="text-slate-500"> · {m.hospital_name}</span>
                </div>
                <span className="font-bold text-amber-700 uppercase text-[10px] tracking-wide">
                  {m.state.replace(/_/g, " ")}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Real accident log — this session only */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <h3 className="text-sm font-extrabold text-slate-900 mb-1 flex items-center gap-2">
          <History className="w-4 h-4 text-slate-500" />
          Accident Log — This Session
        </h3>
        <p className="text-xs text-slate-500 mb-3">
          Real accidents actually reported while this page has been open. Not a historical
          deployment study — resets when the page reloads.
        </p>
        {seenAccidents.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">No accidents reported yet this session.</p>
        ) : (
          <div className="flex flex-col gap-1.5 max-h-64 overflow-y-auto">
            {seenAccidents.map((a) => (
              <div
                key={a.accident_id}
                className="flex items-center justify-between p-2 rounded-lg border border-slate-100 text-xs"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${a.resolved ? "bg-emerald-500" : "bg-red-500"}`}
                  />
                  <span className="font-semibold text-slate-700">{a.road_name}</span>
                  <span className="text-slate-400 uppercase text-[10px] font-bold">{a.severity}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <span>{new Date(a.reported_at).toLocaleTimeString("en-IN", { hour12: false })}</span>
                  <span className={a.resolved ? "text-emerald-600 font-bold" : "text-red-600 font-bold"}>
                    {a.resolved ? "RESOLVED" : "ACTIVE"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SnapshotCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Car;
  label: string;
  value: string;
  color: "sky" | "violet" | "emerald" | "red";
}) {
  const colorMap = {
    sky: "bg-sky-50 border-sky-200 text-sky-700",
    violet: "bg-violet-50 border-violet-200 text-violet-700",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-700",
    red: "bg-red-50 border-red-200 text-red-700",
  } as const;
  return (
    <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${colorMap[color]}`}>
      <Icon className="w-4 h-4 opacity-80" />
      <div>
        <p className="text-[10px] font-bold uppercase tracking-wider opacity-70">{label}</p>
        <p className="text-sm font-extrabold">{value}</p>
      </div>
    </div>
  );
}
