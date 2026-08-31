"use client";

import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, DEFAULT_MAP_PITCH, MAPBOX_TOKEN } from "@/lib/constants";
import { RouteOption, LocationSuggestion } from "@/types/route";
import { GeoCoordinates } from "@/types/common";
import type { FeatureCollection } from "geojson";
import {
  boundsFromTopology,
  NetworkTopology,
  TopologyFeature,
  projectToViewBox,
  riskToColor,
  GeoBounds,
  CameraState,
  clampScale,
  centerOfBounds,
  baseSpanForAspect,
  computeViewBounds,
  unprojectFromViewBox,
  boundsFromPoints,
  scaleToFit,
} from "@/lib/map";
import { fetchNetworkTopology } from "@/services/networkApi";
import { fetchRealHospitals } from "@/services/ambulanceApi";
import { EdgeRiskMap, StreamAccident, StreamMission, StreamVehicle } from "@/hooks/useSimulationStream";
import { useVehicleInterpolation } from "@/hooks/useVehicleInterpolation";

import HUDOverlay, { LayerVisibilityState } from "./HUDOverlay";
import VehicleLayer from "./VehicleLayer";
import AccidentZone from "./AccidentZone";
import RippleEffect from "./RippleEffect";
import AmbulanceLayer from "./AmbulanceLayer";
import HospitalLayer from "./HospitalLayer";
import JourneyVehicleMarker from "./JourneyVehicleMarker";

import { Layers, Flag } from "lucide-react";

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
const ACCIDENTS_SOURCE = "active-accidents";
const ACCIDENTS_LAYER = "active-accidents-dots";
const CORRIDOR_SOURCE = "green-corridor";
const CORRIDOR_LAYER = "green-corridor-line";
// Distinct both from the risk-severity green (thin, low opacity, used for
// LOW-risk roads) and from the user route's blue — a clearly separate,
// bold emergency accent per DESIGN_SYSTEM.md §3/§7.
const CORRIDOR_COLOR = "#16a34a";
const AFFECTED_CORRIDOR_SOURCE = "affected-corridors";
const AFFECTED_CORRIDOR_LAYER = "affected-corridors-line";
// Distinct from both the ambulance green corridor and the user's blue
// route — a dashed warning amber tracing the real, currently-reduced-
// capacity road segment (see app/routing/graph_manager.py::apply_capacity_multiplier),
// not just a point marker at the accident's location.
const AFFECTED_CORRIDOR_COLOR = "#f97316";
const AMBULANCE_SOURCE = "active-ambulances";
const AMBULANCE_LAYER = "active-ambulances-dots";
const HOSPITALS_SOURCE = "real-hospitals";
const HOSPITALS_LAYER = "real-hospitals-dots";
const JOURNEY_TRAVELED_SOURCE = "journey-traveled";
const JOURNEY_TRAVELED_LAYER = "journey-traveled-line";
const JOURNEY_REMAINING_SOURCE = "journey-remaining";
const JOURNEY_REMAINING_LAYER = "journey-remaining-line";
// The traveled portion reuses the route's own blue but solid/bold; the
// remaining portion is dimmed so the covered path reads as "done" without
// a second unrelated color competing with the risk/route/corridor palette.
const JOURNEY_TRAVELED_COLOR = "#0284c7";
const JOURNEY_REMAINING_COLOR = "#7dd3fc";
const JOURNEY_VEHICLE_SOURCE = "journey-vehicle";
const JOURNEY_VEHICLE_LAYER = "journey-vehicle-dot";

/** Real active-journey vehicle state from hooks/useJourneySimulation —
 * derived from the route's own real geometry, real elapsed time, and real
 * live per-edge traffic. Never a second routing/simulation engine. */
export interface JourneyVehicleState {
  position: GeoCoordinates | null;
  headingDeg: number;
  traveled: GeoCoordinates[];
  remaining: GeoCoordinates[];
  arrived: boolean;
}

interface TrafficMapProps {
  activeRoute?: RouteOption;
  /** Real, currently-active accidents from the WebSocket stream — see
   * app/services/accident_service.py. Empty array, never fabricated. */
  accidents?: StreamAccident[];
  /** Real, currently-active emergency missions — see
   * app/emergency/mission_manager.py. Empty array, never fabricated. */
  missions?: StreamMission[];
  isNavigating?: boolean;
  riskByEdge?: EdgeRiskMap;
  /** Latest authoritative vehicle snapshot from the real WebSocket stream —
   * empty whenever SUMO isn't connected (see FRONTEND_AUDIT.md §1.2). This
   * component smooths motion between updates but never invents a vehicle. */
  vehicles?: StreamVehicle[];
  /** Present only while an active-navigation journey is running — see
   * app/page.tsx. Drives the journey vehicle marker, the traveled/
   * remaining route split, and camera-follow below. */
  journeyVehicle?: JourneyVehicleState;
  onBaselineReady?: () => void;
}

function accidentsToGeoJSON(accidents: StreamAccident[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: accidents
      .filter((a) => a.lat !== null && a.lng !== null)
      .map((a) => ({
        type: "Feature",
        properties: { id: a.accident_id, severity: a.severity, roadName: a.road_name },
        geometry: { type: "Point", coordinates: [a.lng as number, a.lat as number] },
      })),
  };
}

// The real, currently-reduced-capacity road segment for each active
// accident — its actual full geometry (not a straight line, not just the
// point marker), looked up from the already-loaded real network topology
// by the accident's own edge_id.
interface AccidentCorridorEntry {
  accidentId: string;
  feature: TopologyFeature;
}

// Keyed by accident_id, not edge_id: two independent real accidents can
// legitimately land on the same edge (confirmed live — placing two
// accidents on one edge during testing produced a real React "duplicate
// key" warning when this was keyed by edge_id alone, which per React's own
// warning risks elements being silently duplicated/omitted on update).
// accident_id is unique per accident by construction, edge_id is not.
function getAccidentCorridorFeatures(
  accidents: StreamAccident[],
  topology: NetworkTopology | null
): AccidentCorridorEntry[] {
  if (!topology) return [];
  const byEdgeId = new Map(topology.features.map((f) => [f.properties.edge_id, f]));
  return accidents
    .map((a) => {
      const feature = byEdgeId.get(a.edge_id);
      return feature ? { accidentId: a.accident_id, feature } : undefined;
    })
    .filter((entry): entry is AccidentCorridorEntry => entry !== undefined);
}

function accidentCorridorsToGeoJSON(
  accidents: StreamAccident[],
  topology: NetworkTopology | null
): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: getAccidentCorridorFeatures(accidents, topology).map(({ accidentId, feature }) => ({
      type: "Feature" as const,
      properties: { edge_id: feature.properties.edge_id, accident_id: accidentId },
      geometry: feature.geometry,
    })),
  };
}

// The real emergency route(s) each mission is currently on — outbound while
// heading to the accident, the real (possibly different) return route once
// heading back. Never a straight line: both come straight from the real
// routing engine (see app/emergency/mission_manager.py).
function missionsToCorridorGeoJSON(missions: StreamMission[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: missions
      .filter((m) => m.state !== "emergency_completed")
      .map((m) => {
        const coords =
          m.state === "returning_to_hospital" && m.return_coords ? m.return_coords : m.outbound_coords;
        return {
          type: "Feature" as const,
          properties: { id: m.mission_id },
          geometry: {
            type: "LineString" as const,
            coordinates: coords.map((c) => [c.lng, c.lat]),
          },
        };
      })
      .filter((f) => f.geometry.coordinates.length >= 2),
  };
}

function missionsToAmbulanceGeoJSON(missions: StreamMission[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: missions
      .filter((m) => m.state !== "emergency_completed")
      .map((m) => ({
        type: "Feature",
        properties: { id: m.mission_id, state: m.state, unit: m.unit_number },
        geometry: { type: "Point", coordinates: [m.lng, m.lat] },
      })),
  };
}

function hospitalsToGeoJSON(hospitals: LocationSuggestion[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: hospitals.map((h) => ({
      type: "Feature",
      properties: { name: h.name },
      geometry: { type: "Point", coordinates: [h.lng, h.lat] },
    })),
  };
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

function coordsToLineGeoJSON(coords: GeoCoordinates[]): FeatureCollection {
  if (coords.length < 2) return { type: "FeatureCollection", features: [] };
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {},
        geometry: { type: "LineString", coordinates: coords.map((c) => [c.lng, c.lat]) },
      },
    ],
  };
}

function journeyVehiclePointGeoJSON(vehicle: JourneyVehicleState | undefined): FeatureCollection {
  if (!vehicle?.position) return { type: "FeatureCollection", features: [] };
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { heading: vehicle.headingDeg, arrived: vehicle.arrived },
        geometry: { type: "Point", coordinates: [vehicle.position.lng, vehicle.position.lat] },
      },
    ],
  };
}

export default function TrafficMap({
  activeRoute,
  accidents = [],
  missions = [],
  isNavigating = false,
  riskByEdge = {},
  vehicles = [],
  journeyVehicle,
  onBaselineReady,
}: TrafficMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const outerRef = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const baselineNotified = useRef(false);
  const [hasToken, setHasToken] = useState(false);
  const [topology, setTopology] = useState<NetworkTopology | null>(null);
  const [topologyError, setTopologyError] = useState<string | null>(null);
  const topologyRef = useRef<NetworkTopology | null>(null);
  topologyRef.current = topology;
  const [hospitals, setHospitals] = useState<LocationSuggestion[]>([]);

  // ── SVG-fallback camera (pan/zoom) — see lib/map.ts's "Interactive camera"
  // section. Only used when !hasToken; Mapbox owns its own real camera
  // natively when a real token is configured. `scale=1` == fit-to-network.
  const [camera, setCamera] = useState<CameraState | null>(null);
  const cameraRef = useRef<CameraState | null>(null);
  cameraRef.current = camera;
  const cameraInitialized = useRef(false);
  // The map panel's real on-screen size — measured (not assumed) so the
  // rendered view genuinely fills the panel instead of being letterboxed
  // inside a fixed-aspect-ratio box unrelated to the real container.
  const [containerSize, setContainerSize] = useState({ width: SVG_W, height: SVG_H });
  const containerSizeRef = useRef(containerSize);
  containerSizeRef.current = containerSize;
  // Which route we already auto-framed — a route "selected" event should
  // fit it into view exactly once, then leave the user's own subsequent
  // pan/zoom alone (never fight manual camera control on every re-render).
  const lastFitRouteId = useRef<string | undefined>(undefined);

  // ── Active-journey camera follow ──────────────────────────────────────
  // Engaged automatically once a journeyVehicle position exists; disengaged
  // the instant the user manually drags/zooms/double-clicks (the SAME
  // native handlers already built for general map interaction — see the
  // interaction useEffect below), matching "respect the user's manual
  // pan/zoom, provide a working recenter." A React state (not just a ref)
  // so the HUD's Recenter button can reflect whether it's currently needed.
  const [autoFollow, setAutoFollow] = useState(true);
  const autoFollowRef = useRef(true);
  autoFollowRef.current = autoFollow;
  const journeyVehicleRef = useRef<JourneyVehicleState | undefined>(journeyVehicle);
  journeyVehicleRef.current = journeyVehicle;
  const lastFollowedJourneyKey = useRef<string | undefined>(undefined);

  // Real, continuously-interpolated vehicle positions (ANIMATED_EFFECTS.md §2).
  const interpolatedVehicles = useVehicleInterpolation(vehicles);

  // Real hospitals — fetched once (they don't change during a session).
  useEffect(() => {
    fetchRealHospitals().then(setHospitals).catch(() => setHospitals([]));
  }, []);

  const [layers, setLayers] = useState<LayerVisibilityState>({
    buildings: true,
    vehicles: true,
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
    if (hasToken && map.current) {
      map.current.flyTo({
        center: [DEFAULT_MAP_CENTER.lng, DEFAULT_MAP_CENTER.lat],
        zoom: DEFAULT_MAP_ZOOM,
        pitch: DEFAULT_MAP_PITCH,
        bearing: 0,
      });
      return;
    }
    // SVG-fallback mode: previously a no-op (map.current is never created
    // without a real Mapbox token, so this whole handler silently did
    // nothing) — now genuinely resets to a fresh fit-to-network view.
    if (topologyRef.current) {
      const nb = boundsFromTopology(topologyRef.current);
      const c = centerOfBounds(nb);
      setCamera({ lng: c.lng, lat: c.lat, scale: 1 });
    }
  };

  // Measure the map panel's REAL on-screen size (not assumed) so the SVG
  // view fills it exactly — fixes the fixed-1000x720-viewBox letterboxing
  // that previously wasted real panel space whenever the panel's actual
  // aspect ratio wasn't ~1.39:1.
  useEffect(() => {
    const el = outerRef.current;
    if (!el) return;
    const update = () => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setContainerSize({ width: rect.width, height: rect.height });
      }
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Initial camera: fit the whole real network once it loads — "the map
  // must initially frame the Anna Nagar network appropriately." A ref guard
  // (matching baselineNotified's pattern above) rather than a state
  // dependency, so this fires exactly once and never re-overrides a camera
  // the user has since panned/zoomed.
  useEffect(() => {
    if (cameraInitialized.current || !topology) return;
    cameraInitialized.current = true;
    const nb = boundsFromTopology(topology);
    const c = centerOfBounds(nb);
    setCamera({ lng: c.lng, lat: c.lat, scale: 1 });
  }, [topology]);

  // When a NEW route is selected, automatically fit it into view — once per
  // route id, so a manual pan/zoom afterward is never fought on re-render.
  useEffect(() => {
    if (!activeRoute || activeRoute.coordinates.length < 2) {
      if (!activeRoute) lastFitRouteId.current = undefined;
      return;
    }
    if (lastFitRouteId.current === activeRoute.id) return;
    lastFitRouteId.current = activeRoute.id;

    const routeBounds = boundsFromPoints(
      activeRoute.coordinates.map((c) => ({ lng: c.lng, lat: c.lat }))
    );
    if (!routeBounds) return;

    if (hasToken && map.current) {
      map.current.fitBounds(
        [
          [routeBounds.minLng, routeBounds.minLat],
          [routeBounds.maxLng, routeBounds.maxLat],
        ],
        { padding: 60, duration: 800 }
      );
      return;
    }

    if (!topologyRef.current) return;
    const nb = boundsFromTopology(topologyRef.current);
    const aspect = containerSizeRef.current.width / containerSizeRef.current.height;
    const scale = scaleToFit(nb, routeBounds, aspect);
    const center = centerOfBounds(routeBounds);
    setCamera({ lng: center.lng, lat: center.lat, scale });
  }, [activeRoute, hasToken]);

  // Real pan (drag), zoom (wheel/trackpad/pinch), and double-click-zoom for
  // the SVG-fallback map. Mapbox is already natively interactive with a
  // real token (wheel/drag/pinch/double-click all work out of the box) —
  // this only adds the equivalent, previously entirely-missing interaction
  // layer to the custom SVG renderer used whenever no token is configured.
  // Attached once (native listeners, not React's passive-by-default
  // onWheel) and reads live camera/size/topology via refs so it never needs
  // to re-bind on every state change.
  useEffect(() => {
    const el = outerRef.current;
    if (!el || hasToken) return;

    const viewBoundsNow = (): GeoBounds | null => {
      const topo = topologyRef.current;
      const cam = cameraRef.current;
      if (!topo || !cam) return null;
      const nb = boundsFromTopology(topo);
      const { width, height } = containerSizeRef.current;
      return computeViewBounds(nb, cam, width / height);
    };

    const zoomAt = (mx: number, my: number, factor: number) => {
      const topo = topologyRef.current;
      const cam = cameraRef.current;
      const bounds = viewBoundsNow();
      if (!topo || !cam || !bounds) return;
      const { width, height } = containerSizeRef.current;
      const point = unprojectFromViewBox(mx, my, bounds, width, height);
      const newScale = clampScale(cam.scale * factor);
      const nb = boundsFromTopology(topo);
      const { lngSpan, latSpan } = baseSpanForAspect(nb, width / height);
      const newLngSpan = lngSpan / newScale;
      const newLatSpan = latSpan / newScale;
      setCamera({
        lng: point.lng + newLngSpan * (0.5 - mx / width),
        lat: point.lat + newLatSpan * (my / height - 0.5),
        scale: newScale,
      });
    };

    // The HUD (layer toggles, zoom buttons, reset) is a React child inside
    // this same outer container, marked with data-map-ui. A DOM ancestry
    // check here — not React's stopPropagation — is what actually works:
    // these are native addEventListener callbacks on an ANCESTOR of the
    // HUD, and native bubbling reaches them before React's own root-level
    // synthetic dispatch (and thus any stopPropagation called inside a
    // React handler) ever runs. Without this, clicking a HUD button also
    // starts a map drag/setPointerCapture and the click never reaches the
    // button — confirmed live: the zoom +/- buttons silently did nothing.
    const isMapUiTarget = (target: EventTarget | null): boolean =>
      target instanceof Element && target.closest("[data-map-ui]") !== null;

    // Any real manual pan/zoom/double-click disengages journey camera-
    // follow — "if the user manually pans/zooms, respect their
    // interaction" — until they explicitly click Recenter.
    const disengageFollow = () => {
      if (autoFollowRef.current) setAutoFollow(false);
    };

    const onWheel = (e: WheelEvent) => {
      if (isMapUiTarget(e.target)) return;
      disengageFollow();
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      // Trackpad pinch is reported as a wheel event with ctrlKey=true and a
      // finer deltaY — a gentler exponent keeps it from feeling twitchy.
      const intensity = e.ctrlKey ? 0.02 : 0.0018;
      const factor = Math.exp(-e.deltaY * intensity);
      zoomAt(mx, my, factor);
    };

    let dragPointerId: number | null = null;
    let dragStart: { x: number; y: number; camera: CameraState; bounds: GeoBounds } | null = null;
    const activePointers = new Map<number, { x: number; y: number }>();
    let pinchStartDist: number | null = null;
    let pinchStartScale = 1;

    const onPointerDown = (e: PointerEvent) => {
      if (isMapUiTarget(e.target)) return;
      disengageFollow();
      activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (activePointers.size === 1) {
        const cam = cameraRef.current;
        const bounds = viewBoundsNow();
        if (!cam || !bounds) return;
        dragPointerId = e.pointerId;
        dragStart = { x: e.clientX, y: e.clientY, camera: cam, bounds };
        el.setPointerCapture(e.pointerId);
        el.style.cursor = "grabbing";
      } else if (activePointers.size === 2) {
        // Second finger down — switch from drag to pinch-zoom.
        dragPointerId = null;
        dragStart = null;
        const pts = Array.from(activePointers.values());
        pinchStartDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        pinchStartScale = cameraRef.current?.scale ?? 1;
      }
    };

    const onPointerMove = (e: PointerEvent) => {
      if (!activePointers.has(e.pointerId)) return;
      activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

      if (activePointers.size === 2 && pinchStartDist !== null) {
        const pts = Array.from(activePointers.values());
        const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        const midX = (pts[0].x + pts[1].x) / 2;
        const midY = (pts[0].y + pts[1].y) / 2;
        const rect = el.getBoundingClientRect();
        const cam = cameraRef.current;
        if (!cam) return;
        const targetScale = clampScale(pinchStartScale * (dist / pinchStartDist));
        zoomAt(midX - rect.left, midY - rect.top, targetScale / cam.scale);
        return;
      }

      if (dragPointerId !== e.pointerId || !dragStart) return;
      const dxScreen = e.clientX - dragStart.x;
      const dyScreen = e.clientY - dragStart.y;
      const { width, height } = containerSizeRef.current;
      const lngSpan = dragStart.bounds.maxLng - dragStart.bounds.minLng;
      const latSpan = dragStart.bounds.maxLat - dragStart.bounds.minLat;
      setCamera({
        lng: dragStart.camera.lng - (dxScreen / width) * lngSpan,
        lat: dragStart.camera.lat + (dyScreen / height) * latSpan,
        scale: dragStart.camera.scale,
      });
    };

    const endPointer = (e: PointerEvent) => {
      activePointers.delete(e.pointerId);
      if (e.pointerId === dragPointerId) {
        dragPointerId = null;
        dragStart = null;
        el.style.cursor = "grab";
      }
      if (activePointers.size < 2) pinchStartDist = null;
    };

    const onDoubleClick = (e: MouseEvent) => {
      if (isMapUiTarget(e.target)) return;
      disengageFollow();
      const rect = el.getBoundingClientRect();
      zoomAt(e.clientX - rect.left, e.clientY - rect.top, 1.6);
    };

    el.style.cursor = "grab";
    el.addEventListener("wheel", onWheel, { passive: false });
    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", endPointer);
    el.addEventListener("pointercancel", endPointer);
    el.addEventListener("dblclick", onDoubleClick);

    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", endPointer);
      el.removeEventListener("pointercancel", endPointer);
      el.removeEventListener("dblclick", onDoubleClick);
      el.style.cursor = "";
    };
  }, [hasToken]);

  // Discrete +/- zoom-button handler (HUD buttons) — zooms toward the
  // current view's center rather than a cursor position.
  const handleZoomButton = (factor: number) => {
    const cam = cameraRef.current;
    if (!cam) return;
    setCamera({ ...cam, scale: clampScale(cam.scale * factor) });
  };

  const handleRecenterOnVehicle = () => {
    setAutoFollow(true);
    const jv = journeyVehicleRef.current;
    const cam = cameraRef.current;
    if (jv?.position && cam) {
      setCamera({ lng: jv.position.lng, lat: jv.position.lat, scale: Math.max(cam.scale, 4) });
    } else if (jv?.position) {
      setCamera({ lng: jv.position.lng, lat: jv.position.lat, scale: 4 });
    }
    if (hasToken && map.current && jv?.position) {
      map.current.easeTo({ center: [jv.position.lng, jv.position.lat], zoom: Math.max(map.current.getZoom(), 16) });
    }
  };

  // A new journey (or the very first vehicle position of one) re-engages
  // auto-follow even if a PREVIOUS journey had it disengaged — each fresh
  // "Start Journey" deserves to start followed.
  useEffect(() => {
    const key = journeyVehicle && !journeyVehicle.arrived ? "active" : undefined;
    if (key && key !== lastFollowedJourneyKey.current) {
      lastFollowedJourneyKey.current = key;
      setAutoFollow(true);
    }
    if (!key) lastFollowedJourneyKey.current = undefined;
  }, [journeyVehicle]);

  // Smoothly follow the real journey vehicle position while auto-follow is
  // engaged — never fights a manual pan/zoom (disengageFollow above stops
  // this the instant the user touches the map), and never resets zoom on
  // every tick (only recentering; zoom stays whatever fit-to-route or the
  // user last set). Small per-tick position deltas (~400ms cadence, a few
  // meters at a time) already read as smooth without an added lerp layer.
  useEffect(() => {
    if (!autoFollow || !journeyVehicle?.position) return;
    if (hasToken && map.current) {
      map.current.easeTo({ center: [journeyVehicle.position.lng, journeyVehicle.position.lat], duration: 350 });
      return;
    }
    setCamera((prev) =>
      prev
        ? { ...prev, lng: journeyVehicle.position!.lng, lat: journeyVehicle.position!.lat }
        : { lng: journeyVehicle.position!.lng, lat: journeyVehicle.position!.lat, scale: 4 }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [journeyVehicle?.position, autoFollow, hasToken]);

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

          // Active-journey traveled/remaining split (see
          // hooks/useJourneySimulation.ts) — drawn on top of ROUTE_LAYER so
          // the covered portion visibly overrides the plain route color.
          if (!map.current.getSource(JOURNEY_REMAINING_SOURCE)) {
            map.current.addSource(JOURNEY_REMAINING_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: JOURNEY_REMAINING_LAYER,
              type: "line",
              source: JOURNEY_REMAINING_SOURCE,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: { "line-width": 5, "line-color": JOURNEY_REMAINING_COLOR, "line-opacity": 0.95 },
            });
          }
          if (!map.current.getSource(JOURNEY_TRAVELED_SOURCE)) {
            map.current.addSource(JOURNEY_TRAVELED_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: JOURNEY_TRAVELED_LAYER,
              type: "line",
              source: JOURNEY_TRAVELED_SOURCE,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: { "line-width": 5, "line-color": JOURNEY_TRAVELED_COLOR, "line-opacity": 1 },
            });
          }
          if (!map.current.getSource(JOURNEY_VEHICLE_SOURCE)) {
            map.current.addSource(JOURNEY_VEHICLE_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: JOURNEY_VEHICLE_LAYER,
              type: "circle",
              source: JOURNEY_VEHICLE_SOURCE,
              paint: {
                "circle-radius": 7,
                "circle-color": "#0ea5e9",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#ffffff",
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

          if (!map.current.getSource(ACCIDENTS_SOURCE)) {
            map.current.addSource(ACCIDENTS_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: ACCIDENTS_LAYER,
              type: "circle",
              source: ACCIDENTS_SOURCE,
              paint: {
                "circle-radius": 9,
                "circle-color": "#dc2626",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#ffffff",
              },
            });
          }

          if (!map.current.getSource(CORRIDOR_SOURCE)) {
            map.current.addSource(CORRIDOR_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: CORRIDOR_LAYER,
              type: "line",
              source: CORRIDOR_SOURCE,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: { "line-width": 6, "line-color": CORRIDOR_COLOR, "line-opacity": 0.85 },
            });
          }

          if (!map.current.getSource(AFFECTED_CORRIDOR_SOURCE)) {
            map.current.addSource(AFFECTED_CORRIDOR_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: AFFECTED_CORRIDOR_LAYER,
              type: "line",
              source: AFFECTED_CORRIDOR_SOURCE,
              layout: { "line-cap": "round", "line-join": "round" },
              paint: {
                "line-width": 6,
                "line-color": AFFECTED_CORRIDOR_COLOR,
                "line-opacity": 0.9,
                "line-dasharray": [2, 1.5],
              },
            });
          }

          if (!map.current.getSource(AMBULANCE_SOURCE)) {
            map.current.addSource(AMBULANCE_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: AMBULANCE_LAYER,
              type: "circle",
              source: AMBULANCE_SOURCE,
              paint: {
                "circle-radius": 7,
                "circle-color": "#0ea5e9",
                "circle-stroke-width": 2,
                "circle-stroke-color": "#ffffff",
              },
            });
          }

          if (!map.current.getSource(HOSPITALS_SOURCE)) {
            map.current.addSource(HOSPITALS_SOURCE, {
              type: "geojson",
              data: { type: "FeatureCollection", features: [] },
            });
            map.current.addLayer({
              id: HOSPITALS_LAYER,
              type: "circle",
              source: HOSPITALS_SOURCE,
              paint: {
                "circle-radius": 4,
                "circle-color": "#f43f5e",
                "circle-stroke-width": 1,
                "circle-stroke-color": "#ffffff",
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

  // Real active-journey vehicle position + traveled/remaining route split
  // (see hooks/useJourneySimulation.ts) — driven straight into the Mapbox
  // sources each tick, same "don't rerender a large tree per tick"
  // reasoning as the live-vehicles effect above.
  useEffect(() => {
    const traveledSource = map.current?.getSource(JOURNEY_TRAVELED_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    const remainingSource = map.current?.getSource(JOURNEY_REMAINING_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    const vehicleSource = map.current?.getSource(JOURNEY_VEHICLE_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (traveledSource) traveledSource.setData(coordsToLineGeoJSON(journeyVehicle?.traveled ?? []));
    if (remainingSource) remainingSource.setData(coordsToLineGeoJSON(journeyVehicle?.remaining ?? []));
    if (vehicleSource) vehicleSource.setData(journeyVehiclePointGeoJSON(journeyVehicle));
  }, [journeyVehicle]);

  // Real, currently-active accidents — see app/services/accident_service.py.
  useEffect(() => {
    const source = map.current?.getSource(ACCIDENTS_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (!source) return;
    source.setData(accidentsToGeoJSON(accidents));
  }, [accidents]);

  // The real affected road segment for each active accident — its actual
  // geometry from the already-loaded network topology, not a point.
  useEffect(() => {
    const source = map.current?.getSource(AFFECTED_CORRIDOR_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (!source) return;
    source.setData(accidentCorridorsToGeoJSON(accidents, topologyRef.current));
  }, [accidents, topology]);

  // Real emergency missions — green corridor route + ambulance position,
  // both real (see app/emergency/mission_manager.py), updated every tick.
  useEffect(() => {
    const corridorSource = map.current?.getSource(CORRIDOR_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    const ambulanceSource = map.current?.getSource(AMBULANCE_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (corridorSource) corridorSource.setData(missionsToCorridorGeoJSON(missions));
    if (ambulanceSource) ambulanceSource.setData(missionsToAmbulanceGeoJSON(missions));
  }, [missions]);

  // Real hospitals — static for the session.
  useEffect(() => {
    const source = map.current?.getSource(HOSPITALS_SOURCE) as mapboxgl.GeoJSONSource | undefined;
    if (!source) return;
    source.setData(hospitalsToGeoJSON(hospitals));
  }, [hospitals]);

  // The full-network reference bounds (fit-to-network baseline) vs. the
  // ACTUAL current view window (reference bounds narrowed/panned by the
  // live camera) — every projectToViewBox call below now uses viewBounds,
  // not the old fixed full-network bounds, so pan/zoom genuinely changes
  // what's rendered instead of always showing the whole network at a fixed
  // scale (the direct cause of "zooming does not appear to work").
  const networkBounds = topology ? boundsFromTopology(topology) : null;
  const containerAspect = containerSize.width / containerSize.height;
  const viewBounds: GeoBounds | null =
    networkBounds && camera ? computeViewBounds(networkBounds, camera, containerAspect) : networkBounds;
  const bw = containerSize.width;
  const bh = containerSize.height;
  const live = Object.keys(riskByEdge).length > 0;

  return (
    <div
      ref={outerRef}
      className="relative w-full h-full min-h-[400px] bg-slate-100 rounded-b-xl overflow-hidden flex items-center justify-center border border-slate-200"
    >
      <HUDOverlay
        layers={layers}
        onToggleLayer={handleToggleLayer}
        onResetCamera={handleResetCamera}
        showBuildingsToggle={hasToken}
        onZoomIn={!hasToken ? () => handleZoomButton(1.5) : undefined}
        onZoomOut={!hasToken ? () => handleZoomButton(1 / 1.5) : undefined}
        onRecenterVehicle={
          journeyVehicle?.position && !journeyVehicle.arrived && !autoFollow ? handleRecenterOnVehicle : undefined
        }
      />

      <div ref={mapContainer} className="absolute inset-0 w-full h-full" />

      {/* SVG topology + vehicles: only when Mapbox isn't active (otherwise
          Mapbox's own layers above already render this — no double-draw).
          viewBox now matches the panel's REEAL measured size (containerSize)
          rather than a fixed 1000x720 box, so preserveAspectRatio never
          needs to letterbox — the network fills the actual panel. Pointer
          events are handled by the outer container (see the interaction
          useEffect above); pointer-events stays "none" here purely so
          hit-testing falls through to that same container rather than
          needing every child re-annotated. */}
      {!hasToken && (
        <svg
          className="absolute inset-0 w-full h-full z-10 pointer-events-none"
          viewBox={`0 0 ${bw} ${bh}`}
          preserveAspectRatio="xMidYMid meet"
        >
          <rect width={bw} height={bh} fill="#0f172a" />
          <defs>
            <pattern id="grid-3d" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width={bw} height={bh} fill="url(#grid-3d)" />
          {topology && viewBounds &&
            topology.features.map((feature) => {
              const coords = feature.geometry.coordinates;
              if (coords.length < 2) return null;
              const d = coords
                .map(([lng, lat], i) => {
                  const { x, y } = projectToViewBox(lng, lat, viewBounds, bw, bh);
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
          {layers.routes && activeRoute && viewBounds && activeRoute.coordinates.length >= 2 && (
            <path
              d={activeRoute.coordinates
                .map((c, i) => {
                  const { x, y } = projectToViewBox(c.lng, c.lat, viewBounds, bw, bh);
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
          {/* Real emergency green corridor(s) — the actual route each active
              mission is on (outbound or return), never a straight line. */}
          {layers.emergency &&
            viewBounds &&
            missions
              .filter((m) => m.state !== "emergency_completed")
              .map((m) => {
                const coords =
                  m.state === "returning_to_hospital" && m.return_coords ? m.return_coords : m.outbound_coords;
                if (coords.length < 2) return null;
                const d = coords
                  .map((c, i) => {
                    const { x, y } = projectToViewBox(c.lng, c.lat, viewBounds, bw, bh);
                    return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
                  })
                  .join(" ");
                return (
                  <path
                    key={m.mission_id}
                    d={d}
                    fill="none"
                    stroke={CORRIDOR_COLOR}
                    strokeWidth={5}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity={0.85}
                  />
                );
              })}
          {/* The real affected road segment for each active accident — its
              actual geometry from the loaded topology, not just a point
              marker (see accidentCorridorsToGeoJSON above). */}
          {layers.incidents &&
            viewBounds &&
            topology &&
            getAccidentCorridorFeatures(accidents, topology).map(({ accidentId, feature: f }) => {
              const d = f.geometry.coordinates
                .map(([lng, lat], i) => {
                  const { x, y } = projectToViewBox(lng, lat, viewBounds, bw, bh);
                  return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
                })
                .join(" ");
              return (
                <path
                  key={accidentId}
                  d={d}
                  fill="none"
                  stroke={AFFECTED_CORRIDOR_COLOR}
                  strokeWidth={5}
                  strokeDasharray="6 4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity={0.9}
                />
              );
            })}
          {/* Active-journey traveled/remaining split — real sub-polylines of
              the route's own coordinates from useJourneySimulation, never a
              client-invented shape. Drawn over the plain route line above so
              the covered portion visibly reads as "done." */}
          {journeyVehicle && viewBounds && journeyVehicle.remaining.length >= 2 && (
            <path
              d={journeyVehicle.remaining
                .map((c, i) => {
                  const { x, y } = projectToViewBox(c.lng, c.lat, viewBounds, bw, bh);
                  return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
                })
                .join(" ")}
              fill="none"
              stroke={JOURNEY_REMAINING_COLOR}
              strokeWidth={4}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={0.95}
            />
          )}
          {journeyVehicle && viewBounds && journeyVehicle.traveled.length >= 2 && (
            <path
              d={journeyVehicle.traveled
                .map((c, i) => {
                  const { x, y } = projectToViewBox(c.lng, c.lat, viewBounds, bw, bh);
                  return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
                })
                .join(" ")}
              fill="none"
              stroke={JOURNEY_TRAVELED_COLOR}
              strokeWidth={4}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={1}
            />
          )}
          {layers.vehicles && viewBounds && (
            <VehicleLayer vehicles={interpolatedVehicles} bounds={viewBounds} width={bw} height={bh} />
          )}
        </svg>
      )}

      {/* Real hospitals — SVG-fallback mode only, same reasoning as the
          accident/ambulance markers above. */}
      {!hasToken &&
        viewBounds &&
        hospitals.map((h) => {
          const { x, y } = projectToViewBox(h.lng, h.lat, viewBounds, bw, bh);
          return (
            <div
              key={h.name}
              className="absolute z-20 pointer-events-none -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${(x / bw) * 100}%`, top: `${(y / bh) * 100}%` }}
            >
              <HospitalLayer name={h.name} />
            </div>
          );
        })}

      {/* Real accident markers — SVG-fallback mode only (positioned from each
          accident's own real lat/lng, never a shared hardcoded offset).
          When Mapbox is active, the native ACCIDENTS_LAYER circle layer
          above already renders them correctly under pan/zoom; a DOM overlay
          positioned via a one-off map.project() call would go stale on the
          next pan without a React re-render, so it's deliberately not
          duplicated here. */}
      {!hasToken &&
        layers.incidents &&
        viewBounds &&
        accidents
          .filter((a) => a.lat !== null && a.lng !== null)
          .map((a) => {
            const { x, y } = projectToViewBox(a.lng as number, a.lat as number, viewBounds, bw, bh);
            return (
              <div
                key={a.accident_id}
                className="absolute z-20 pointer-events-none -translate-x-1/2 -translate-y-full"
                style={{ left: `${(x / bw) * 100}%`, top: `${(y / bh) * 100}%` }}
              >
                <RippleEffect />
                <AccidentZone accident={a} />
              </div>
            );
          })}

      {/* Real ambulance markers — SVG-fallback mode only, same reasoning as
          the accident markers above (native AMBULANCE_LAYER handles Mapbox). */}
      {!hasToken &&
        layers.emergency &&
        viewBounds &&
        missions
          .filter((m) => m.state !== "emergency_completed")
          .map((m) => {
            const { x, y } = projectToViewBox(m.lng, m.lat, viewBounds, bw, bh);
            return (
              <div
                key={m.mission_id}
                className="absolute z-20 pointer-events-none -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${(x / bw) * 100}%`, top: `${(y / bh) * 100}%` }}
              >
                <AmbulanceLayer mission={m} />
              </div>
            );
          })}

      {/* Real active-journey vehicle marker — SVG-fallback mode only (native
          JOURNEY_VEHICLE_LAYER above handles Mapbox). Position/heading come
          entirely from hooks/useJourneySimulation.ts, never invented here. */}
      {!hasToken && viewBounds && journeyVehicle?.position && (() => {
        const { x, y } = projectToViewBox(journeyVehicle.position.lng, journeyVehicle.position.lat, viewBounds, bw, bh);
        return (
          <div
            data-testid="journey-vehicle-marker"
            className="absolute z-30 pointer-events-none -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${(x / bw) * 100}%`, top: `${(y / bh) * 100}%` }}
          >
            <JourneyVehicleMarker headingDeg={journeyVehicle.headingDeg} arrived={journeyVehicle.arrived} />
          </div>
        );
      })()}

      {/* Destination highlight — the route's real final coordinate,
          emphasized once the journey actually reaches it ("ARRIVED"). */}
      {!hasToken && viewBounds && activeRoute && activeRoute.coordinates.length > 0 && journeyVehicle && (
        (() => {
          const dest = activeRoute.coordinates[activeRoute.coordinates.length - 1];
          const { x, y } = projectToViewBox(dest.lng, dest.lat, viewBounds, bw, bh);
          return (
            <div
              className="absolute z-20 pointer-events-none -translate-x-1/2 -translate-y-full"
              style={{ left: `${(x / bw) * 100}%`, top: `${(y / bh) * 100}%` }}
            >
              <div
                className={`flex items-center justify-center w-7 h-7 rounded-full border-2 shadow-lg ${
                  journeyVehicle.arrived
                    ? "bg-emerald-500 border-white animate-pulse"
                    : "bg-slate-900/90 border-slate-300"
                }`}
              >
                <Flag className={`w-3.5 h-3.5 ${journeyVehicle.arrived ? "text-white" : "text-slate-300"}`} />
              </div>
            </div>
          );
        })()
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
