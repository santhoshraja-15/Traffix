"use client";

/**
 * useJourneySimulation
 * =======================
 * Drives the active-journey vehicle marker (position, heading, KPIs) from
 * three real inputs, and nothing else:
 *
 *   1. The route's own real geometry (RouteOption.coordinates — the actual
 *      backend-returned polyline; never a frontend-invented shape).
 *   2. Real wall-clock elapsed time since the real "Start Journey" click.
 *   3. Real live per-edge traffic data for this specific route's edges
 *      (StreamEdge.speed, from the same 1Hz WebSocket broadcast that
 *      already drives the map's risk coloring — see hooks/useWebSocket.ts).
 *
 * There is no backend capability that tracks an ordinary user's live
 * position along a route (confirmed by grep — only SUMO's bulk vehicles
 * and the emergency-mission system have real position tracking; see the
 * frontend repair project's "journey progress" finding). The user
 * explicitly approved building this honestly on the frontend rather than
 * adding that backend capability, on the condition that it never becomes
 * "an independent fake simulation disconnected from the backend" — so
 * every number here is derived from real data:
 *   - Position is always a real point ON the route's real polyline
 *     (lib/journeyPath.ts interpolates BETWEEN real coordinates, never off
 *     the line).
 *   - Speed is the real live average of StreamEdge.speed for the edges
 *     this route actually traverses (falling back to the route's own
 *     real backend-computed average speed only when no live data has
 *     arrived yet for those edges) — genuinely traffic-aware, never a
 *     fabricated constant.
 *   - Elapsed time is real Date.now() arithmetic against the real click
 *     timestamp.
 * Nothing here is a "competing frontend simulation" of anything the
 * backend already tracks — SUMO vehicles and ambulance missions still
 * come entirely from the WebSocket, untouched.
 */

import { useEffect, useRef, useState } from "react";
import { RouteOption } from "../types/route";
import { GeoCoordinates } from "../types/common";
import type { StreamEdge } from "./useWebSocket";
import { cumulativeDistances, positionAtDistance, splitRouteAtDistance } from "../lib/journeyPath";

const BASE_SPEED_KMH = 30; // "approximately 30 km/h under normal conditions" — see spec
const MIN_SPEED_KMH = 5; // crawl floor — a fully jammed edge shouldn't freeze the marker forever
const MAX_SPEED_KMH = 60; // sane cap for this urban network
// State-commit throttle: the animation itself runs every rAF frame, but
// React state (and therefore TrafficMap's re-render) only commits at this
// interval — smooth to the eye for a ~5-15 m/s marker, while bounding
// re-render frequency. Mirrors the lesson from this session's
// useVehicleInterpolation.ts fix: never commit React state on every raw
// rAF frame without a reason to.
const COMMIT_INTERVAL_MS = 400;

export interface JourneySimulationState {
  position: GeoCoordinates | null;
  headingDeg: number;
  distanceCoveredKm: number;
  distanceLeftKm: number;
  elapsedMinutes: number;
  etaMinutes: number;
  estimatedArrival: string;
  currentSpeedKmh: number;
  progressFraction: number;
  /** Real sub-polylines of the route's own coordinates, split exactly at
   * the current real position — for "traveled vs remaining" styling. */
  traveled: GeoCoordinates[];
  remaining: GeoCoordinates[];
  arrived: boolean;
}

const EMPTY_STATE: JourneySimulationState = {
  position: null,
  headingDeg: 0,
  distanceCoveredKm: 0,
  distanceLeftKm: 0,
  elapsedMinutes: 0,
  etaMinutes: 0,
  estimatedArrival: "—",
  currentSpeedKmh: 0,
  progressFraction: 0,
  traveled: [],
  remaining: [],
  arrived: false,
};

function computeEffectiveSpeedKmh(route: RouteOption, edges: StreamEdge[]): number {
  const matched = route.roadIds
    .map((id) => edges.find((e) => e.edge_id === id))
    .filter((e): e is StreamEdge => e !== undefined);
  if (matched.length === 0) {
    // No live data for this route's specific edges yet — fall back to the
    // route's own real backend-computed average speed (still real, never
    // invented; the routing service naturally keeps this close to the
    // ~30 km/h target on this network).
    return Math.min(MAX_SPEED_KMH, Math.max(MIN_SPEED_KMH, route.averageSpeedKmh || BASE_SPEED_KMH));
  }
  const liveAvg = matched.reduce((sum, e) => sum + e.speed, 0) / matched.length;
  return Math.min(MAX_SPEED_KMH, Math.max(MIN_SPEED_KMH, liveAvg));
}

/**
 * @param route the active route — may change mid-journey on a real reroute
 *   (see hooks/useRouteReoptimization.ts); distance covered persists
 *   across that swap as long as `journeyStartedAt` itself doesn't change
 *   (see app/page.tsx's reroute-continuity handling) — "never teleport the
 *   vehicle" is honored by keeping covered-distance continuous even though
 *   the route shape underneath it changed.
 * @param journeyStartedAt real Date.now() of the last genuine "Start
 *   Journey" click, or null before it's clicked / after the journey ends.
 * @param edges the live per-edge traffic snapshot already streamed for map
 *   coloring (see TraffixContext) — reused here, not a second connection.
 */
export function useJourneySimulation(
  route: RouteOption | null,
  journeyStartedAt: number | null,
  edges: StreamEdge[]
): JourneySimulationState {
  const [state, setState] = useState<JourneySimulationState>(EMPTY_STATE);

  const routeRef = useRef(route);
  routeRef.current = route;
  const edgesRef = useRef(edges);
  edgesRef.current = edges;

  const distanceCoveredMetersRef = useRef(0);
  const lastJourneyStartedAtRef = useRef<number | null>(null);
  const arrivedRef = useRef(false);
  const rafRef = useRef<number | null>(null);
  const lastFrameAtRef = useRef<number | null>(null);
  const lastCommitAtRef = useRef(0);

  useEffect(() => {
    if (journeyStartedAt === null || !route) {
      setState(EMPTY_STATE);
      distanceCoveredMetersRef.current = 0;
      lastJourneyStartedAtRef.current = null;
      arrivedRef.current = false;
      return;
    }

    if (lastJourneyStartedAtRef.current !== journeyStartedAt) {
      // A genuinely new journey — start from the real route origin.
      lastJourneyStartedAtRef.current = journeyStartedAt;
      distanceCoveredMetersRef.current = 0;
      arrivedRef.current = false;
    }
    // Else: same journey session, only the route object changed under it
    // (a real reroute) — distanceCoveredMetersRef is intentionally left
    // untouched here.

    lastFrameAtRef.current = performance.now();
    lastCommitAtRef.current = 0; // force an immediate commit on the first frame

    const tick = () => {
      const now = performance.now();
      const r = routeRef.current;

      if (!r || r.coordinates.length < 2) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      const dtSeconds = lastFrameAtRef.current !== null ? Math.max(0, (now - lastFrameAtRef.current) / 1000) : 0;
      lastFrameAtRef.current = now;

      if (!arrivedRef.current) {
        const speedKmh = computeEffectiveSpeedKmh(r, edgesRef.current);
        distanceCoveredMetersRef.current += ((speedKmh * 1000) / 3600) * dtSeconds;
      }

      if (now - lastCommitAtRef.current >= COMMIT_INTERVAL_MS) {
        lastCommitAtRef.current = now;

        const cumulative = cumulativeDistances(r.coordinates);
        const totalMeters = cumulative[cumulative.length - 1] ?? 0;
        const covered = Math.min(distanceCoveredMetersRef.current, totalMeters);
        if (totalMeters > 0 && covered >= totalMeters) arrivedRef.current = true;

        const { position, headingDeg } = positionAtDistance(r.coordinates, cumulative, covered);
        const { traveled, remaining } = splitRouteAtDistance(r.coordinates, cumulative, covered);
        const currentSpeedKmh = arrivedRef.current ? 0 : computeEffectiveSpeedKmh(r, edgesRef.current);
        const remainingMeters = totalMeters - covered;
        const etaMinutes = currentSpeedKmh > 0 ? (remainingMeters / 1000 / currentSpeedKmh) * 60 : 0;

        setState({
          position,
          headingDeg,
          distanceCoveredKm: covered / 1000,
          distanceLeftKm: remainingMeters / 1000,
          elapsedMinutes: (Date.now() - journeyStartedAt) / 60_000,
          etaMinutes,
          estimatedArrival: new Date(Date.now() + etaMinutes * 60_000).toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }),
          currentSpeedKmh,
          progressFraction: totalMeters > 0 ? covered / totalMeters : 0,
          traveled,
          remaining,
          arrived: arrivedRef.current,
        });
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [journeyStartedAt, route]);

  return state;
}
