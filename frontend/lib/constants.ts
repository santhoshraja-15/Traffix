export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
export const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAP_TOKEN || "";
export const API_TIMEOUT_MS = 8000;
export const API_MAX_RETRIES = 2;

// Default center: Chennai Anna Salai Corridor
export const DEFAULT_MAP_CENTER = {
  lat: 13.0482,
  lng: 80.2425,
};

export const DEFAULT_MAP_ZOOM = 14;
export const DEFAULT_MAP_BEARING = 0;
export const DEFAULT_MAP_PITCH = 45;

export const CONGESTION_COLORS = {
  low: "#22c55e",       // Green
  moderate: "#eab308",  // Yellow
  high: "#f97316",      // Orange
  congested: "#ef4444", // Red
  emergency: "#dc2626", // Dark Red
};
