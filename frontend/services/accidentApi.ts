import { apiRequest } from "./api";
import { Accident, AccidentSeverity } from "../types/accident";

export async function simulateAccident(
  roadId: string,
  severity: AccidentSeverity = "high"
): Promise<Accident> {
  try {
    return await apiRequest<Accident>("/accidents/create", {
      method: "POST",
      body: JSON.stringify({ roadId, severity }),
    });
  } catch (err) {
    console.warn("[TRAFFIX] Backend unavailable, simulating local accident trigger");
    return {
      id: `acc-${Date.now()}`,
      location: { lat: 13.0215, lng: 80.2210 }, // Anna Salai Sec 2
      roadId: roadId || "road_anna_2",
      roadName: "Anna Salai (Teynampet Junction)",
      severity,
      status: "active",
      affectedRoadIds: ["road_anna_2", "road_anna_3"],
      createdAt: new Date().toLocaleTimeString(),
      description: "Severe multi-vehicle collision blocking 2 lanes.",
    };
  }
}
