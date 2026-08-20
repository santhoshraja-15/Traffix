"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, DEFAULT_MAP_PITCH, MAPBOX_TOKEN } from "@/lib/constants";
import { RouteOption } from "@/types/route";
import { Accident } from "@/types/accident";
import { Ambulance } from "@/types/ambulance";
import { TrafficStateSnapshot } from "@/types/traffic";

import HUDOverlay, { LayerVisibilityState } from "./HUDOverlay";
import VehicleLayer from "./VehicleLayer";
import TrafficSignals from "./TrafficSignals";
import RouteLayer from "./RouteLayer";
import AccidentZone from "./AccidentZone";
import RippleEffect from "./RippleEffect";
import AmbulanceLayer from "./AmbulanceLayer";
import HospitalLayer from "./HospitalLayer";

import { Layers } from "lucide-react";
import { MOCK_TRAFFIC_SNAPSHOT } from "@/lib/mockData";

interface TrafficMapProps {
  activeRoute?: RouteOption;
  accident?: Accident | null;
  ambulance?: Ambulance | null;
  isNavigating?: boolean;
  trafficSnapshot?: TrafficStateSnapshot;
}

export default function TrafficMap({
  activeRoute,
  accident,
  ambulance,
  isNavigating = false,
  trafficSnapshot = MOCK_TRAFFIC_SNAPSHOT,
}: TrafficMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [hasToken, setHasToken] = useState(false);

  // Layer Visibility State
  const [layers, setLayers] = useState<LayerVisibilityState>({
    buildings: true,
    vehicles: true,
    signals: true,
    incidents: true,
    emergency: true,
    routes: true,
  });

  const handleToggleLayer = (key: keyof LayerVisibilityState) => {
    setLayers((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      // Toggle Mapbox 3D buildings layer if available
      if (key === "buildings" && map.current && map.current.getLayer("3d-buildings")) {
        map.current.setLayoutProperty(
          "3d-buildings",
          "visibility",
          next.buildings ? "visible" : "none"
        );
      }
      return next;
    });
  };

  const handleResetCamera = () => {
    if (map.current) {
      map.current.flyTo({
        center: [DEFAULT_MAP_CENTER.lng, DEFAULT_MAP_CENTER.lat],
        zoom: DEFAULT_MAP_ZOOM,
        pitch: DEFAULT_MAP_PITCH,
        bearing: 0,
      });
    }
  };

  useEffect(() => {
    const token = MAPBOX_TOKEN || process.env.NEXT_PUBLIC_MAP_TOKEN;
    if (token && token.startsWith("pk.")) {
      setHasToken(true);
      mapboxgl.accessToken = token;

      if (!map.current && mapContainer.current) {
        map.current = new mapboxgl.Map({
          container: mapContainer.current,
          style: "mapbox://styles/mapbox/light-v11",
          center: [DEFAULT_MAP_CENTER.lng, DEFAULT_MAP_CENTER.lat],
          zoom: DEFAULT_MAP_ZOOM,
          pitch: DEFAULT_MAP_PITCH,
          bearing: 0,
        });

        map.current.on("load", () => {
          if (map.current) {
            const styleLayers = map.current.getStyle().layers;
            const labelLayerId = styleLayers?.find(
              (l) => l.type === "symbol" && l.layout?.["text-field"]
            )?.id;

            map.current.addLayer(
              {
                id: "3d-buildings",
                source: "composite",
                "source-layer": "building",
                filter: ["==", "extrude", "true"],
                type: "fill-extrusion",
                minzoom: 13,
                paint: {
                  "fill-extrusion-color": "#e2e8f0",
                  "fill-extrusion-height": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    13,
                    0,
                    15.05,
                    ["get", "height"],
                  ],
                  "fill-extrusion-base": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    13,
                    0,
                    15.05,
                    ["get", "min_height"],
                  ],
                  "fill-extrusion-opacity": 0.6,
                },
              },
              labelLayerId
            );
          }
        });
      }
    }
  }, []);

  return (
    <div className="relative w-full h-full min-h-[400px] bg-slate-100 rounded-b-xl overflow-hidden flex items-center justify-center border border-slate-200">
      
      {/* HUD Layer Toggle & Camera Controller Overlay */}
      <HUDOverlay
        layers={layers}
        onToggleLayer={handleToggleLayer}
        onResetCamera={handleResetCamera}
      />

      {/* Mapbox Canvas */}
      <div ref={mapContainer} className="absolute inset-0 w-full h-full" />

      {/* Interactive Vector Twin Canvas Fallback */}
      {!hasToken && (
        <div className="absolute inset-0 bg-slate-900 text-white flex flex-col justify-between p-4">
          
          {/* Top Status Banner */}
          <div className="flex items-center justify-between text-xs z-10">
            <div className="flex items-center gap-2 bg-slate-800/90 px-3 py-1.5 rounded-lg border border-slate-700 backdrop-blur">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-slate-200">
                SUMO 3D Digital Twin (Anna Salai Vector Grid)
              </span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400 bg-slate-800/90 px-2.5 py-1 rounded-lg border border-slate-700">
              <Layers className="w-3 h-3 text-sky-400" />
              <span>60 FPS Batched</span>
            </div>
          </div>

          {/* Canvas Digital Twin Render Area */}
          <div className="relative flex-1 my-2 rounded-lg border border-slate-800 bg-slate-950/70 overflow-hidden flex items-center justify-center">
            
            {/* Grid network */}
            <svg className="absolute inset-0 w-full h-full opacity-30 pointer-events-none">
              <defs>
                <pattern id="grid-3d" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#334155" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid-3d)" />
            </svg>

            {/* Route Layer */}
            {layers.routes && activeRoute && (
              <svg className="absolute inset-0 w-full h-full z-10 pointer-events-none">
                <path
                  d="M 120 320 Q 280 200, 480 140 T 720 100"
                  fill="none"
                  stroke="#0ea5e9"
                  strokeWidth="6"
                  strokeLinecap="round"
                  className="drop-shadow-[0_0_8px_rgba(14,165,233,0.8)]"
                />
                <path
                  d="M 120 320 Q 280 200, 480 140 T 720 100"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2"
                  strokeDasharray="8 8"
                  className="animate-pulse"
                />
              </svg>
            )}

            {/* Vehicle Layer */}
            {layers.vehicles && (
              <div className="absolute inset-0 z-20 pointer-events-none">
                <div className="absolute left-[280px] top-[200px]">
                  <VehicleLayer vehicles={trafficSnapshot.vehicles} />
                </div>
                <div className="absolute left-[400px] top-[165px]">
                  <VehicleLayer vehicles={trafficSnapshot.vehicles} />
                </div>
              </div>
            )}

            {/* Traffic Signals Layer */}
            {layers.signals && (
              <div className="absolute left-[280px] top-[180px] z-20">
                <TrafficSignals signals={trafficSnapshot.signals} />
              </div>
            )}

            {/* Incident Layer (Accident + Ripple) */}
            {layers.incidents && accident && (
              <div className="absolute left-[480px] top-[140px] -translate-x-1/2 -translate-y-1/2 z-30">
                <RippleEffect />
                <AccidentZone accident={accident} />
              </div>
            )}

            {/* Emergency Layer (Ambulance + Green Corridor) */}
            {layers.emergency && ambulance && ambulance.status !== "idle" && (
              <div className="absolute left-[340px] top-[180px] -translate-x-1/2 -translate-y-1/2 z-30">
                <AmbulanceLayer ambulance={ambulance} />
              </div>
            )}

            {/* Hospital Infrastructure POIs */}
            <div className="absolute left-[650px] top-[220px] z-20">
              <HospitalLayer />
            </div>

          </div>

          {/* Footer Info */}
          <div className="text-[10px] text-slate-400 flex items-center justify-between z-10">
            <span>Provide NEXT_PUBLIC_MAP_TOKEN in .env.local for full Mapbox 3D vector tiles.</span>
            <span>Anna Salai SUMO Network (13.0482° N, 80.2425° E)</span>
          </div>

        </div>
      )}

    </div>
  );
}
