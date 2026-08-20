import { GeoCoordinates } from "./common";

export type CongestionLevel = "low" | "moderate" | "high" | "congested";

export interface Vehicle {
  id: string;
  position: GeoCoordinates;
  speedKmh: number;
  roadId: string;
  type?: "passenger" | "emergency" | "bus" | "truck";
  waitingTimeSec: number;
  headingAngle?: number;
}

export interface RoadSegment {
  id: string;
  name: string;
  coordinates: GeoCoordinates[];
  congestion: CongestionLevel;
  averageSpeedKmh: number;
  vehicleCount: number;
  riskScore: number; // 0.0 to 1.0
  isClosed?: boolean;
}

export interface TrafficSignal {
  id: string;
  name: string;
  location: GeoCoordinates;
  state: "red" | "yellow" | "green";
  cycleTimeSec: number;
  remainingPhaseSec: number;
}

export interface TrafficStateSnapshot {
  timestamp: string;
  step: number;
  totalVehicles: number;
  averageSpeedKmh: number;
  stoppedVehicles: number;
  averageWaitingTimeSec: number;
  congestionLevel: CongestionLevel;
  roads: Record<string, RoadSegment>;
  vehicles: Vehicle[];
  signals: TrafficSignal[];
}
