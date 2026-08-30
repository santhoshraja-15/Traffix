import { apiPost } from "./api";
import { Accident, AccidentSeverity } from "../types/accident";

// ── Real backend contract (app/models/accident_models.py) ────────────────────
interface ApiAccidentReport {
  accident_id: string;
  edge_id: string;
  location: { lat: number; lng: number } | null;
  severity: string;
  lanes_blocked: number;
  road_name: string;
  status: string;
}

function toAccident(report: ApiAccidentReport): Accident {
  return {
    id: report.accident_id,
    // location is only ever null if the reported edge somehow isn't in the
    // graph (see AccidentService.report_accident) — surfacing (0, 0) would
    // silently look like a real place, so this is deliberately Anna Nagar's
    // own center as an honest "location unknown" fallback, not a guess at
    // where the accident actually is.
    location: report.location ?? { lat: 13.085, lng: 80.2101 },
    roadId: report.edge_id,
    roadName: report.road_name || report.edge_id,
    severity: report.severity as AccidentSeverity,
    status: report.status === "resolved" ? "cleared" : "active",
    affectedRoadIds: [report.edge_id],
    createdAt: new Date().toLocaleTimeString(),
    description: `${report.severity} severity incident, ${report.lanes_blocked} lane(s) blocked.`,
  };
}

/**
 * Report a real accident on *edgeId* — the backend applies a genuine
 * capacity reduction to that edge (see app/services/accident_service.py),
 * which the live simulation reflects as real, elevated congestion/risk on
 * the next tick. Throws on failure — never silently returns a fabricated
 * accident (see FRONTEND_AUDIT.md §2.4 for what this replaced).
 */
export async function simulateAccident(
  edgeId: string,
  severity: AccidentSeverity = "high",
  lanesBlocked: number = 1
): Promise<Accident> {
  const result = await apiPost<{ accident: ApiAccidentReport }>("/accidents", {
    edge_id: edgeId,
    severity,
    lanes_blocked: lanesBlocked,
  });
  return toAccident(result.accident);
}

/** Resolve a real accident — restores the affected edge's real capacity. */
export async function resolveAccident(accidentId: string): Promise<boolean> {
  const result = await apiPost<{ accident_id: string; resolved: boolean }>(
    `/accidents/${accidentId}/resolve`,
    {}
  );
  return result.resolved;
}
