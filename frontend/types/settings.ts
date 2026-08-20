export interface SumoSettings {
  host: string;
  port: number;
  autoConnect: boolean;
  stepInterval: number;
  maxSteps: number;
}

export interface MapSettings {
  defaultLat: number;
  defaultLng: number;
  defaultZoom: number;
  show3DBuildings: boolean;
  showVehicleLayer: boolean;
  showSignalLayer: boolean;
  showAccidentZones: boolean;
  showHospitalLayer: boolean;
  mapboxToken: string;
}

export interface NotificationSettings {
  enableSounds: boolean;
  criticalOnly: boolean;
  minimumSeverity: "critical" | "warning" | "info";
  autoAcknowledgeInfo: boolean;
  alertRetentionHours: number;
}

export interface DisplaySettings {
  compactMode: boolean;
  animationsEnabled: boolean;
  refreshIntervalMs: number;
  dateFormat: "24h" | "12h";
  coordinateFormat: "decimal" | "dms";
}

export interface AppSettings {
  sumo: SumoSettings;
  map: MapSettings;
  notifications: NotificationSettings;
  display: DisplaySettings;
}

export const DEFAULT_SETTINGS: AppSettings = {
  sumo: {
    host: "localhost",
    port: 8813,
    autoConnect: true,
    stepInterval: 1000,
    maxSteps: 3600,
  },
  map: {
    defaultLat: 13.0482,
    defaultLng: 80.2425,
    defaultZoom: 14,
    show3DBuildings: true,
    showVehicleLayer: true,
    showSignalLayer: true,
    showAccidentZones: true,
    showHospitalLayer: true,
    mapboxToken: "",
  },
  notifications: {
    enableSounds: false,
    criticalOnly: false,
    minimumSeverity: "info",
    autoAcknowledgeInfo: false,
    alertRetentionHours: 24,
  },
  display: {
    compactMode: false,
    animationsEnabled: true,
    refreshIntervalMs: 2000,
    dateFormat: "24h",
    coordinateFormat: "decimal",
  },
};
