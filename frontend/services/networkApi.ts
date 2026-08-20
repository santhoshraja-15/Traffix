import { API_BASE_URL, API_ORIGIN } from "../lib/constants";
import { NetworkTopology } from "../lib/map";

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
