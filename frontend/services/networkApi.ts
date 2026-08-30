import { API_ORIGIN, API_TIMEOUT_MS } from "../lib/constants";
import { NetworkTopology } from "../lib/map";
import { LocationSuggestion } from "../types/route";
import { apiGet, fetchWithTimeout } from "./api";

export interface HealthResponse {
  status: string;
  app?: string;
  version?: string;
}

/**
 * Real backend health probe — GET /health (root-level, not under /api; see
 * app/main.py). Timeout-protected directly (fetchWithTimeout) rather than
 * apiGet()/apiRequest(), which always prepends API_BASE_URL (the /api
 * prefix) and would 404 against this root-level route.
 *
 * Previously a raw fetch() with no timeout at all — if the configured
 * backend port is unreachable in a way that never produces a response
 * (TCP connection accepted but nothing ever replies, e.g. an unrelated
 * process squatting the port), this call would hang indefinitely instead
 * of failing into a real, honest error the UI can show.
 */
export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetchWithTimeout(`${API_ORIGIN}/health`, {}, API_TIMEOUT_MS);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}

/**
 * Real Anna Nagar network topology — GET /api/network/topology (see
 * app/api/network.py -> RoadNetworkGraph.to_geojson()). Now routed through
 * apiGet(), which is timeout- and retry-protected (see services/api.ts) —
 * previously a raw, un-timeout-protected fetch() that could hang forever
 * against an unreachable backend, leaving TrafficMap.tsx's "Loading Anna
 * Nagar network…" state stuck permanently instead of surfacing its own
 * already-built honest "network data unavailable" error state.
 */
export async function fetchNetworkTopology(): Promise<NetworkTopology> {
  return apiGet<NetworkTopology>("/network/topology");
}

/** Real, searchable FROM/TO locations (real OSM street names in the loaded
 * network) — see app/api/network.py::get_network_locations. Same
 * timeout/retry fix as fetchNetworkTopology above. */
export async function fetchNetworkLocations(): Promise<LocationSuggestion[]> {
  const data = await apiGet<{ locations: LocationSuggestion[] }>("/network/locations");
  return data.locations;
}
