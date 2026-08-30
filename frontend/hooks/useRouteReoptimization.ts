"use client";

/**
 * useRouteReoptimization
 * =========================
 * Implements FLOW.md's continuous route-optimization loop:
 *
 *   CURRENT ROUTE ACTIVE → LIVE TRAFFIC/RISK STATE STREAMS IN →
 *   BACKEND RE-EVALUATES → meaningfully better route? → ROUTE UPDATED
 *
 * There is no backend-push mechanism for this yet (no per-session "this
 * user is on route X" tracking server-side — see FRONTEND_AUDIT.md-style
 * note in the Phase 6 commit for why that's a bigger architectural change
 * than this phase's scope). Instead: while a route is active, this hook
 * watches the real live per-edge risk along that route's own edges (the
 * same riskByEdge already streamed for map coloring) and, only when it has
 * moved meaningfully since the last check, asks the REAL backend routing
 * endpoint to recompute — the same endpoint and contract Phase 4 already
 * wired up. RoutingService re-refreshes live congestion weights on every
 * call (see app/services/routing_service.py), so this genuinely reflects
 * current backend state each time, not a cached or guessed answer.
 *
 * "ROUTE UPDATED" only ever fires when that fresh backend response is a
 * genuinely different route AND a meaningfully faster one — never on a
 * cosmetic/periodic refresh, and never a client-invented decision.
 */

import { useEffect, useRef } from "react";
import { calculateRoutes } from "@/services/navigationApi";
import { RouteOption, RouteSearchResult } from "@/types/route";
import type { EdgeRiskMap } from "@/hooks/useWebSocket";

// Rate limits: never re-check more often than MIN_INTERVAL even if risk is
// swinging wildly, but always re-check at least once every MAX_INTERVAL as
// a safety net (covers gradual drift too small to trip the delta alone).
const MIN_INTERVAL_MS = 10_000;
const MAX_INTERVAL_MS = 30_000;
const RISK_DELTA_THRESHOLD = 0.08; // avg risk along the route must move this much
// A new candidate must beat the active route by at least this fraction of
// its ETA (or this many minutes, whichever is larger) to count as
// "meaningfully better" — never reroute over noise-level differences.
const MIN_IMPROVEMENT_FRACTION = 0.08;
const MIN_IMPROVEMENT_MINUTES = 0.5;

export interface RouteUpdateEvent {
  previous: RouteOption;
  result: RouteSearchResult;
  reason: string;
}

interface UseRouteReoptimizationArgs {
  active: boolean;
  origin: string;
  destination: string;
  currentRoute: RouteOption | null;
  riskByEdge: EdgeRiskMap;
  onRouteUpdated: (event: RouteUpdateEvent) => void;
}

export function useRouteReoptimization({
  active,
  origin,
  destination,
  currentRoute,
  riskByEdge,
  onRouteUpdated,
}: UseRouteReoptimizationArgs) {
  // Refs for values read inside the effect without needing to be in its
  // dependency array (avoids re-subscribing/stale-closure issues — same
  // pattern as hooks/useWebSocket.ts).
  const stateRef = useRef({ active, origin, destination, currentRoute, onRouteUpdated });
  stateRef.current = { active, origin, destination, currentRoute, onRouteUpdated };

  const lastCheckRisk = useRef<number | null>(null);
  const lastCheckAt = useRef<number>(0);
  const checking = useRef(false);

  useEffect(() => {
    const { active, origin, destination, currentRoute, onRouteUpdated } = stateRef.current;

    if (!active || !currentRoute || currentRoute.roadIds.length === 0) {
      lastCheckRisk.current = null;
      return;
    }

    const risks = currentRoute.roadIds
      .map((id) => riskByEdge[id])
      .filter((v): v is number => v !== undefined);
    if (risks.length === 0) return; // no live risk data for this route yet
    const avgRisk = risks.reduce((a, b) => a + b, 0) / risks.length;

    if (lastCheckRisk.current === null) {
      // First observation for this active route — establish the baseline,
      // don't check yet (nothing to compare against).
      lastCheckRisk.current = avgRisk;
      lastCheckAt.current = Date.now();
      return;
    }

    const elapsed = Date.now() - lastCheckAt.current;
    const riskDelta = Math.abs(avgRisk - lastCheckRisk.current);
    const dueToMeaningfulChange = elapsed > MIN_INTERVAL_MS && riskDelta > RISK_DELTA_THRESHOLD;
    const dueToSafetyNet = elapsed > MAX_INTERVAL_MS;

    if (checking.current || (!dueToMeaningfulChange && !dueToSafetyNet)) return;

    checking.current = true;
    const previousAvgRisk = lastCheckRisk.current;
    lastCheckAt.current = Date.now();
    lastCheckRisk.current = avgRisk;

    calculateRoutes(origin, destination, riskByEdge)
      .then((result) => {
        const next = result.recommendedRoute;
        const isDifferentRoute = next.roadIds.join(",") !== currentRoute.roadIds.join(",");
        const improvement = currentRoute.etaMinutes - next.etaMinutes;
        const requiredImprovement = Math.max(
          MIN_IMPROVEMENT_MINUTES,
          currentRoute.etaMinutes * MIN_IMPROVEMENT_FRACTION
        );

        if (isDifferentRoute && improvement > requiredImprovement) {
          const riskDirection =
            avgRisk > previousAvgRisk
              ? `risk along your route rose from ${Math.round(previousAvgRisk * 100)}% to ${Math.round(avgRisk * 100)}%`
              : `traffic conditions changed`;
          const reason = `Live re-evaluation: ${riskDirection} — the backend found a route ${Math.round(
            improvement
          )} min faster.`;
          onRouteUpdated({ previous: currentRoute, result, reason });
        }
      })
      .catch(() => {
        // A failed background re-check shouldn't disrupt the active route —
        // the user keeps their current one; the next tick will try again.
      })
      .finally(() => {
        checking.current = false;
      });
  }, [riskByEdge]);
}
