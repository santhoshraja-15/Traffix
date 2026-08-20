import { GeoCoordinates } from "./common";

export type AccidentSeverity = "low" | "medium" | "high" | "critical";

export interface Accident {
  id: string;
  location: GeoCoordinates;
  roadId: string;
  roadName: string;
  severity: AccidentSeverity;
  status: "active" | "cleared";
  affectedRoadIds: string[];
  createdAt: string;
  description: string;
}

export interface AccidentSimRequest {
  roadId: string;
  location?: GeoCoordinates;
  severity: AccidentSeverity;
}
