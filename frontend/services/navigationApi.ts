import { apiPost, ApiError } from "./api";
import { fetchNetworkLocations } from "./networkApi";
import {
  ApiCandidateRoute,
  ApiRouteResponse,
  LocationSuggestion,
  RouteOption,
  RouteSearchResult,
} from "../types/route";
import { CongestionLevel } from "../types/traffic";
import type { EdgeRiskMap } from "../hooks/useWebSocket";

// ── Errors — thrown, not silently swallowed into mock data ───────────────────
// See TECHNICAL_DEEP_DIVE.md §8's error-handling matrix: "Invalid/unsupported
// source or destination" and "No route available" each need a specific,
// user-visible state, not a full-app crash and not a fabricated fallback.

export class LocationNotFoundError extends Error {
  constructor(public field: "origin" | "destination", public query: string) {
    super(`"${query}" was not found in the supported Anna Nagar network.`);
    this.name = "LocationNotFoundError";
  }
}

export class NoRouteFoundError extends Error {
  constructor() {
    super("No route available for the selected destination.");
    this.name = "NoRouteFoundError";
  }
}

// ── Real location search (backed by app/api/network.py locations) ───────────
// Fetched once and cached for the session — 129 real street names, small
// enough to hold in memory and filter client-side.

let locationsPromise: Promise<LocationSuggestion[]> | null = null;

export function loadRealLocations(): Promise<LocationSuggestion[]> {
  if (!locationsPromise) {
    locationsPromise = fetchNetworkLocations().catch((err) => {
      locationsPromise = null; // allow retry on next call rather than caching a failure forever
      throw err;
    });
  }
  return locationsPromise;
}

/** Case-insensitive exact match first, then substring match, against the
 * real location list. Returns null (never a guessed/default coordinate) if
 * nothing in the actual network matches. */
export async function resolveLocation(query: string): Promise<LocationSuggestion | null> {
  const q = query.trim().toLowerCase();
  if (!q) return null;

  const locations = await loadRealLocations();
  const exact = locations.find((l) => l.name.toLowerCase() === q);
  if (exact) return exact;
  return locations.find((l) => l.name.toLowerCase().includes(q)) ?? null;
}

// ── Route calculation — the real /api/routes endpoint ────────────────────────

const CONGESTION_MAP: Record<ApiCandidateRoute["congestion_level"], CongestionLevel> = {
  free_flow: "low",
  light: "low",
  moderate: "moderate",
  heavy: "high",
  severe: "congested",
};

function toRouteOption(route: ApiCandidateRoute, riskByEdge: EdgeRiskMap): RouteOption {
  const distanceKm = route.distance / 1000;
  const etaMinutes = route.travel_time / 60;
  const averageSpeedKmh = route.travel_time > 0 ? distanceKm / (route.travel_time / 3600) : 0;

  // Prefer real, live V15/V16 per-edge risk (riskByEdge, from the WebSocket
  // stream — see hooks/useWebSocket.ts) over the routing service's own
  // congestion estimate (traffic_level), when it's available for this
  // route's edges. Both are real backend-computed numbers either way —
  // never a value invented on the frontend.
  const liveRiskValues = route.edges
    .map((id) => riskByEdge[id])
    .filter((v): v is number => v !== undefined);
  const hasLiveRisk = liveRiskValues.length > 0;
  const riskScore = hasLiveRisk
    ? liveRiskValues.reduce((a, b) => a + b, 0) / liveRiskValues.length
    : route.traffic_level;
  const highRiskEdgesCount = hasLiveRisk ? liveRiskValues.filter((v) => v > 0.5).length : 0;

  const roadName =
    route.road_names.length > 0
      ? route.road_names.slice(0, 3).join(" → ")
      : `${route.edges.length}-segment route`;

  return {
    id: route.route_id,
    name: `Route ${route.rank + 1} (${roadName})`,
    roadName,
    coordinates: route.coords,
    roadIds: route.edges,
    distanceKm,
    etaMinutes,
    averageSpeedKmh,
    congestion: CONGESTION_MAP[route.congestion_level] ?? "moderate",
    riskScore,
    // Internal ordering aid derived from the real returned numbers — not
    // rendered anywhere in the UI (confirmed against components/routes/*).
    score: Math.max(0, 100 - route.rank * 10 - riskScore * 30),
    isRecommended: route.rank === 0, // backend already ranks candidates by real cost
    reasoning:
      route.rank === 0
        ? `Backend-ranked fastest of ${route.rank + 1} candidate route(s) — ${distanceKm.toFixed(1)} km, ~${Math.round(etaMinutes)} min via ${roadName}.`
        : `${distanceKm.toFixed(1)} km, ~${Math.round(etaMinutes)} min via ${roadName}.`,
    highRiskEdgesCount,
  };
}

/**
 * Resolve FROM/TO against the real network, then request the real route
 * from the backend routing engine. Throws LocationNotFoundError /
 * NoRouteFoundError on failure — callers show these, never fall back to
 * mock data (see FLOW.md's "Mode note").
 */
export async function calculateRoutes(
  origin: string,
  destination: string,
  riskByEdge: EdgeRiskMap = {}
): Promise<RouteSearchResult> {
  const [originLoc, destLoc] = await Promise.all([resolveLocation(origin), resolveLocation(destination)]);
  if (!originLoc) throw new LocationNotFoundError("origin", origin);
  if (!destLoc) throw new LocationNotFoundError("destination", destination);

  let response: ApiRouteResponse;
  try {
    response = await apiPost<ApiRouteResponse>("/routes", {
      source: { lat: originLoc.lat, lng: originLoc.lng },
      destination: { lat: destLoc.lat, lng: destLoc.lng },
      alternatives: 3,
    });
  } catch (err) {
    if (err instanceof ApiError && (err.status === 400 || err.status === 404)) {
      throw new NoRouteFoundError();
    }
    throw err;
  }

  const routes = response.routes.map((r) => toRouteOption(r, riskByEdge));
  if (routes.length === 0) throw new NoRouteFoundError();

  return {
    shortestRoute: routes[0],
    optimalRoutes: routes,
    recommendedRoute: routes[0],
    timestamp: new Date().toISOString(),
  };
}

// ── Not yet wired to a real backend endpoint ──────────────────────────────────
// Dynamic re-routing (continuous route optimization, Phase 6) and a
// dedicated per-route risk-evaluation endpoint (Phase 5) don't exist on the
// backend yet and these two functions are unused anywhere in the app today
// — left unimplemented rather than pointed at fabricated data or a
// nonexistent endpoint. Wire them up in their respective phases.
