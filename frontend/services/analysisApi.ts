import { apiGet } from "./api";

// ── Real AI insight, from app/services/analytics_service.py via
// GET /analysis/insights — derived from the live traffic_state_store,
// which the simulation tick loop now actually populates (see
// app/core/simulation_manager.py). Never fabricated: when no simulation
// is running the backend honestly returns a single "System Nominal"
// placeholder instead of inventing congestion.
export interface AiInsight {
  insight_id: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  recommendation: string;
  estimated_delay: number; // seconds
}

export interface AnalysisInsightsResponse {
  insights: AiInsight[];
}

export async function fetchAiInsights(): Promise<AiInsight[]> {
  const res = await apiGet<AnalysisInsightsResponse>("/analysis/insights");
  return res.insights;
}
