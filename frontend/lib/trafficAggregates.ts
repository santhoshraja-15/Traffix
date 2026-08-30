import type { StreamEdge } from "../hooks/useWebSocket";

/**
 * Network-wide traffic KPIs + congestion distribution, computed entirely
 * from the real per-edge WebSocket snapshot — no REST endpoint, no mock
 * fallback. Recomputed on every real tick (see hooks/useLiveData.ts), so
 * it updates exactly as often as the backend actually pushes new data.
 *
 * Two distinct real backend signals are kept deliberately separate rather
 * than conflated under one label (per DESIGN_SYSTEM.md §3):
 *  - `congestion` / `congestion_score` — the routing service's own traffic
 *    density estimate. Drives networkHealthPct/congestionIndex/the
 *    Free-Flow…Bottleneck breakdown here.
 *  - `risk_score` — the V15/V16 XGBoost model. Drives per-edge road
 *    coloring on the map and route risk (see TrafficMap.tsx / navigationApi.ts)
 *    — not recomputed here.
 */
export interface TrafficAggregates {
  activeVehicles: number;
  stoppedVehicles: number;
  avgSpeedKmh: number;
  networkHealthPct: number; // 0-100, derived from avg congestion_score
  congestionIndex: number; // 0.0-1.0, avg congestion_score
  lowCount: number; // free_flow + light
  moderateCount: number;
  highCount: number; // heavy
  congestedCount: number; // severe
  // The backend doesn't broadcast incident/accident state yet (see
  // FRONTEND_AUDIT.md §1.2 — that's Phase 7 territory), so this always
  // computes to 0 here; page.tsx's (still-mock) accident simulation
  // increments it locally via setKpi in the meantime.
  activeIncidents: number;
}

const EMPTY: TrafficAggregates = {
  activeVehicles: 0,
  stoppedVehicles: 0,
  avgSpeedKmh: 0,
  networkHealthPct: 100,
  congestionIndex: 0,
  lowCount: 0,
  moderateCount: 0,
  highCount: 0,
  congestedCount: 0,
  activeIncidents: 0,
};

export function computeTrafficAggregates(edges: StreamEdge[]): TrafficAggregates {
  if (edges.length === 0) return EMPTY;

  let activeVehicles = 0;
  let stoppedVehicles = 0;
  let speedWeightedSum = 0;
  let congestionSum = 0;
  let lowCount = 0;
  let moderateCount = 0;
  let highCount = 0;
  let congestedCount = 0;

  for (const edge of edges) {
    activeVehicles += edge.vehicle_count;
    stoppedVehicles += edge.stopped_vehicles;
    speedWeightedSum += edge.speed * edge.vehicle_count;
    congestionSum += edge.congestion_score;

    switch (edge.congestion) {
      case "free_flow":
      case "light":
        lowCount++;
        break;
      case "moderate":
        moderateCount++;
        break;
      case "heavy":
        highCount++;
        break;
      default: // "severe"
        congestedCount++;
    }
  }

  const avgCongestion = congestionSum / edges.length;
  const avgSpeedKmh = activeVehicles > 0 ? speedWeightedSum / activeVehicles : 0;

  return {
    activeVehicles,
    stoppedVehicles,
    avgSpeedKmh,
    networkHealthPct: Math.round(Math.max(0, Math.min(1, 1 - avgCongestion)) * 100),
    congestionIndex: avgCongestion,
    lowCount,
    moderateCount,
    highCount,
    congestedCount,
    activeIncidents: 0,
  };
}
