"use client";

import { Play, Square, Info } from "lucide-react";

interface SimulationControlsProps {
  /** Inferred from real tick activity (see app/simulation/page.tsx) — the
   * WebSocket socket itself stays open for a while after the tick loop
   * actually stops (confirmed live: ~35s before the backend closes the
   * idle socket), so "wsConnected" alone is NOT a safe signal for whether
   * the simulation is actually producing ticks. This is deliberately an
   * observation ("ticks arrived recently"), not a claimed backend status
   * field — the backend doesn't expose one. */
  looksActive: boolean;
  busy: boolean;
  error: string | null;
  onStart: () => void;
  onStop: () => void;
}

/**
 * Real simulation lifecycle controls — audited against
 * app/core/simulation_manager.py. Only start/stop of the background tick
 * loop are real backend operations; a previous version of this component
 * also had Pause, Step, and a Speed slider wired to frontend functions
 * that called backend paths which don't exist at all (every click
 * silently "succeeded" without doing anything). Removed rather than kept
 * looking functional — see the honest note below instead.
 */
export default function SimulationControls({ looksActive, busy, error, onStart, onStop }: SimulationControlsProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900">Simulation Lifecycle Controls</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Controls the one real simulation every page&apos;s live data depends on
          </p>
        </div>
        <span
          className={`text-[10px] font-bold px-2 py-1 rounded-full border shrink-0 ${
            looksActive
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-slate-100 text-slate-500 border-slate-200"
          }`}
        >
          {looksActive ? "Ticks arriving" : "No recent ticks"}
        </span>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Both buttons stay clickable regardless of the inferred state
            above — Start is a safe no-op if already running, and there's
            no authoritative "is it running" field from the backend to
            gate on reliably (see looksActive's doc comment). Only `busy`
            (this click's own request in flight) blocks re-clicking. */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={onStart}
            disabled={busy}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-extrabold text-white shadow-sm transition-all bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40"
          >
            <Play className="w-4 h-4" />
            Start
          </button>

          <button
            onClick={onStop}
            disabled={busy}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 transition-all disabled:opacity-40"
          >
            <Square className="w-4 h-4" />
            Stop
          </button>
        </div>

        {error && (
          <p className="text-xs text-red-600 font-semibold bg-red-50 border border-red-200 rounded-lg p-2.5">
            {error}
          </p>
        )}

        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2.5 flex items-start gap-2">
          <span className="font-bold shrink-0">⚠</span>
          <span>
            Stopping ends the live simulation for the whole app, not just this page — the map,
            KPIs, and every other real-time panel go quiet until it&apos;s started again.
          </span>
        </p>

        {/* Honest disclosure — see the /simulation page audit for the full
            reasoning: SimulationManager's tick loop has no pause flag, no
            single-step entry point, and no speed-multiplier concept today. */}
        <div className="flex items-start gap-2 p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500">
          <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
          <span>
            Pause, single-step, and speed control aren&apos;t available in this deployment — the
            simulation engine runs continuously at real time (1 tick = 1 real second) with no
            pause/step/speed mechanism built. Adding one would be a real backend change, not
            something this page can fake.
          </span>
        </div>
      </div>
    </div>
  );
}
