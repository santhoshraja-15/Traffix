"use client";

import { useEffect, useState } from "react";
import Header from "@/components/common/Header";
import { ApplicationMode } from "@/types/common";
import { AccidentSeverity } from "@/types/accident";
import { ShieldAlert, Siren, Ambulance, Hospital, CheckCircle2 } from "lucide-react";
import AccidentPanel from "@/components/accident/AccidentPanel";
import EmergencyStatusPanel from "@/components/emergency/EmergencyStatusPanel";
import { useTraffixContext } from "@/context/TraffixContext";
import { simulateAccident, resolveAccident } from "@/services/accidentApi";
import { fetchAmbulanceUnits, AmbulanceUnit } from "@/services/ambulanceApi";

const STATUS_META: Record<string, { label: string; className: string }> = {
  available: { label: "AVAILABLE", className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  dispatched: { label: "DISPATCHED", className: "bg-amber-50 text-amber-700 border-amber-200" },
  at_scene: { label: "AT SCENE", className: "bg-red-50 text-red-700 border-red-200" },
  returning: { label: "RETURNING", className: "bg-sky-50 text-sky-700 border-sky-200" },
};

/**
 * Real Emergency Response Command page — this used to be an entirely
 * disconnected, fabricated simulation (hardcoded road IDs from the old
 * mock grid, local-only `incidentActive`/`dispatchedUnitId` state with no
 * backend calls at all, a `Date.now()`-based fake ETA countdown). Rebuilt
 * around the same real backend/components the main page already proved
 * out in Phase 7/8: real accident reporting, the real WebSocket-driven
 * mission lifecycle, and the real ambulance fleet (including idle units,
 * which the WebSocket stream doesn't carry — see GET /ambulance/units).
 */
export default function EmergencyPage() {
  const [mode, setMode] = useState<ApplicationMode>("simulation");
  const { accidents: liveAccidents, missions: liveMissions } = useTraffixContext();

  const [fleet, setFleet] = useState<AmbulanceUnit[]>([]);
  const [fleetError, setFleetError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      fetchAmbulanceUnits()
        .then((units) => {
          if (!cancelled) {
            setFleet(units);
            setFleetError(null);
          }
        })
        .catch(() => {
          if (!cancelled) setFleetError("Ambulance fleet data unavailable.");
        });
    };
    load();
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const handleSimulateAccident = async (edgeId: string, roadName: string, severity: AccidentSeverity) => {
    await simulateAccident(edgeId, severity);
  };

  const handleResolveAccident = async (accidentId: string) => {
    await resolveAccident(accidentId);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header mode={mode} onModeChange={setMode} />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Siren className="w-6 h-6 text-red-600" />
            Emergency Response Command
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real accident reporting, real ambulance dispatch, and the real emergency mission
            lifecycle — the same backend the main map uses, not a separate simulation.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <AccidentPanel
            onSimulateAccident={handleSimulateAccident}
            activeAccidentRoadName={liveAccidents[0]?.road_name || liveAccidents[0]?.edge_id}
          />

          {/* Real active missions — one card per real mission, all of them
              (not just the first, unlike the main page's compact banner). */}
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
              <Ambulance className="w-4 h-4 text-sky-600" />
              Active Missions ({liveMissions.length})
            </h3>
            {liveMissions.length === 0 ? (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 text-center text-xs text-slate-400">
                No emergency missions active right now.
              </div>
            ) : (
              liveMissions.map((m) => <EmergencyStatusPanel key={m.mission_id} mission={m} />)
            )}
          </div>
        </div>

        {/* Real active accidents — full list with resolve actions, not just
            the main page's single-accident banner. */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-500" />
            <h3 className="text-sm font-extrabold text-slate-900">
              Active Accidents ({liveAccidents.length})
            </h3>
          </div>
          <div className="p-4 flex flex-col gap-2">
            {liveAccidents.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-4">No active accidents.</p>
            ) : (
              liveAccidents.map((a) => (
                <div
                  key={a.accident_id}
                  className="flex items-center justify-between p-3 rounded-xl border border-red-200 bg-red-50/60 text-xs"
                >
                  <div>
                    <span className="font-bold text-red-900">{a.road_name || a.edge_id}</span>
                    <span className="text-red-700 uppercase font-bold ml-2">{a.severity}</span>
                  </div>
                  <button
                    onClick={() => handleResolveAccident(a.accident_id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-red-100 text-red-700 border border-red-300 rounded-lg font-bold transition-all"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Resolve
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Real ambulance fleet, including idle units — the WebSocket
            stream only carries missions in progress, so this is the only
            real view of the whole fleet's status. */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <Hospital className="w-4 h-4 text-rose-500" />
            <h3 className="text-sm font-extrabold text-slate-900">Ambulance Fleet</h3>
            <span className="text-xs text-slate-400 ml-auto">{fleet.length} real units</span>
          </div>
          <div className="overflow-x-auto">
            {fleetError ? (
              <p className="text-xs text-red-600 font-semibold text-center py-6">{fleetError}</p>
            ) : fleet.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-6">Loading real fleet data…</p>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="text-left px-5 py-2.5 text-slate-500 font-bold uppercase tracking-wider">Unit</th>
                    <th className="text-left px-4 py-2.5 text-slate-500 font-bold uppercase tracking-wider">Home Hospital</th>
                    <th className="text-right px-5 py-2.5 text-slate-500 font-bold uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {fleet.map((u) => {
                    const meta = STATUS_META[u.status] ?? {
                      label: u.status.toUpperCase(),
                      className: "bg-slate-50 text-slate-600 border-slate-200",
                    };
                    return (
                      <tr key={u.ambulance_id}>
                        <td className="px-5 py-2.5 font-bold text-slate-800">{u.unit_number}</td>
                        <td className="px-4 py-2.5 text-slate-600">{u.hospital_name}</td>
                        <td className="px-5 py-2.5 text-right">
                          <span className={`px-2 py-0.5 rounded-full border font-bold ${meta.className}`}>
                            {meta.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
