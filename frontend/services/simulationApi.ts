import { apiPost } from "./api";
import { DEMO_SIMULATION_ID } from "../lib/constants";

/**
 * Real simulation lifecycle control — audited against app/api/simulation.py
 * and app/core/simulation_manager.py (see the /simulation page rework
 * commit for the full audit). Only two real, backend-backed operations
 * exist: start and stop of the one shared tick loop every page's
 * WebSocket connection already runs against (DEMO_SIMULATION_ID) — see
 * hooks/useWebSocket.ts, which auto-starts it on first connect.
 *
 * Deliberately NOT implemented here (confirmed to have no real backend
 * counterpart — see the audit): pause, resume, single-step, speed
 * multiplier, live scenario/network switching. Previous versions of this
 * file called nonexistent endpoints for those and silently returned a
 * fake `{ success: true }` on every failure — removed rather than kept,
 * since a fake success is worse than no button at all.
 */

export interface SimulationStartResult {
  simulation_id: string;
  status: string;
}

/** POST /simulation/start — real: spawns SimulationManager's background
 * tick loop (idempotent if already running for this id). Throws on
 * failure rather than pretending it succeeded. */
export async function startSimulation(): Promise<SimulationStartResult> {
  return apiPost<SimulationStartResult>("/simulation/start", {
    simulation_id: DEMO_SIMULATION_ID,
  });
}

export interface SimulationStopResult {
  simulation_id: string;
  status: string;
  tick: number;
  elapsed_seconds: number;
  active_vehicles: number;
}

/** POST /simulation/stop/{id} — real: cancels the background tick loop.
 * Note this is the SAME simulation every page's live data depends on
 * (see hooks/useWebSocket.ts) — stopping it here stops the live feed
 * everywhere in the app, not just this page. */
export async function stopSimulation(): Promise<SimulationStopResult> {
  return apiPost<SimulationStopResult>(`/simulation/stop/${DEMO_SIMULATION_ID}`, {});
}
