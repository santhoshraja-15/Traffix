"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, DEFAULT_MAP_PITCH, MAPBOX_TOKEN } from "@/lib/constants";
import { RouteOption } from "@/types/route";
import { Accident } from "@/types/accident";
import { Ambulance } from "@/types/ambulance";
import { TrafficStateSnapshot } from "@/types/traffic";
import { boundsFromTopology, NetworkTopology, projectToViewBox, riskToColor } from "@/lib/map";
import { ANNA_NAGAR_TOPOLOGY } from "@/lib/annaNagarTopology";
import { EdgeRiskMap } from "@/hooks/useSimulationStream";

import HUDOverlay, { LayerVisibilityState } from "./HUDOverlay";
import VehicleLayer from "./VehicleLayer";
import TrafficSignals from "./TrafficSignals";
import AccidentZone from "./AccidentZone";
import RippleEffect from "./RippleEffect";
import AmbulanceLayer from "./AmbulanceLayer";
import HospitalLayer from "./HospitalLayer";

import { Layers } from "lucide-react";
import { MOCK_TRAFFIC_SNAPSHOT } from "@/lib/mockData";

const SVG_W = 1000;
const SVG_H = 720;
const TOPOLOGY_SOURCE = "anna-nagar-network";
const TOPOLOGY_LAYER = "anna-nagar-roads";

interface TrafficMapProps {
  activeRoute?: RouteOption;
  accident?: Accident | null;
  ambulance?: Ambulance | null;
  isNavigating?: boolean;
  trafficSnapshot?: TrafficStateSnapshot;
  riskByEdge?: EdgeRiskMap;
  onBaselineReady?: () => void;
}

export default function TrafficMap({
  activeRoute,
  accident,
  ambulance,
  isNavigating = false,
  trafficSnapshot = MOCK_TRAFFIC_SNAPSHOT,
  riskByEdge = {},
  onBaselineReady,
}: TrafficMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const topologyRef = useRef<NetworkTopology>(ANNA_NAGAR_TOPOLOGY);
  const baselineNotified = useRef(false);
  const [hasToken, setHasToken] = useState(false);
  const [topology] = useState<NetworkTopology>(ANNA_NAGAR_TOPOLOGY);

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
    if (baselineNotified.current) return;
    baselineNotified.current = true;
    onBaselineReady?.();
  }, [onBaselineReady]);

  useEffect(() => {
    const token = MAPBOX_TOKEN || process.env.NEXT_PUBLIC_MAP_TOKEN;
    if (token && token.startsWith("pk.") && !token.includes("example_token")) {
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
          if (!map.current) return;
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

          const loaded = topologyRef.current;
          if (loaded && !map.current.getSource(TOPOLOGY_SOURCE)) {
            map.current.addSource(TOPOLOGY_SOURCE, { type: "geojson", data: loaded });
            map.current.addLayer({
              id: TOPOLOGY_LAYER,
              type: "line",
              source: TOPOLOGY_SOURCE,
              paint: {
                "line-width": 4,
                "line-color": "#22c55e",
                "line-opacity": 0.9,
              },
            });
          }
        });
      }
    }
  }, []);

  useEffect(() => {
    if (!topology || !map.current?.isStyleLoaded()) return;
    if (!map.current.getSource(TOPOLOGY_SOURCE)) {
      map.current.addSource(TOPOLOGY_SOURCE, { type: "geojson", data: topology });
      map.current.addLayer({
        id: TOPOLOGY_LAYER,
        type: "line",
        source: TOPOLOGY_SOURCE,
        paint: {
          "line-width": 4,
          "line-color": "#22c55e",
          "line-opacity": 0.9,
        },
      });
    }
  }, [topology]);

  useEffect(() => {
    const source = map.current?.getSource(TOPOLOGY_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    const current = topologyRef.current;
    if (!source || !current) return;

    const colored: NetworkTopology = {
      ...current,
      features: current.features.map((feature) => ({
        ...feature,
        properties: {
          ...feature.properties,
          risk_score: riskByEdge[feature.properties.edge_id] ?? 0,
        },
      })),
    };
    source.setData(colored as GeoJSON.FeatureCollection);

    if (map.current?.getLayer(TOPOLOGY_LAYER)) {
      map.current.setPaintProperty(TOPOLOGY_LAYER, "line-color", [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", "risk_score"], 0],
        0,
        "#22c55e",
        0.5,
        "#eab308",
        1,
        "#ef4444",
      ]);
    }
  }, [riskByEdge]);

  const bounds = topology ? boundsFromTopology(topology) : null;
  const live = Object.keys(riskByEdge).length > 0;

  return (
    <div className="relative w-full h-full min-h-[400px] bg-slate-100 rounded-b-xl overflow-hidden flex items-center justify-center border border-slate-200">
      <HUDOverlay
        layers={layers}
        onToggleLayer={handleToggleLayer}
        onResetCamera={handleResetCamera}
      />

      <div ref={mapContainer} className="absolute inset-0 w-full h-full" />

      {/* SVG topology: always drawn so the Anna Nagar graph renders without Mapbox */}
      <svg
        className="absolute inset-0 w-full h-full z-10 pointer-events-none"
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <rect width={SVG_W} height={SVG_H} fill={hasToken ? "transparent" : "#0f172a"} />
        {!hasToken && (
          <defs>
            <pattern id="grid-3d" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
            </pattern>
          </defs>
        )}
        {!hasToken && <rect width={SVG_W} height={SVG_H} fill="url(#grid-3d)" />}
        {topology && bounds &&
          topology.features.map((feature) => {
            const coords = feature.geometry.coordinates;
            if (coords.length < 2) return null;
            const d = coords
              .map(([lng, lat], i) => {
                const { x, y } = projectToViewBox(lng, lat, bounds, SVG_W, SVG_H);
                return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
              })
              .join(" ");
            const score = riskByEdge[feature.properties.edge_id] ?? 0;
            return (
              <path
                key={feature.properties.edge_id}
                d={d}
                fill="none"
                stroke={live ? riskToColor(score) : "#38bdf8"}
                strokeWidth={live ? 5 : 4}
                strokeLinecap="round"
                opacity={0.92}
              />
            );
          })}
      </svg>

      <div className="absolute top-3 left-3 z-20 flex items-center gap-2 text-xs">
        <div className="flex items-center gap-2 bg-slate-900/90 text-white px-3 py-1.5 rounded-lg border border-slate-700 backdrop-blur">
          <span className={`w-2 h-2 rounded-full ${topology ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`} />
          <span className="font-semibold">
            {topology
              ? `Anna Nagar network · ${topology.metadata?.edges ?? topology.features.length} edges`
              : "Loading Anna Nagar topology…"}
          </span>
        </div>
        {live && (
          <div className="flex items-center gap-2 bg-emerald-700/90 text-white px-3 py-1.5 rounded-lg border border-emerald-500/40">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            <span className="font-semibold">Live V15 risk (throttled 1s)</span>
          </div>
        )}
      </div>

      {!hasToken && (
        <div className="absolute inset-0 pointer-events-none z-10">
          {layers.vehicles && (
            <div className="absolute left-[280px] top-[200px]">
              <VehicleLayer vehicles={trafficSnapshot.vehicles} />
            </div>
          )}
          {layers.signals && (
            <div className="absolute left-[280px] top-[180px]">
              <TrafficSignals signals={trafficSnapshot.signals} />
            </div>
          )}
          {layers.incidents && accident && (
            <div className="absolute left-[480px] top-[140px] -translate-x-1/2 -translate-y-1/2">
              <RippleEffect />
              <AccidentZone accident={accident} />
            </div>
          )}
          {layers.emergency && ambulance && ambulance.status !== "idle" && (
            <div className="absolute left-[340px] top-[180px] -translate-x-1/2 -translate-y-1/2">
              <AmbulanceLayer ambulance={ambulance} />
            </div>
          )}
          <div className="absolute left-[650px] top-[220px]">
            <HospitalLayer />
          </div>
        </div>
      )}

      <div className="absolute bottom-3 left-3 right-3 z-20 text-[10px] text-slate-300 flex items-center justify-between">
        <span className="flex items-center gap-1.5 bg-slate-900/80 px-2 py-1 rounded">
          <Layers className="w-3 h-3 text-sky-400" />
          Static Anna Nagar baseline · live colors after map paint
        </span>
        <span className="bg-slate-900/80 px-2 py-1 rounded">
          Anna Nagar, Chennai ({DEFAULT_MAP_CENTER.lat}° N, {DEFAULT_MAP_CENTER.lng}° E)
        </span>
      </div>
    </div>
  );
}
