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
import type { EdgeRiskMap, StreamAccident } from "@/hooks/useWebSocket";

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
  /** True when the trigger was the active route passing through a real,
   * currently-active accident's edge — see FLOW.md's "ordinary-user
   * rerouting around the emergency zone" flow (Phase 9). */
  isEmergencyZone: boolean;
}

/**
 * Fired when the active route just started passing through a real,
 * currently-active accident's edge but the backend's freshly-recomputed
 * route was NOT a genuinely faster alternative (isDifferentRoute or the
 * improvement bar failed) — an accident only ever makes the affected area
 * *worse*, so "beats what you were originally promised" often can't be
 * cleared even though the hazard itself is real. Rather than silently
 * saying nothing (the risk is real, the user should know) or fabricating a
 * reroute that isn't actually better, this carries the honest, real
 * accident record so the UI can warn without a false "we fixed it" claim.
 */
export interface EmergencyZoneWarningEvent {
  accident: StreamAccident;
}

interface UseRouteReoptimizationArgs {
  active: boolean;
  origin: string;
  destination: string;
  currentRoute: RouteOption | null;
  riskByEdge: EdgeRiskMap;
  /** Real, currently-active accidents — used only to recognize when the
   * active route itself passes through one, for the emergency-zone
   * messaging/urgency below. Never invents an accident. */
  accidents: StreamAccident[];
  onRouteUpdated: (event: RouteUpdateEvent) => void;
  /** Optional: called instead of onRouteUpdated when the route enters an
   * emergency zone but no genuinely faster alternative was found. */
  onEmergencyZoneWarning?: (event: EmergencyZoneWarningEvent) => void;
}

export function useRouteReoptimization({
  active,
  origin,
  destination,
  currentRoute,
  riskByEdge,
  accidents,
  onRouteUpdated,
  onEmergencyZoneWarning,
}: UseRouteReoptimizationArgs) {
  // Refs for values read inside the effect without needing to be in its
  // dependency array (avoids re-subscribing/stale-closure issues — same
  // pattern as hooks/useWebSocket.ts).
  const stateRef = useRef({
    active,
    origin,
    destination,
    currentRoute,
    accidents,
    onRouteUpdated,
    onEmergencyZoneWarning,
  });
  stateRef.current = {
    active,
    origin,
    destination,
    currentRoute,
    accidents,
    onRouteUpdated,
    onEmergencyZoneWarning,
  };

  const lastCheckRisk = useRef<number | null>(null);
  const lastCheckAt = useRef<number>(0);
  const wasInEmergencyZone = useRef(false);
  const checking = useRef(false);

  useEffect(() => {
    const { active, origin, destination, currentRoute, accidents, onRouteUpdated, onEmergencyZoneWarning } =
      stateRef.current;

    if (!active || !currentRoute || currentRoute.roadIds.length === 0) {
      lastCheckRisk.current = null;
      wasInEmergencyZone.current = false;
      return;
    }

    const risks = currentRoute.roadIds
      .map((id) => riskByEdge[id])
      .filter((v): v is number => v !== undefined);
    if (risks.length === 0) return; // no live risk data for this route yet
    const avgRisk = risks.reduce((a, b) => a + b, 0) / risks.length;

    // The active route now runs through a real, currently-active accident's
    // edge — check immediately rather than waiting for the risk delta or
    // the periodic safety net, matching FLOW.md's "IF emergency zone
    // congests → backend reroutes affected ordinary users" urgency.
    const accidentByEdgeId = new Map(accidents.map((a) => [a.edge_id, a] as const));
    const routeAccident = currentRoute.roadIds.map((id) => accidentByEdgeId.get(id)).find((a) => a !== undefined);
    const routeInEmergencyZone = routeAccident !== undefined;
    const justEnteredEmergencyZone = routeInEmergencyZone && !wasInEmergencyZone.current;
    wasInEmergencyZone.current = routeInEmergencyZone;

    if (lastCheckRisk.current === null) {
      // First observation for this active route — establish the baseline,
      // don't check yet (nothing to compare against), unless it's already
      // in an emergency zone the moment it's picked up.
      lastCheckRisk.current = avgRisk;
      lastCheckAt.current = Date.now();
      if (!justEnteredEmergencyZone) return;
    }

    const elapsed = Date.now() - lastCheckAt.current;
    const riskDelta = Math.abs(avgRisk - lastCheckRisk.current);
    const dueToMeaningfulChange = elapsed > MIN_INTERVAL_MS && riskDelta > RISK_DELTA_THRESHOLD;
    const dueToSafetyNet = elapsed > MAX_INTERVAL_MS;

    if (checking.current || (!dueToMeaningfulChange && !dueToSafetyNet && !justEnteredEmergencyZone)) return;

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
          const reason = routeInEmergencyZone
            ? "EMERGENCY ZONE AHEAD — rerouting to a lower-congestion road."
            : `Live re-evaluation: ${
                avgRisk > previousAvgRisk
                  ? `risk along your route rose from ${Math.round(previousAvgRisk * 100)}% to ${Math.round(avgRisk * 100)}%`
                  : "traffic conditions changed"
              } — the backend found a route ${Math.round(improvement)} min faster.`;
          onRouteUpdated({ previous: currentRoute, result, reason, isEmergencyZone: routeInEmergencyZone });
        } else if (routeInEmergencyZone && routeAccident) {
          // The route genuinely enters a real accident's edge, but nothing
          // the backend found actually beats the ETA the user was already
          // promised — an accident only ever makes the area worse, so that
          // bar frequently can't be cleared even though the hazard is real.
          // Warn honestly with the real accident record instead of either
          // staying silent or fabricating a "we rerouted you" claim.
          onEmergencyZoneWarning?.({ accident: routeAccident });
        }
      })
      .catch(() => {
        // A failed background re-check shouldn't disrupt the active route —
        // the user keeps their current one; the next tick will try again.
      })
      .finally(() => {
        checking.current = false;
      });
  }, [riskByEdge, accidents]);
}
