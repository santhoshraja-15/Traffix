import { apiGet, apiPost } from "./api";
import { TrafficStateSnapshot } from "../types/traffic";
import { MOCK_TRAFFIC_SNAPSHOT } from "../lib/mockData";

// ── Traffic state ────────────────────────────────────────────────────────────
export async function fetchTrafficState(): Promise<TrafficStateSnapshot> {
  try {
    return await apiGet<TrafficStateSnapshot>("/traffic/state");
  } catch {
    console.warn("[TRAFFIX] /traffic/state unavailable → mock");
    return MOCK_TRAFFIC_SNAPSHOT;
  }
}

// ── Density snapshot per road segment ───────────────────────────────────────
export interface RoadDensity {
  roadId: string;
  label: string;
  vehiclesPerKm: number;
  avgSpeedKmh: number;
  occupancyPct: number;
  level: "free" | "moderate" | "heavy" | "bottleneck";
}

const MOCK_DENSITIES: RoadDensity[] = [
  { roadId: "road_anna_2", label: "Anna Salai (Teynampet)", vehiclesPerKm: 280, avgSpeedKmh: 22, occupancyPct: 73, level: "heavy" },
  { roadId: "road_mount_1", label: "Mount Flyover Jn", vehiclesPerKm: 140, avgSpeedKmh: 38, occupancyPct: 46, level: "moderate" },
  { roadId: "road_ring_2", label: "Guindy Ring Road", vehiclesPerKm: 450, avgSpeedKmh: 8, occupancyPct: 94, level: "bottleneck" },
  { roadId: "road_nungam_1", label: "Nungambakkam High Rd", vehiclesPerKm: 60, avgSpeedKmh: 52, occupancyPct: 18, level: "free" },
];

export async function fetchRoadDensities(): Promise<RoadDensity[]> {
  try {
    return await apiGet<RoadDensity[]>("/traffic/density");
  } catch {
    return MOCK_DENSITIES;
  }
}

// ── Network KPI summary ──────────────────────────────────────────────────────
export interface NetworkKpi {
  activeVehicles: number;
  avgSpeedKmh: number;
  networkHealthPct: number;
  activeIncidents: number;
  throughputVehPerHr: number;
  congestionIndex: number;
}

const MOCK_KPI: NetworkKpi = {
  activeVehicles: 1247,
  avgSpeedKmh: 34.2,
  networkHealthPct: 88,
  activeIncidents: 2,
  throughputVehPerHr: 1820,
  congestionIndex: 0.62,
};

export async function fetchNetworkKpi(): Promise<NetworkKpi> {
  try {
    return await apiGet<NetworkKpi>("/traffic/kpi");
  } catch {
    return MOCK_KPI;
  }
}

// ── XGBoost risk score for a road segment ───────────────────────────────────
export interface RiskScoreResponse {
  roadId: string;
  riskScore: number;     // 0.0 – 1.0
  confidence: number;    // 0.0 – 1.0
  modelVersion: string;
  computedAt: string;
}

export async function fetchRiskScore(roadId: string): Promise<RiskScoreResponse> {
  try {
    return await apiPost<RiskScoreResponse>("/traffic/risk-score", { roadId });
  } catch {
    return {
      roadId,
      riskScore: 0.72,
      confidence: 0.948,
      modelVersion: "XGBoost v15",
      computedAt: new Date().toISOString(),
    };
  }
}
