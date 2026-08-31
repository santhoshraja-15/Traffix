import { apiPost } from "./api";
import { DEMO_SIMULATION_ID } from "../lib/constants";

/**
 * Real simulation lifecycle control — audited against app/api/simulation.py
 * and app/core/simulation_manager.py (see the /simulation page rework
 * commit for the full audit). Real, backend-backed operations: start,
 * stop, pause, resume, and single-step of the one shared tick loop every
 * page's WebSocket connection already runs against (DEMO_SIMULATION_ID) —
 * see hooks/useWebSocket.ts, which auto-starts it on first connect.
 *
 * Still deliberately NOT implemented here (confirmed to have no real
 * backend counterpart — see the audit): a speed multiplier, and live
 * scenario/network switching. A previous version of this file called
 * nonexistent endpoints for those too and silently returned a fake
 * `{ success: true }` on every failure — removed rather than kept, since
 * a fake success is worse than no button at all.
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

export interface SimulationPauseStateResult {
  simulation_id: string;
  paused: boolean;
  tick: number;
}

/** POST /simulation/pause/{id} — real: sets a flag the tick loop itself
 * checks every iteration. While paused, no TraCI/mock step, no ML
 * inference, no broadcast, no tick advance — genuinely nothing happens,
 * not a frontend-simulated pause. */
export async function pauseSimulation(): Promise<SimulationPauseStateResult> {
  return apiPost<SimulationPauseStateResult>(`/simulation/pause/${DEMO_SIMULATION_ID}`, {});
}

/** POST /simulation/resume/{id} — real: clears the pause flag. */
export async function resumeSimulation(): Promise<SimulationPauseStateResult> {
  return apiPost<SimulationPauseStateResult>(`/simulation/resume/${DEMO_SIMULATION_ID}`, {});
}

/** POST /simulation/step/{id} — real: queues exactly one real tick (full
 * TraCI/mock step + inference + broadcast + tick increment) to run while
 * paused, then the loop re-pauses. Only meaningful while paused. */
export async function stepSimulation(): Promise<SimulationPauseStateResult> {
  return apiPost<SimulationPauseStateResult>(`/simulation/step/${DEMO_SIMULATION_ID}`, {});
}
