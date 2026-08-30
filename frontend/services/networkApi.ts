import { API_BASE_URL, API_ORIGIN } from "../lib/constants";
import { NetworkTopology } from "../lib/map";
import { LocationSuggestion } from "../types/route";

export interface HealthResponse {
  status: string;
  app?: string;
  version?: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_ORIGIN}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}

export async function fetchNetworkTopology(): Promise<NetworkTopology> {
  const response = await fetch(`${API_BASE_URL}/network/topology`);
  if (!response.ok) {
    throw new Error(`Topology fetch failed: ${response.status}`);
  }
  return (await response.json()) as NetworkTopology;
}

/** Real, searchable FROM/TO locations (real OSM street names in the loaded
 * network) — see app/api/network.py::get_network_locations. */
export async function fetchNetworkLocations(): Promise<LocationSuggestion[]> {
  const response = await fetch(`${API_BASE_URL}/network/locations`);
  if (!response.ok) {
    throw new Error(`Locations fetch failed: ${response.status}`);
  }
  const data = (await response.json()) as { locations: LocationSuggestion[] };
  return data.locations;
}
