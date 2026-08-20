"use client";

/**
 * useSimulationStream  (Phase 3 re-export alias)
 * ================================================
 * Delegates all logic to useTrafficSocket (hooks/useWebSocket.ts).
 *
 * This file is kept as the canonical home for shared TypeScript types so that
 * the many consumers that import from "@/hooks/useSimulationStream" continue
 * to work without any import-path changes.
 */

import { DEMO_SIMULATION_ID } from "../lib/constants";
import { useTrafficSocket } from "./useWebSocket";

export type {
  StreamEdge,
  SimulationStreamPayload,
  EdgeRiskMap,
} from "./useWebSocket";

// ── Throttle constant (Step 2) — re-exported for badge display ───────────────
export const UI_THROTTLE_MS = 1000;

// ── Hook alias ───────────────────────────────────────────────────────────────

/**
 * Convenience wrapper around useTrafficSocket that always subscribes to
 * the DEMO_SIMULATION_ID ("anna-nagar-live").
 *
 * @param enabled  Pass `false` to stay disconnected (e.g. in SSR guards).
 */
export function useSimulationStream(enabled = true) {
  return useTrafficSocket(enabled ? DEMO_SIMULATION_ID : "");
}
