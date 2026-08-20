export type ConnectionStatus = "connected" | "reconnecting" | "offline";

export type ApplicationMode = "simulation" | "realtime";

export interface GeoCoordinates {
  lat: number;
  lng: number;
}

export interface IntelligenceMessage {
  id: string;
  timestamp: string;
  type: "info" | "success" | "warning" | "accident" | "emergency" | "routing" | "system";
  text: string;
  details?: string;
  urgent?: boolean;
}

export interface SystemHealth {
  backendConnected: boolean;
  simulationRunning: boolean;
  trafficStreamActive: boolean;
  lastTickTime: string;
  fps: number;
  vehicleCount: number;
}
