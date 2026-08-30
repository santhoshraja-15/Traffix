"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, DEFAULT_MAP_PITCH, MAPBOX_TOKEN } from "@/lib/constants";
import { RouteOption } from "@/types/route";
import { Accident } from "@/types/accident";
import { Ambulance } from "@/types/ambulance";
import { TrafficStateSnapshot } from "@/types/traffic";
import type { FeatureCollection } from "geojson";
import { boundsFromTopology, NetworkTopology, projectToViewBox, riskToColor } from "@/lib/map";
import { fetchNetworkTopology } from "@/services/networkApi";
import { EdgeRiskMap, StreamVehicle } from "@/hooks/useSimulationStream";
import { useVehicleInterpolation } from "@/hooks/useVehicleInterpolation";

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
const VEHICLES_SOURCE = "live-vehicles";
const VEHICLES_LAYER = "live-vehicles-dots";
const ROUTE_SOURCE = "active-route";
const ROUTE_LAYER = "active-route-line";
// Distinct from the risk-severity palette (green/amber/orange/red) per
// DESIGN_SYSTEM.md §3 — one clear accent for the active recommended route.
const ROUTE_COLOR = "#0ea5e9";

interface TrafficMapProps {
  activeRoute?: RouteOption;
  accident?: Accident | null;
  ambulance?: Ambulance | null;
  isNavigating?: boolean;
  trafficSnapshot?: TrafficStateSnapshot;
  riskByEdge?: EdgeRiskMap;
  /** Latest authoritative vehicle snapshot from the real WebSocket stream —
   * empty whenever SUMO isn't connected (see FRONTEND_AUDIT.md §1.2). This
   * component smooths motion between updates but never invents a vehicle. */
  vehicles?: StreamVehicle[];
  onBaselineReady?: () => void;
}

function routeToGeoJSON(route: RouteOption | undefined): FeatureCollection {
  if (!route || route.coordinates.length < 2) {
    return { type: "FeatureCollection", features: [] };
  }
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { id: route.id },
        geometry: {
          type: "LineString",
          coordinates: route.coordinates.map((c) => [c.lng, c.lat]),
        },
      },
    ],
  };
}

function vehiclesToGeoJSON(vehicles: ReturnType<typeof useVehicleInterpolation>): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: vehicles.map((v) => ({
      type: "Feature",
      properties: { id: v.id, speedKmh: v.speedKmh, heading: v.headingAngle ?? 0 },
      geometry: { type: "Point", coordinates: [v.position.lng, v.position.lat] },
    })),
  };
}

export default function TrafficMap({
  activeRoute,
  accident,
  ambulance,
  isNavigating = false,
  trafficSnapshot = MOCK_TRAFFIC_SNAPSHOT,
  riskByEdge = {},
  vehicles = [],
  onBaselineReady,
}: TrafficMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const baselineNotified = useRef(false);
  const [hasToken, setHasToken] = useState(false);
  const [topology, setTopology] = useState<NetworkTopology | null>(null);
  const [topologyError, setTopologyError] = useState<string | null>(null);
  const topologyRef = useRef<NetworkTopology | null>(null);
  topologyRef.current = topology;

  // Real, continuously-interpolated vehicle positions (ANIMATED_EFFECTS.md §2).
  const interpolatedVehicles = useVehicleInterpolation(vehicles);

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

  // Load the REAL Anna Nagar network from the backend (app/routing/graph_manager.py,
  // now built from the actual SUMO net file — see FRONTEND_AUDIT.md §1.3). No
  // hand-authored fallback grid: on failure this shows an honest error state.
  useEffect(() => {
    let cancelled = false;
    fetchNetworkTopology()
      .then((data) => {
        if (cancelled) return;
        setTopology(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setTopologyError(err instanceof Error ? err.message : "Network data unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Baseline is "ready" once the real network has either loaded or definitively
  // failed — not on mount, so downstream consumers (e.g. page.tsx's mapReady
  // gate) actually wait for real data instead of firing immediately.
  useEffect(() => {
    if (baselineNotified.current) return;
    if (!topology && !topologyError) return;
    baselineNotified.current = true;
    onBaselineReady?.();
  }, [topology, topologyError, onBaselineReady]);

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
            map.current.addSource(TOPOLOGY_SOURCE, { type: "geojson", data: loaded as unknown as FeatureCollection });
            map.current.addLayer({
              id: TOPOLOGY_LAYER,
              type: "line",
              source: TOPOLOGY_SOURCE,
              paint: {
                "line-width": 2,
                "line-color": "#22c55e",
                "line-opacity": 0.85,
              },
            });
          }

          if (!map.current.getSource(ROUTE_SOURCE)) {
            map.current.addSource(ROUTE_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: ROUTE_LAYER,
              type: "line",
              source: ROUTE_SOURCE,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: {
                "line-width": 5,
                "line-color": ROUTE_COLOR,
                "line-opacity": 0.95,
              },
            });
          }

          if (!map.current.getSource(VEHICLES_SOURCE)) {
            map.current.addSource(VEHICLES_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: VEHICLES_LAYER,
              type: "circle",
              source: VEHICLES_SOURCE,
              paint: {
                "circle-radius": 4,
                "circle-color": "#34d399",
                "circle-stroke-width": 1,
                "circle-stroke-color": "#0f172a",
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
      map.current.addSource(TOPOLOGY_SOURCE, { type: "geojson", data: topology as unknown as FeatureCollection });
      map.current.addLayer({
        id: TOPOLOGY_LAYER,
        type: "line",
        source: TOPOLOGY_SOURCE,
        paint: {
          "line-width": 2,
          "line-color": "#22c55e",
          "line-opacity": 0.85,
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
    source.setData(colored as unknown as FeatureCollection);

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

  // Drive the Mapbox vehicle layer straight from interpolated positions each
  // frame (TECHNICAL_DEEP_DIVE.md §7 — update the map source directly rather
  // than rerendering a large component tree per tick).
  useEffect(() => {
    const source = map.current?.getSource(VEHICLES_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (!source) return;
    source.setData(vehiclesToGeoJSON(interpolatedVehicles));
  }, [interpolatedVehicles]);

  // The active route's real geometry (resolved by the backend against the
  // real network graph — see app/services/routing_service.py), never a
  // straight line or a client-side recomputation.
  useEffect(() => {
    const source = map.current?.getSource(ROUTE_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (!source) return;
    source.setData(routeToGeoJSON(activeRoute));
  }, [activeRoute]);

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

      {/* SVG topology + vehicles: only when Mapbox isn't active (otherwise
          Mapbox's own layers above already render this — no double-draw). */}
      {!hasToken && (
        <svg
          className="absolute inset-0 w-full h-full z-10 pointer-events-none"
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          preserveAspectRatio="xMidYMid meet"
        >
          <rect width={SVG_W} height={SVG_H} fill="#0f172a" />
          <defs>
            <pattern id="grid-3d" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width={SVG_W} height={SVG_H} fill="url(#grid-3d)" />
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
                  strokeWidth={live ? 2.5 : 1.5}
                  strokeLinecap="round"
                  opacity={0.85}
                />
              );
            })}
          {layers.routes && activeRoute && bounds && activeRoute.coordinates.length >= 2 && (
            <path
              d={activeRoute.coordinates
                .map((c, i) => {
                  const { x, y } = projectToViewBox(c.lng, c.lat, bounds, SVG_W, SVG_H);
                  return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
                })
                .join(" ")}
              fill="none"
              stroke={ROUTE_COLOR}
              strokeWidth={4}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={0.95}
            />
          )}
          {layers.vehicles && bounds && (
            <VehicleLayer vehicles={interpolatedVehicles} bounds={bounds} width={SVG_W} height={SVG_H} />
          )}
        </svg>
      )}

      <div className="absolute top-3 left-3 z-20 flex items-center gap-2 text-xs">
        <div className="flex items-center gap-2 bg-slate-900/90 text-white px-3 py-1.5 rounded-lg border border-slate-700 backdrop-blur">
          <span
            className={`w-2 h-2 rounded-full ${
              topology ? "bg-emerald-400" : topologyError ? "bg-red-500" : "bg-amber-400 animate-pulse"
            }`}
          />
          <span className="font-semibold">
            {topology
              ? `Anna Nagar network · ${topology.metadata?.edges ?? topology.features.length} edges`
              : topologyError
              ? "Anna Nagar network data unavailable"
              : "Loading Anna Nagar network…"}
          </span>
        </div>
        {live && (
          <div className="flex items-center gap-2 bg-emerald-700/90 text-white px-3 py-1.5 rounded-lg border border-emerald-500/40">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            <span className="font-semibold">Live V15 risk (throttled 1s)</span>
          </div>
        )}
        {interpolatedVehicles.length > 0 && (
          <div className="flex items-center gap-2 bg-emerald-700/90 text-white px-3 py-1.5 rounded-lg border border-emerald-500/40">
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            <span className="font-semibold">{interpolatedVehicles.length} live vehicles</span>
          </div>
        )}
      </div>

      {!hasToken && (
        <div className="absolute inset-0 pointer-events-none z-10">
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
          Real Anna Nagar network · live vehicles when SUMO is connected
        </span>
        <span className="bg-slate-900/80 px-2 py-1 rounded">
          Anna Nagar, Chennai ({DEFAULT_MAP_CENTER.lat}° N, {DEFAULT_MAP_CENTER.lng}° E)
        </span>
      </div>
    </div>
  );
}
