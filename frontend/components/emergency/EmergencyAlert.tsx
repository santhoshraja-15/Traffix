"use client";

import { AlertTriangle, ShieldAlert, X, Clock } from "lucide-react";
import { useEffect, useState } from "react";

export interface EmergencyAlertItem {
  id: string;
  level: "critical" | "warning" | "info";
  message: string;
  source: string;
  timestamp: string;
}

const LEVEL_STYLES: Record<EmergencyAlertItem["level"], string> = {
  critical: "bg-red-50 border-red-200 text-red-800",
  warning: "bg-amber-50 border-amber-200 text-amber-800",
  info: "bg-sky-50 border-sky-200 text-sky-800",
};

const LEVEL_ICONS: Record<EmergencyAlertItem["level"], React.ReactNode> = {
  critical: <ShieldAlert className="w-3.5 h-3.5 text-red-600" />,
  warning: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
  info: <Clock className="w-3.5 h-3.5 text-sky-600" />,
};

const INITIAL_ALERTS: EmergencyAlertItem[] = [
  {
    id: "a1",
    level: "critical",
    message: "High-severity accident detected at Anna Salai (Teynampet). Lane 2 blocked.",
    source: "Optical Camera CAM-02",
    timestamp: "17:51:00",
  },
  {
    id: "a2",
    level: "warning",
    message: "Traffic queue forming on Mount Flyover — spillback 400 m detected.",
    source: "Radar Sensor RAD-01",
    timestamp: "17:51:04",
  },
  {
    id: "a3",
    level: "info",
    message: "XGBoost v15 risk score elevated: 0.91 on corridor Node 14→18.",
    source: "AI Risk Engine",
    timestamp: "17:51:07",
  },
];

interface EmergencyAlertProps {
  incidentActive: boolean;
  dispatchActive: boolean;
}

export default function EmergencyAlert({ incidentActive, dispatchActive }: EmergencyAlertProps) {
  const [alerts, setAlerts] = useState<EmergencyAlertItem[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  // Simulate streaming alerts when incident fires
  useEffect(() => {
    if (!incidentActive) return;
    let idx = 0;
    const timer = setInterval(() => {
      if (idx < INITIAL_ALERTS.length) {
        setAlerts((prev) => [...prev, INITIAL_ALERTS[idx]]);
        idx++;
      } else {
        clearInterval(timer);
      }
    }, 800);
    return () => clearInterval(timer);
  }, [incidentActive]);

  // Add dispatch alert
  useEffect(() => {
    if (!dispatchActive) return;
    setAlerts((prev) => [
      ...prev,
      {
        id: "a4",
        level: "info",
        message: "Ambulance A-07 dispatched. Emergency green corridor activated. ETA 3 min.",
        source: "Dispatch Command",
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
      },
    ]);
  }, [dispatchActive]);

  const visible = alerts.filter((a) => !dismissed.has(a.id));

  if (visible.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <h3 className="text-sm font-extrabold text-slate-900">Emergency Alert Stream</h3>
        </div>
        <span className="text-xs font-bold text-slate-500">{visible.length} active</span>
      </div>

      <div className="p-4 flex flex-col gap-2 max-h-72 overflow-y-auto">
        {visible.map((alert) => (
          <div
            key={alert.id}
            className={`flex items-start gap-3 p-3 rounded-xl border text-xs transition-all ${LEVEL_STYLES[alert.level]}`}
          >
            <div className="mt-0.5 flex-shrink-0">{LEVEL_ICONS[alert.level]}</div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold leading-snug">{alert.message}</p>
              <div className="mt-1 flex items-center gap-2 text-xs opacity-70">
                <span>{alert.source}</span>
                <span>·</span>
                <span>{alert.timestamp}</span>
              </div>
            </div>
            <button
              onClick={() => setDismissed((prev) => new Set([...prev, alert.id]))}
              className="ml-1 flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
