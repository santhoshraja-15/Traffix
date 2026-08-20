"use client";

import { useState, useEffect, useRef } from "react";
import { Camera, Radio, CheckCircle2, AlertTriangle, RefreshCw, Activity } from "lucide-react";
import { fetchRoadDensities, RoadDensity } from "@/services/trafficApi";
import { useTraffixContext } from "@/context/TraffixContext";

export interface IotDevice {
  id: string;
  name: string;
  type: "camera" | "radar_sensor" | "loop_detector";
  location: string;
  status: "active" | "maintenance" | "offline";
  vehicleCount: number;
  avgSpeedKmh: number;
  occupancyPct: number;
  healthPct: number;
  lastUpdatedAt: number; // epoch ms
}

const BASE_DEVICES: IotDevice[] = [
  { id: "CAM-01", name: "Anna Salai Optical Cam #1", type: "camera", location: "Teynampet Junction", status: "active", vehicleCount: 42, avgSpeedKmh: 38.5, occupancyPct: 24, healthPct: 98, lastUpdatedAt: 0 },
  { id: "CAM-02", name: "Mount Flyover AI Cam #2", type: "camera", location: "Saidapet North", status: "active", vehicleCount: 28, avgSpeedKmh: 42.0, occupancyPct: 18, healthPct: 100, lastUpdatedAt: 0 },
  { id: "SENS-04", name: "Guindy Loop Detector #4", type: "loop_detector", location: "Guindy West", status: "active", vehicleCount: 56, avgSpeedKmh: 28.4, occupancyPct: 62, healthPct: 92, lastUpdatedAt: 0 },
  { id: "RAD-01", name: "Poonamallee Radar #1", type: "radar_sensor", location: "Aminjikarai Crossing", status: "maintenance", vehicleCount: 0, avgSpeedKmh: 0, occupancyPct: 0, healthPct: 45, lastUpdatedAt: 0 },
];

// Map road IDs to device indices
const ROAD_TO_DEVICE: Record<string, number> = {
  road_anna_2: 0,
  road_mount_1: 1,
  road_ring_2: 2,
};

function freshness(lastUpdatedAt: number): string {
  if (!lastUpdatedAt) return "—";
  const secs = Math.floor((Date.now() - lastUpdatedAt) / 1000);
  if (secs < 2) return "Just now";
  if (secs < 60) return `${secs} sec ago`;
  return `${Math.floor(secs / 60)} min ago`;
}

export default function IotMonitoringPanel() {
  const { wsStep } = useTraffixContext();
  const [devices, setDevices] = useState<IotDevice[]>(
    BASE_DEVICES.map((d) => ({ ...d, lastUpdatedAt: Date.now() }))
  );
  const [loading, setLoading] = useState(false);
  const [tick, setTick] = useState(0);

  // Tick freshness display every second
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const refresh = async () => {
    setLoading(true);
    try {
      const densities: RoadDensity[] = await fetchRoadDensities();
      setDevices((prev) => {
        const updated = [...prev];
        densities.forEach((d) => {
          const idx = ROAD_TO_DEVICE[d.roadId];
          if (idx !== undefined && updated[idx].status === "active") {
            updated[idx] = {
              ...updated[idx],
              avgSpeedKmh: d.avgSpeedKmh,
              occupancyPct: d.occupancyPct,
              vehicleCount: Math.round(d.vehiclesPerKm * 0.4),
              lastUpdatedAt: Date.now(),
            };
          }
        });
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  // Poll every 4 seconds
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, []);

  // Also refresh on WS step change every 10 steps
  useEffect(() => {
    if (wsStep > 0 && wsStep % 10 === 0) refresh();
  }, [wsStep]);

  const activeCount = devices.filter((d) => d.status === "active").length;



  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col gap-3">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-2">
          <Camera className="w-4 h-4 text-sky-500" />
          <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wide">
            CAMERA & IOT SENSOR MONITORING
          </h3>
        </div>
        <span className="text-[10px] font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
          {activeCount}/{devices.length} Devices Online
        </span>
      </div>

      {/* Device List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {devices.map((dev) => (
          <div
            key={dev.id}
            className={`p-3 rounded-xl border flex flex-col justify-between gap-2.5 transition-all ${
              dev.status === "active"
                ? "bg-slate-50/80 border-slate-200"
                : "bg-amber-50/60 border-amber-200"
            }`}
          >
            {/* Title & Status badge */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {dev.type === "camera" ? (
                  <Camera className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                ) : (
                  <Radio className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                )}
                <div>
                  <span className="font-extrabold text-xs text-slate-900 block">{dev.name}</span>
                  <span className="text-[10px] text-slate-400 font-medium">{dev.location}</span>
                </div>
              </div>

              <span
                className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                  dev.status === "active"
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {dev.status}
              </span>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-1 bg-white p-2 rounded-lg border border-slate-200/80 text-[11px] text-center">
              <div>
                <span className="text-[9px] text-slate-400 font-bold uppercase block">Volume</span>
                <span className="font-extrabold text-slate-800">{dev.vehicleCount} veh</span>
              </div>
              <div>
                <span className="text-[9px] text-slate-400 font-bold uppercase block">Avg Speed</span>
                <span className="font-extrabold text-slate-800">{dev.avgSpeedKmh} km/h</span>
              </div>
              <div>
                <span className="text-[9px] text-slate-400 font-bold uppercase block">Occupancy</span>
                <span className={`font-extrabold ${dev.occupancyPct > 50 ? "text-amber-600" : "text-emerald-700"}`}>
                  {dev.occupancyPct}%
                </span>
              </div>
            </div>

            {/* Health & Freshness footer */}
            <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3 text-sky-500" />
                <span>Health: <strong className="text-slate-800">{dev.healthPct}%</strong></span>
              </span>
              <span className="text-slate-400 font-mono">
                Freshness: {freshness(dev.lastUpdatedAt)}
              </span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
