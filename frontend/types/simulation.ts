export type SimulationScenario = "low" | "medium" | "high" | "congested";

export interface SimulationControlState {
  isRunning: boolean;
  isPaused: boolean;
  scenario: SimulationScenario;
  speedMultiplier: number; // e.g. 1.0x, 2.0x, 5.0x
  currentStep: number;
  vehicleCount: number;
  loadedConfig: string;
}
