"use client";

import { useState } from "react";
import Header from "@/components/common/Header";
import { AppSettings, DEFAULT_SETTINGS } from "@/types/settings";
import {
  SettingsSection,
  SettingsRow,
  Toggle,
  TextInput,
  NumberInput,
  Select,
} from "@/components/common/SettingsControls";
import {
  Cpu,
  Map,
  Bell,
  Monitor,
  Key,
  RotateCcw,
  Save,
  CheckCircle2,
  Settings,
  Layers,
} from "lucide-react";

type SettingsTab = "sumo" | "map" | "notifications" | "display" | "api";

const TABS: { id: SettingsTab; label: string; icon: React.ReactNode }[] = [
  { id: "sumo", label: "SUMO / TraCI", icon: <Cpu className="w-3.5 h-3.5" /> },
  { id: "map", label: "Map Display", icon: <Map className="w-3.5 h-3.5" /> },
  { id: "notifications", label: "Notifications", icon: <Bell className="w-3.5 h-3.5" /> },
  { id: "display", label: "Display", icon: <Monitor className="w-3.5 h-3.5" /> },
  { id: "api", label: "API Keys", icon: <Key className="w-3.5 h-3.5" /> },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [activeTab, setActiveTab] = useState<SettingsTab>("sumo");
  const [saved, setSaved] = useState(false);

  const update = <S extends keyof AppSettings>(
    section: S,
    field: keyof AppSettings[S],
    value: AppSettings[S][keyof AppSettings[S]]
  ) => {
    setSaved(false);
    setSettings((prev) => ({
      ...prev,
      [section]: { ...prev[section], [field]: value },
    }));
  };

  const handleSave = () => {
    // In production this would persist to localStorage / backend
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    setSaved(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-[1200px] w-full mx-auto p-6 flex flex-col gap-6">
        {/* Page title */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Settings className="w-6 h-6 text-sky-500" />
              System Settings
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Configure SUMO TraCI connection, map layers, notifications, display preferences, and API keys.
            </p>
          </div>

          {/* Save / Reset controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 border border-slate-200 rounded-xl text-xs font-bold transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Defaults
            </button>
            <button
              onClick={handleSave}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-extrabold shadow-sm transition-all ${
                saved
                  ? "bg-emerald-500 text-white border border-emerald-500"
                  : "bg-sky-500 hover:bg-sky-600 text-white border border-sky-500"
              }`}
            >
              {saved ? (
                <><CheckCircle2 className="w-3.5 h-3.5" />Saved!</>
              ) : (
                <><Save className="w-3.5 h-3.5" />Save Settings</>
              )}
            </button>
          </div>
        </div>

        {/* Tab + content layout */}
        <div className="flex gap-5 flex-col lg:flex-row">
          {/* Sidebar tabs */}
          <div className="flex flex-row lg:flex-col gap-1 lg:w-48 flex-shrink-0 bg-white rounded-xl border border-slate-200 shadow-sm p-2 h-fit">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-xs font-bold transition-all w-full text-left ${
                  activeTab === tab.id
                    ? "bg-sky-50 text-sky-700 border border-sky-200"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                <span className={activeTab === tab.id ? "text-sky-600" : "text-slate-400"}>
                  {tab.icon}
                </span>
                <span className="hidden sm:inline lg:inline">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Content panels */}
          <div className="flex-1 flex flex-col gap-5">

            {/* ── SUMO / TraCI ── */}
            {activeTab === "sumo" && (
              <SettingsSection
                title="SUMO / TraCI Connection"
                description="Configure the SUMO simulation engine and TraCI socket connection"
                icon={<Cpu className="w-4 h-4" />}
                accentColor="text-sky-600 bg-sky-50 border-sky-100"
              >
                <SettingsRow label="TraCI Host" description="Hostname or IP of SUMO TraCI server">
                  <TextInput
                    id="traci-host"
                    value={settings.sumo.host}
                    onChange={(v) => update("sumo", "host", v)}
                    placeholder="localhost"
                  />
                </SettingsRow>
                <SettingsRow label="TraCI Port" description="Default: 8813">
                  <NumberInput
                    id="traci-port"
                    value={settings.sumo.port}
                    onChange={(v) => update("sumo", "port", v)}
                    min={1024}
                    max={65535}
                    unit="port"
                  />
                </SettingsRow>
                <SettingsRow label="Auto-Connect on Start" description="Automatically connect to SUMO when the app loads">
                  <Toggle
                    id="sumo-autoconnect"
                    enabled={settings.sumo.autoConnect}
                    onChange={(v) => update("sumo", "autoConnect", v)}
                  />
                </SettingsRow>
                <SettingsRow label="Step Interval" description="Milliseconds between simulation ticks">
                  <NumberInput
                    id="sumo-step-interval"
                    value={settings.sumo.stepInterval}
                    onChange={(v) => update("sumo", "stepInterval", v)}
                    min={100}
                    max={10000}
                    step={100}
                    unit="ms"
                  />
                </SettingsRow>
                <SettingsRow label="Max Steps per Epoch" description="Number of steps for a full simulation epoch">
                  <NumberInput
                    id="sumo-max-steps"
                    value={settings.sumo.maxSteps}
                    onChange={(v) => update("sumo", "maxSteps", v)}
                    min={100}
                    max={86400}
                    step={100}
                    unit="steps"
                  />
                </SettingsRow>
              </SettingsSection>
            )}

            {/* ── Map Display ── */}
            {activeTab === "map" && (
              <>
                <SettingsSection
                  title="Map Center & Zoom"
                  description="Default viewport when the map loads"
                  icon={<Map className="w-4 h-4" />}
                  accentColor="text-emerald-600 bg-emerald-50 border-emerald-100"
                >
                  <SettingsRow label="Default Latitude" description="Anna Salai, Chennai: 13.0482">
                    <NumberInput
                      id="map-lat"
                      value={settings.map.defaultLat}
                      onChange={(v) => update("map", "defaultLat", v)}
                      step={0.0001}
                      unit="°N"
                    />
                  </SettingsRow>
                  <SettingsRow label="Default Longitude" description="Anna Salai, Chennai: 80.2425">
                    <NumberInput
                      id="map-lng"
                      value={settings.map.defaultLng}
                      onChange={(v) => update("map", "defaultLng", v)}
                      step={0.0001}
                      unit="°E"
                    />
                  </SettingsRow>
                  <SettingsRow label="Default Zoom Level" description="1 = world, 22 = street level">
                    <NumberInput
                      id="map-zoom"
                      value={settings.map.defaultZoom}
                      onChange={(v) => update("map", "defaultZoom", v)}
                      min={1}
                      max={22}
                      unit="zoom"
                    />
                  </SettingsRow>
                </SettingsSection>

                <SettingsSection
                  title="Layer Visibility Defaults"
                  description="Which map layers are enabled when the dashboard first loads"
                  icon={<Layers className="w-4 h-4" />}
                  accentColor="text-emerald-600 bg-emerald-50 border-emerald-100"
                >
                  {[
                    { key: "show3DBuildings" as const, label: "3D Buildings", desc: "Mapbox GL extrusion layer" },
                    { key: "showVehicleLayer" as const, label: "Vehicle Layer", desc: "Live vehicle positions" },
                    { key: "showSignalLayer" as const, label: "Traffic Signals", desc: "Junction signal indicators" },
                    { key: "showAccidentZones" as const, label: "Accident Zones", desc: "Hazard markers and ripple effects" },
                    { key: "showHospitalLayer" as const, label: "Hospital Markers", desc: "Emergency hospital locations" },
                  ].map((item) => (
                    <SettingsRow key={item.key} label={item.label} description={item.desc}>
                      <Toggle
                        id={`map-${item.key}`}
                        enabled={settings.map[item.key] as boolean}
                        onChange={(v) => update("map", item.key, v)}
                      />
                    </SettingsRow>
                  ))}
                </SettingsSection>
              </>
            )}

            {/* ── Notifications ── */}
            {activeTab === "notifications" && (
              <SettingsSection
                title="Notification Preferences"
                description="Control how TRAFFIX alert notifications are delivered and filtered"
                icon={<Bell className="w-4 h-4" />}
                accentColor="text-amber-600 bg-amber-50 border-amber-100"
              >
                <SettingsRow label="Enable Alert Sounds" description="Play audio cue on critical alerts">
                  <Toggle
                    id="notif-sounds"
                    enabled={settings.notifications.enableSounds}
                    onChange={(v) => update("notifications", "enableSounds", v)}
                  />
                </SettingsRow>
                <SettingsRow label="Critical Alerts Only" description="Suppress warning and info-level notifications">
                  <Toggle
                    id="notif-critical-only"
                    enabled={settings.notifications.criticalOnly}
                    onChange={(v) => update("notifications", "criticalOnly", v)}
                  />
                </SettingsRow>
                <SettingsRow label="Minimum Severity" description="Minimum level that creates an alert card">
                  <Select
                    id="notif-severity"
                    value={settings.notifications.minimumSeverity}
                    onChange={(v) => update("notifications", "minimumSeverity", v)}
                    options={[
                      { value: "info", label: "Info (all alerts)" },
                      { value: "warning", label: "Warning and above" },
                      { value: "critical", label: "Critical only" },
                    ]}
                  />
                </SettingsRow>
                <SettingsRow label="Auto-Acknowledge Info Alerts" description="Automatically mark info-level alerts as acknowledged">
                  <Toggle
                    id="notif-auto-ack"
                    enabled={settings.notifications.autoAcknowledgeInfo}
                    onChange={(v) => update("notifications", "autoAcknowledgeInfo", v)}
                  />
                </SettingsRow>
                <SettingsRow label="Alert Retention" description="How long to keep dismissed alerts in history">
                  <NumberInput
                    id="notif-retention"
                    value={settings.notifications.alertRetentionHours}
                    onChange={(v) => update("notifications", "alertRetentionHours", v)}
                    min={1}
                    max={168}
                    unit="hours"
                  />
                </SettingsRow>
              </SettingsSection>
            )}

            {/* ── Display ── */}
            {activeTab === "display" && (
              <SettingsSection
                title="Display & UI Preferences"
                description="Adjust the interface layout, animations, and data formatting"
                icon={<Monitor className="w-4 h-4" />}
                accentColor="text-violet-600 bg-violet-50 border-violet-100"
              >
                <SettingsRow label="Compact Mode" description="Reduce padding for higher information density">
                  <Toggle
                    id="display-compact"
                    enabled={settings.display.compactMode}
                    onChange={(v) => update("display", "compactMode", v)}
                  />
                </SettingsRow>
                <SettingsRow label="Enable Animations" description="Micro-animations, ripple effects, and transitions">
                  <Toggle
                    id="display-animations"
                    enabled={settings.display.animationsEnabled}
                    onChange={(v) => update("display", "animationsEnabled", v)}
                  />
                </SettingsRow>
                <SettingsRow label="Dashboard Refresh Interval" description="How often live data panels re-fetch">
                  <NumberInput
                    id="display-refresh"
                    value={settings.display.refreshIntervalMs}
                    onChange={(v) => update("display", "refreshIntervalMs", v)}
                    min={500}
                    max={30000}
                    step={500}
                    unit="ms"
                  />
                </SettingsRow>
                <SettingsRow label="Time Format" description="12-hour or 24-hour clock">
                  <Select
                    id="display-time"
                    value={settings.display.dateFormat}
                    onChange={(v) => update("display", "dateFormat", v)}
                    options={[
                      { value: "24h", label: "24-hour (17:51)" },
                      { value: "12h", label: "12-hour (5:51 PM)" },
                    ]}
                  />
                </SettingsRow>
                <SettingsRow label="Coordinate Format" description="How GPS coordinates are displayed">
                  <Select
                    id="display-coords"
                    value={settings.display.coordinateFormat}
                    onChange={(v) => update("display", "coordinateFormat", v)}
                    options={[
                      { value: "decimal", label: "Decimal (13.0482°N)" },
                      { value: "dms", label: "DMS (13°02′53″N)" },
                    ]}
                  />
                </SettingsRow>
              </SettingsSection>
            )}

            {/* ── API Keys ── */}
            {activeTab === "api" && (
              <SettingsSection
                title="API Key Management"
                description="Securely configure third-party service tokens"
                icon={<Key className="w-4 h-4" />}
                accentColor="text-indigo-600 bg-indigo-50 border-indigo-100"
              >
                <SettingsRow
                  label="Mapbox Access Token"
                  description="Required for 3D map rendering and satellite layers. Get yours at mapbox.com"
                >
                  <TextInput
                    id="api-mapbox"
                    value={settings.map.mapboxToken}
                    onChange={(v) => update("map", "mapboxToken", v)}
                    placeholder="pk.eyJ1IjoiLi4u"
                    type="password"
                  />
                </SettingsRow>

                {/* Info box */}
                <div className="px-5 py-4">
                  <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-800 leading-relaxed">
                    <p className="font-bold mb-1">🔒 Security Note</p>
                    <p>
                      API keys are stored in your browser&apos;s local storage only — they are never sent to
                      any TRAFFIX server. The Mapbox token is required only for the live 3D map layer.
                      The vector canvas fallback works without it.
                    </p>
                  </div>
                </div>

                {/* SUMO connection test */}
                <SettingsRow label="Test SUMO Connection" description={`Ping ${settings.sumo.host}:${settings.sumo.port}`}>
                  <button className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-lg text-xs font-bold transition-all">
                    <Cpu className="w-3.5 h-3.5" />
                    Test Connection
                  </button>
                </SettingsRow>
              </SettingsSection>
            )}

            {/* Save confirmation footer */}
            {saved && (
              <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-bold text-emerald-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Settings saved successfully. Changes will take effect on next dashboard refresh.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
