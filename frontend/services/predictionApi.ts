import { apiPost, apiGet } from "./api";

// ── Prediction horizon type ──────────────────────────────────────────────────
export type PredictionHorizon = "15min" | "30min" | "60min" | "120min";

// ── Forecast point ───────────────────────────────────────────────────────────
export interface ForecastPoint {
  timeLabel: string;
  historicalDensity: number;
  currentDensity: number;
  predictedDensity: number;
  riskScore: number;
  confidence: number;
}

// ── Full prediction response (from trafficx_v15_live.py) ─────────────────────
export interface PredictionResponse {
  roadId: string;
  horizon: PredictionHorizon;
  modelVersion: string;
  generatedAt: string;
  overallConfidence: number;
  overallRisk: number;
  peakDensityTime: string;
  points: ForecastPoint[];
}

// ── Mock data generator ──────────────────────────────────────────────────────
function generateMockForecast(
  roadId: string,
  horizon: PredictionHorizon
): PredictionResponse {
  const basePoints = [
    { t: "-60m", h: 62, c: 71, p: 71 },
    { t: "-45m", h: 64, c: 74, p: 74 },
    { t: "-30m", h: 68, c: 79, p: 79 },
    { t: "-15m", h: 72, c: 83, p: 83 },
    { t: "NOW",  h: 75, c: 86, p: 86 },
    { t: "+15m", h: 76, c: 86, p: 91 },
    { t: "+30m", h: 74, c: 86, p: 88 },
    { t: "+60m", h: 69, c: 86, p: 78 },
    { t: "+2hr", h: 58, c: 86, p: 61 },
  ];

  const cutoffIndex =
    horizon === "15min" ? 6
    : horizon === "30min" ? 7
    : horizon === "60min" ? 8
    : 9;

  return {
    roadId,
    horizon,
    modelVersion: "XGBoost v15",
    generatedAt: new Date().toISOString(),
    overallConfidence: 0.948,
    overallRisk: 0.72,
    peakDensityTime: "17:00",
    points: basePoints.slice(0, cutoffIndex).map((p) => ({
      timeLabel: p.t,
      historicalDensity: p.h,
      currentDensity: p.c,
      predictedDensity: p.p,
      riskScore: p.p / 100,
      confidence: 0.948,
    })),
  };
}

// ── Fetch forecast from trafficx_v15_live.py ─────────────────────────────────
export async function fetchTrafficForecast(
  roadId: string,
  horizon: PredictionHorizon = "30min"
): Promise<PredictionResponse> {
  try {
    return await apiPost<PredictionResponse>("/prediction/forecast", {
      roadId,
      horizon,
      modelVersion: "v15",
    });
  } catch {
    console.warn("[TRAFFIX] /prediction/forecast unavailable → mock");
    return generateMockForecast(roadId, horizon);
  }
}

// ── Batch forecast for multiple roads ────────────────────────────────────────
export async function fetchBatchForecast(
  roadIds: string[],
  horizon: PredictionHorizon = "30min"
): Promise<PredictionResponse[]> {
  try {
    return await apiPost<PredictionResponse[]>("/prediction/batch-forecast", {
      roadIds,
      horizon,
    });
  } catch {
    return roadIds.map((id) => generateMockForecast(id, horizon));
  }
}

// ── Incident probability score ────────────────────────────────────────────────
export interface IncidentProbability {
  roadId: string;
  probability: number;
  severity: "low" | "medium" | "high";
  contributingFactors: string[];
  modelVersion: string;
}

export async function fetchIncidentProbability(
  roadId: string
): Promise<IncidentProbability> {
  try {
    return await apiGet<IncidentProbability>(
      `/prediction/incident-probability/${roadId}`
    );
  } catch {
    return {
      roadId,
      probability: 0.34,
      severity: "medium",
      contributingFactors: [
        "High vehicle density (73%)",
        "Historical peak hours pattern",
        "Weather: Clear (low risk)",
      ],
      modelVersion: "XGBoost v15",
    };
  }
}
