"use client";

import { Play, Square, Pause, SkipForward, Info } from "lucide-react";

interface SimulationControlsProps {
  /** Inferred from real tick activity (see app/simulation/page.tsx) — the
   * WebSocket socket itself stays open for a while after the tick loop
   * actually stops (confirmed live: ~35s before the backend closes the
   * idle socket), so "wsConnected" alone is NOT a safe signal for whether
   * the simulation is actually producing ticks. This is deliberately an
   * observation ("ticks arrived recently"), not a claimed backend status
   * field — the backend doesn't expose one. */
  looksActive: boolean;
  /** Real — set from the response of the real pause/resume/step calls
   * (see app/simulation/page.tsx), not inferred. */
  paused: boolean;
  busy: boolean;
  error: string | null;
  onStart: () => void;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
  onStep: () => void;
}

/**
 * Real simulation lifecycle controls — audited against
 * app/core/simulation_manager.py. Start/Stop/Pause/Resume/Step are all
 * real backend operations now: SimulationManager's tick loop checks a
 * real pause flag every iteration (no TraCI/mock step, no ML inference,
 * no broadcast, no tick advance while paused), and Step queues exactly
 * one real tick to run. Speed control and scenario/network switching are
 * still genuinely unavailable — see the note below, not a fake control.
 */
export default function SimulationControls({
  looksActive,
  paused,
  busy,
  error,
  onStart,
  onStop,
  onPause,
  onResume,
  onStep,
}: SimulationControlsProps) {
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
            paused
              ? "bg-amber-50 text-amber-700 border-amber-200"
              : looksActive
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-slate-100 text-slate-500 border-slate-200"
          }`}
        >
          {paused ? "Paused" : looksActive ? "Ticks arriving" : "No recent ticks"}
        </span>
      </div>

      <div className="p-5 flex flex-col gap-4">
        {/* Start/Stop stay clickable regardless of the inferred state above
            — Start is a safe no-op if already running, and there's no
            authoritative "is it running" field to gate on reliably (see
            looksActive's doc comment). Only `busy` (this click's own
            request in flight) blocks re-clicking. Pause/Resume toggle
            based on the real, response-derived `paused` flag; Step is only
            meaningful while paused (a running loop consumes a step request
            on its very next already-scheduled tick, with no visible
            difference), so it's disabled otherwise rather than pretending
            it did something. */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={onStart}
            disabled={busy}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-extrabold text-white shadow-sm transition-all bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40"
          >
            <Play className="w-4 h-4" />
            Start
          </button>

          {paused ? (
            <button
              onClick={onResume}
              disabled={busy}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 transition-all disabled:opacity-40"
            >
              <Play className="w-4 h-4" />
              Resume
            </button>
          ) : (
            <button
              onClick={onPause}
              disabled={busy}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 transition-all disabled:opacity-40"
            >
              <Pause className="w-4 h-4" />
              Pause
            </button>
          )}

          <button
            onClick={onStep}
            disabled={busy || !paused}
            title={paused ? "Advance exactly one real tick" : "Pause first to single-step"}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-all disabled:opacity-40"
          >
            <SkipForward className="w-4 h-4" />
            Step +1
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
            KPIs, and every other real-time panel go quiet until it&apos;s started again. Pausing
            has the same whole-app effect but resumes exactly where it left off.
          </span>
        </p>

        {/* Honest disclosure — still true after adding real pause/step:
            SimulationManager has no speed-multiplier concept, and the
            routing graph / SUMO bridge are both hardcoded to
            scenarios/medium (see the page's own disclosure block below
            for the scenario/network specifics). */}
        <div className="flex items-start gap-2 p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500">
          <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
          <span>
            Speed control isn&apos;t available in this deployment — ticks always advance at real
            time (1 tick = 1 real second) when running. Adding a speed multiplier would be a
            real backend change, not something this page can fake.
          </span>
        </div>
      </div>
    </div>
  );
}
