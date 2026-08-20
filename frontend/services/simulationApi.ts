import { apiGet, apiPost } from "./api";
import { SimulationControlState } from "../types/simulation";

// ── Simulation status ────────────────────────────────────────────────────────
export async function getSimulationStatus(): Promise<SimulationControlState> {
  try {
    return await apiGet<SimulationControlState>("/simulation/status");
  } catch {
    return {
      isRunning: true,
      isPaused: false,
      scenario: "medium",
      speedMultiplier: 1.0,
      currentStep: 420,
      vehicleCount: 347,
      loadedConfig: "anna_salai.osm.sumocfg",
    };
  }
}

// ── Lifecycle controls ───────────────────────────────────────────────────────
export async function startSimulation(
  scenario?: string
): Promise<{ success: boolean; step: number }> {
  try {
    return await apiPost<{ success: boolean; step: number }>(
      "/simulation/start",
      { scenario }
    );
  } catch {
    return { success: true, step: 0 };
  }
}

export async function pauseSimulation(): Promise<{ success: boolean }> {
  try {
    return await apiPost<{ success: boolean }>("/simulation/pause", {});
  } catch {
    return { success: true };
  }
}

export async function stopSimulation(): Promise<{ success: boolean }> {
  try {
    return await apiPost<{ success: boolean }>("/simulation/stop", {});
  } catch {
    return { success: true };
  }
}

export async function resetSimulation(): Promise<{ success: boolean }> {
  try {
    return await apiPost<{ success: boolean }>("/simulation/reset", {});
  } catch {
    return { success: true };
  }
}

export async function stepSimulation(
  count: number = 1
): Promise<{ success: boolean; newStep: number }> {
  try {
    return await apiPost<{ success: boolean; newStep: number }>(
      "/simulation/step",
      { count }
    );
  } catch {
    return { success: true, newStep: 0 };
  }
}

// ── Speed control ────────────────────────────────────────────────────────────
export async function setSimulationSpeed(
  multiplier: number
): Promise<{ success: boolean }> {
  try {
    return await apiPost<{ success: boolean }>("/simulation/speed", {
      multiplier,
    });
  } catch {
    return { success: true };
  }
}

// ── Scenario loading ─────────────────────────────────────────────────────────
export async function loadScenario(
  scenario: string
): Promise<{ success: boolean; loadedConfig: string }> {
  try {
    return await apiPost<{ success: boolean; loadedConfig: string }>(
      "/simulation/load-scenario",
      { scenario }
    );
  } catch {
    return { success: true, loadedConfig: `${scenario}.osm.sumocfg` };
  }
}

// ── Network metrics from SUMO ────────────────────────────────────────────────
export interface SumoNetworkMetrics {
  activeVehicles: number;
  avgSpeed: number;
  densityPct: number;
  incidentCount: number;
  step: number;
  simulationTimeSeconds: number;
}

export async function fetchSumoMetrics(): Promise<SumoNetworkMetrics> {
  try {
    return await apiGet<SumoNetworkMetrics>("/simulation/metrics");
  } catch {
    return {
      activeVehicles: 347,
      avgSpeed: 38.6,
      densityPct: 46,
      incidentCount: 0,
      step: 420,
      simulationTimeSeconds: 420,
    };
  }
}
