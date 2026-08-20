import { apiPost, apiGet } from "./api";
import { RouteSearchResult, RouteOption } from "../types/route";
import { MOCK_ROUTE_SEARCH_RESULT, MOCK_ROUTES } from "../lib/mockData";

// ── Route calculation (calls trafficx_risk_router.py) ────────────────────────
export async function calculateRoutes(
  origin: string,
  destination: string,
  mode: "simulation" | "realtime" = "simulation"
): Promise<RouteSearchResult> {
  try {
    return await apiPost<RouteSearchResult>("/navigation/route", {
      origin,
      destination,
      mode,
    });
  } catch {
    console.warn("[TRAFFIX] /navigation/route unavailable → mock");
    return MOCK_ROUTE_SEARCH_RESULT;
  }
}

// ── Dynamic reroute (called on accident / bottleneck) ────────────────────────
export async function recalculateIntersectionRoute(
  currentRoadId: string,
  destination: string
): Promise<RouteOption[]> {
  try {
    return await apiPost<RouteOption[]>("/navigation/reroute", {
      currentRoadId,
      destination,
    });
  } catch {
    console.warn("[TRAFFIX] /navigation/reroute unavailable → mock");
    return MOCK_ROUTES;
  }
}

// ── XGBoost route risk evaluation ────────────────────────────────────────────
export interface RouteRiskEvaluation {
  routeId: string;
  riskScore: number;
  highRiskSegments: number;
  riskExposurePct: number;
  recommendation: string;
  modelVersion: string;
}

export async function evaluateRouteRisk(
  routeId: string,
  waypoints: string[]
): Promise<RouteRiskEvaluation> {
  try {
    return await apiPost<RouteRiskEvaluation>("/navigation/risk-eval", {
      routeId,
      waypoints,
    });
  } catch {
    return {
      routeId,
      riskScore: routeId === "route_1" ? 0.71 : 0.22,
      highRiskSegments: routeId === "route_1" ? 3 : 1,
      riskExposurePct: routeId === "route_1" ? 68 : 18,
      recommendation:
        routeId === "route_1"
          ? "HIGH RISK — avoid Teynampet junction"
          : "LOW RISK — recommended route",
      modelVersion: "XGBoost v15",
    };
  }
}

// ── Resolve location string → coordinates ───────────────────────────────────
export interface LocationResolution {
  query: string;
  lat: number;
  lng: number;
  label: string;
  confidence: number;
}

const LOCATION_CACHE: Record<string, LocationResolution> = {
  "anna salai": { query: "anna salai", lat: 13.0482, lng: 80.2425, label: "Anna Salai, Chennai", confidence: 0.97 },
  "guindy":     { query: "guindy", lat: 13.0067, lng: 80.2206, label: "Guindy, Chennai", confidence: 0.95 },
  "t nagar":    { query: "t nagar", lat: 13.0418, lng: 80.2341, label: "T. Nagar, Chennai", confidence: 0.96 },
  "apollo hospital": { query: "apollo hospital", lat: 13.0601, lng: 80.2534, label: "Apollo Hospital, Greams Rd", confidence: 0.99 },
};

export async function resolveLocation(query: string): Promise<LocationResolution> {
  const key = query.toLowerCase().trim();
  try {
    return await apiPost<LocationResolution>("/navigation/resolve-location", { query });
  } catch {
    return (
      LOCATION_CACHE[key] ?? {
        query,
        lat: 13.0482,
        lng: 80.2425,
        label: query,
        confidence: 0.5,
      }
    );
  }
}
