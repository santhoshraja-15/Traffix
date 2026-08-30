"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Header from "@/components/common/Header";
import SimulationStatus from "@/components/simulation/SimulationStatus";
import SimulationControls from "@/components/simulation/SimulationControls";
import AccidentPanel from "@/components/accident/AccidentPanel";
import { useTraffixContext } from "@/context/TraffixContext";
import { useLiveKpi } from "@/hooks/useLiveData";
import { startSimulation, stopSimulation } from "@/services/simulationApi";
import { simulateAccident, resolveAccident } from "@/services/accidentApi";
import { fetchNetworkTopology } from "@/services/networkApi";
import { AccidentSeverity } from "@/types/accident";
import { Cpu, ShieldAlert, ArrowRight, CheckCircle2 } from "lucide-react";

/**
 * Real Simulation Engine control page.
 *
 * Audited against app/api/simulation.py, app/core/simulation_manager.py,
 * app/integrations/sumo_bridge.py, and app/integrations/sumo_network_loader.py
 * before rewriting (see the Phase 13 commit for the full write-up). Real:
 * start/stop of the one shared tick loop (the same simulation every page's
 * live data already depends on — see hooks/useWebSocket.ts, which
 * auto-starts it on first connect), and real accident injection (the same
 * AccidentPanel/backend flow already proven on the main page and
 * /emergency — not a second implementation).
 *
 * Confirmed NOT real, and not faked here: pause/step/speed control (no
 * such mechanism exists in SimulationManager's tick loop) and live
 * scenario/network switching (app/integrations/sumo_network_loader.py and
 * sumo_bridge.py are both hardcoded to scenarios/medium — nothing reads
 * the scenarios/low, high, or congested directories that exist on disk).
 */
export default function SimulationPage() {
  const { wsConnected, wsStep, dataSource, edges, accidents: liveAccidents } = useTraffixContext();
  const { kpi } = useLiveKpi(edges);

  const [busy, setBusy] = useState(false);
  const [controlError, setControlError] = useState<string | null>(null);
  const [networkEdgeCount, setNetworkEdgeCount] = useState<number | null>(null);
  const [networkArea, setNetworkArea] = useState<string | null>(null);

  // Real, derived "ticks arriving recently" signal — NOT the same as
  // wsConnected. Confirmed live that the WebSocket socket itself stays
  // open for tens of seconds after the tick loop actually stops (the
  // backend only closes it once idle, separately from the loop
  // cancelling), so gating Start/Stop on wsConnected left Start
  // permanently stuck showing "Running" after a real Stop. This instead
  // tracks whether the real tick counter has actually moved recently.
  const [looksActive, setLooksActive] = useState(false);
  const lastTickRef = useRef<{ value: number; at: number }>({ value: -1, at: 0 });

  useEffect(() => {
    if (wsStep !== lastTickRef.current.value) {
      lastTickRef.current = { value: wsStep, at: Date.now() };
    }
  }, [wsStep]);

  useEffect(() => {
    const interval = setInterval(() => {
      setLooksActive(Date.now() - lastTickRef.current.at < 3000);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchNetworkTopology()
      .then((topo) => {
        setNetworkEdgeCount(topo.metadata?.edges ?? null);
        setNetworkArea(topo.metadata?.area ?? "Anna Nagar, Chennai");
      })
      .catch(() => {
        /* honest: leaves the "Loading real network metadata…" state visible */
      });
  }, []);

  const handleStart = async () => {
    setBusy(true);
    setControlError(null);
    try {
      await startSimulation();
    } catch (err) {
      setControlError(err instanceof Error ? err.message : "Failed to start the simulation.");
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    setBusy(true);
    setControlError(null);
    try {
      await stopSimulation();
    } catch (err) {
      setControlError(err instanceof Error ? err.message : "Failed to stop the simulation.");
    } finally {
      setBusy(false);
    }
  };

  // Real accident injection — the exact same backend flow AccidentPanel
  // already drives on the main page and /emergency (POST /accidents,
  // real capacity reduction). Not a second, separate implementation.
  const handleSimulateAccident = async (edgeId: string, roadName: string, severity: AccidentSeverity) => {
    await simulateAccident(edgeId, severity);
  };

  const handleResolveAccident = async (accidentId: string) => {
    await resolveAccident(accidentId);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-[1400px] w-full mx-auto p-6 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Cpu className="w-6 h-6 text-sky-500" />
            Simulation Engine
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real control over the live SUMO/mock tick loop — the same simulation the entire app
            reads from, not a separate demo.
          </p>
        </div>

        {/* Top row: real engine status + real lifecycle controls */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <SimulationStatus
            wsConnected={wsConnected}
            dataSource={dataSource}
            tick={wsStep}
            activeVehicles={kpi.activeVehicles}
            avgSpeedKmh={kpi.avgSpeedKmh}
            networkHealthPct={kpi.networkHealthPct}
            activeIncidents={liveAccidents.length}
            networkEdgeCount={networkEdgeCount}
            networkArea={networkArea}
          />
          <SimulationControls
            looksActive={looksActive}
            busy={busy}
            error={controlError}
            onStart={handleStart}
            onStop={handleStop}
          />
        </div>

        {/* Real accident injection — reuses the proven AccidentPanel/backend
            flow, not a duplicate fake implementation. */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <AccidentPanel
            onSimulateAccident={handleSimulateAccident}
            activeAccidentRoadName={liveAccidents[0]?.road_name || liveAccidents[0]?.edge_id}
          />

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col gap-3">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-500" />
              Active Accidents ({liveAccidents.length})
            </h3>
            {liveAccidents.length === 0 ? (
              <p className="text-xs text-slate-400">No active accidents right now.</p>
            ) : (
              <div className="flex flex-col gap-1.5">
                {liveAccidents.slice(0, 3).map((a) => (
                  <div key={a.accident_id} className="flex items-center justify-between text-xs p-2 bg-red-50/60 border border-red-100 rounded-lg gap-2">
                    <div className="min-w-0">
                      <span className="font-bold text-red-900">{a.road_name || a.edge_id}</span>{" "}
                      <span className="text-red-700 uppercase font-bold">{a.severity}</span>
                    </div>
                    <button
                      onClick={() => handleResolveAccident(a.accident_id)}
                      className="shrink-0 px-2 py-1 bg-white hover:bg-red-100 text-red-700 border border-red-300 rounded-lg font-bold transition-all"
                    >
                      Resolve
                    </button>
                  </div>
                ))}
              </div>
            )}
            <Link
              href="/emergency"
              className="mt-auto self-start flex items-center gap-1.5 text-xs font-bold text-sky-600 hover:text-sky-800 transition-all"
            >
              Full accident &amp; mission management
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Honest disclosure — scenario/network switching genuinely doesn't
            exist in this deployment (see the audit in this file's own doc
            comment above), so no interactive-looking control is shown for
            it. Real scenario directories (low/medium/high/congested) exist
            on disk but nothing in the backend reads them. */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex items-start gap-3">
          <CheckCircle2 className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-500">
            <span className="font-bold text-slate-700">Scenario / network switching isn&apos;t available.</span>{" "}
            This deployment&apos;s routing graph and (when connected) TraCI session are both fixed
            to the <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded">scenarios/medium</code> network —
            neither the graph loader nor the SUMO bridge reads the <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded">low</code>,{" "}
            <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded">high</code>, or{" "}
            <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded">congested</code> scenario files that exist
            on disk. Switching between them live would need real backend work, not a frontend control.
          </div>
        </div>
      </main>
    </div>
  );
}
