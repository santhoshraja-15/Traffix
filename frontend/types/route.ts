import { GeoCoordinates } from "./common";
import { CongestionLevel } from "./traffic";

// ── Real backend contract (app/models/route_models.py) ───────────────────────
// Raw shapes as the API actually returns them — kept separate from the
// frontend display type below (RouteOption) per TECHNICAL_DEEP_DIVE.md §3's
// adapter-layer guidance. Normalization happens in services/navigationApi.ts.

export interface ApiCandidateRoute {
  route_id: string;
  rank: number;
  travel_time: number; // seconds
  distance: number; // meters
  traffic_level: number; // 0.0-1.0
  congestion_level: "free_flow" | "light" | "moderate" | "heavy" | "severe";
  edges: string[];
  coords: GeoCoordinates[];
  road_names: string[];
}

export interface ApiRouteResponse {
  request_id: string;
  routes: ApiCandidateRoute[];
}

export interface LocationSuggestion {
  name: string;
  lat: number;
  lng: number;
  /** A real, routable edge on this street — used by the accident-location
   * picker to target real network data. */
  edge_id: string;
}

export interface RouteOption {
  id: string;
  name: string;
  roadName: string; // e.g. "Road A", "Anna Salai"
  coordinates: GeoCoordinates[];
  roadIds: string[];
  /** Full real ordered street names traversed (backend-deduplicated
   * consecutive repeats, unnamed edges dropped) — used to build real
   * turn-by-turn directions, see lib/turnInstructions.ts. */
  roadNames: string[];
  distanceKm: number;
  etaMinutes: number;
  averageSpeedKmh: number;
  congestion: CongestionLevel;
  riskScore: number; // 0.0 to 1.0
  score: number; // overall calculated score
  isRecommended: boolean;
  reasoning: string;
  highRiskEdgesCount: number;
}

export interface RouteSearchResult {
  shortestRoute: RouteOption;
  optimalRoutes: RouteOption[];
  recommendedRoute: RouteOption;
  timestamp: string;
}
