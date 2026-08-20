import { GeoCoordinates } from "./common";
import { CongestionLevel } from "./traffic";

export interface RouteOption {
  id: string;
  name: string;
  roadName: string; // e.g. "Road A", "Anna Salai"
  coordinates: GeoCoordinates[];
  roadIds: string[];
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
