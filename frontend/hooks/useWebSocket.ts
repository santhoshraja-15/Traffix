"use client";

/**
 * useTrafficSocket(simulationId)
 * ================================
 * Phase 3 — The Socket Hook (Step 1 + Step 2)
 *
 * Connects to the FastAPI WebSocket endpoint:
 *   ws://<host>/api/realtime/<simulationId>
 *
 * Thread-safe design decisions:
 *  - All WebSocket state lives in refs — no React state update per message.
 *  - A single setInterval at UI_THROTTLE_MS (1000 ms) is the ONLY trigger
 *    for React state updates, coalescing rapid WS frames into calm 1 Hz renders.
 *  - Exponential-backoff reconnect: starts at RECONNECT_BASE_MS (1 s),
 *    doubles each failed attempt, caps at RECONNECT_MAX_MS (30 s).
 *    Reconnect loop exits cleanly when the component unmounts.
 */

import { useEffect, useRef, useState } from "react";
import { API_BASE_URL, API_TIMEOUT_MS, WS_BASE_URL } from "../lib/constants";
import { fetchWithTimeout } from "../services/api";

// ── Shared stream types (exported — useSimulationStream re-exports these) ─────

export interface StreamEdge {
  edge_id: string;
  speed: number;
  vehicle_count: number;
  stopped_vehicles: number;
  congestion: string;
  congestion_score: number;
  edge_cost: number;
  base_cost: number;
  risk_score: number;
  model?: string;
  source?: string;
}

/** One live vehicle position, as broadcast by SimulationManager (real TraCI
 * data only — this array is empty whenever `source !== "sumo"`, since the
 * mock sensor path has no individual vehicles to report). */
export interface StreamVehicle {
  id: string;
  lat: number;
  lng: number;
  heading: number; // compass bearing, 0 = north, clockwise
  speed_kmh: number;
  edge_id: string;
}

/** A real, currently-active accident — see app/services/accident_service.py.
 * lat/lng are null only if the reported edge_id isn't found in the graph
 * (never a placeholder coordinate). */
export interface StreamAccident {
  accident_id: string;
  edge_id: string;
  severity: string;
  road_name: string;
  lat: number | null;
  lng: number | null;
  reported_at: string;
}

/** A real, currently-active emergency mission — see
 * app/emergency/mission_manager.py. Position and route geometry are both
 * real (interpolated along the real backend-computed route by real
 * elapsed simulation ticks), never invented on the frontend. */
export type MissionState =
  | "ambulance_dispatched"
  | "green_corridor_active"
  | "en_route_to_accident"
  | "ambulance_arrived"
  | "on_site_response"
  | "returning_to_hospital"
  | "emergency_completed";

export interface StreamMission {
  mission_id: string;
  accident_id: string;
  edge_id: string;
  hospital_name: string;
  ambulance_id: string;
  unit_number: string;
  state: MissionState;
  lat: number;
  lng: number;
  outbound_coords: { lat: number; lng: number }[];
  return_coords: { lat: number; lng: number }[] | null;
  signal_priority_available: boolean;
  // Ticks remaining in the on-site hold, driven by the backend's own
  // simulation tick counter — never a frontend setTimeout/wall clock.
  on_site_seconds_remaining: number | null;
}

export interface SimulationStreamPayload {
  type: string;
  simulation_id: string;
  status: string;
  tick: number;
  edges_updated: number;
  model?: string;
  source?: string;
  traffic: StreamEdge[];
  vehicles: StreamVehicle[];
  accidents: StreamAccident[];
  emergency_missions: StreamMission[];
  timestamp: string;
}

/** Step 3 — Map state keyed by SUMO edge_id → risk score [0, 1]. */
export type EdgeRiskMap = Record<string, number>;

// ── Throttle interval — state updates fire at most once per second ────────────
const UI_THROTTLE_MS = 1000;

// ── Reconnect back-off parameters ────────────────────────────────────────────
const RECONNECT_BASE_MS  = 1_000;
const RECONNECT_MAX_MS   = 30_000;

export interface UseTrafficSocketReturn {
  connected: boolean;
  riskByEdge: EdgeRiskMap;
  /** The full latest per-edge traffic snapshot (all StreamEdge fields, not
   * just risk) — for aggregate panels (KPI overview, congestion breakdown)
   * that need more than the map's paint-color value. Same 1s throttle as
   * riskByEdge/tick. */
  edges: StreamEdge[];
  vehicles: StreamVehicle[];
  accidents: StreamAccident[];
  missions: StreamMission[];
  tick: number | undefined;
  /** The real broadcast source for this tick — "sumo" when real TraCI is
   * connected, "mock" when SimulationManager is generating sensor data
   * itself (see app/core/simulation_manager.py). Undefined before the
   * first frame arrives. Never inferred from wsConnected — a mock-mode
   * WebSocket connects successfully too, so "connected" alone can't tell
   * these apart (see Header.tsx's connection badge). */
  dataSource: string | undefined;
}

/**
 * Connect to the FastAPI simulation WebSocket for `simulationId`.
 *
 * @param simulationId  The simulation to subscribe to (e.g. "anna-nagar-live").
 *                      Pass an empty string to stay disconnected.
 */
export function useTrafficSocket(simulationId: string): UseTrafficSocketReturn {
  const [connected, setConnected] = useState(false);
  const [riskByEdge, setRiskByEdge] = useState<EdgeRiskMap>({});
  const [edges, setEdges] = useState<StreamEdge[]>([]);
  const [vehicles, setVehicles] = useState<StreamVehicle[]>([]);
  const [accidents, setAccidents] = useState<StreamAccident[]>([]);
  const [missions, setMissions] = useState<StreamMission[]>([]);
  const [tick, setTick] = useState<number | undefined>(undefined);
  const [dataSource, setDataSource] = useState<string | undefined>(undefined);

  // Refs — never trigger re-renders, safe to read inside closures.
  const wsRef          = useRef<WebSocket | null>(null);
  const latestPayload  = useRef<SimulationStreamPayload | null>(null);
  const throttleTimer  = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedRef      = useRef(false);   // set to true on unmount → stops reconnect loop
  const loggedOnce     = useRef(false);

  useEffect(() => {
    if (!simulationId) return;

    closedRef.current = false;
    let reconnectDelay = RECONNECT_BASE_MS;

    // ── Step 2: State throttle ────────────────────────────────────────────────
    // Reads latestPayload.current once per second and triggers React state update.
    // WS messages never touch React state directly — only this interval does.
    const flush = () => {
      const payload = latestPayload.current;
      if (!payload) return;

      const next: EdgeRiskMap = {};
      for (const edge of payload.traffic) {
        next[edge.edge_id] = edge.risk_score;
      }
      setRiskByEdge(next);
      setEdges(payload.traffic);
      setVehicles(payload.vehicles ?? []);
      setAccidents(payload.accidents ?? []);
      setMissions(payload.emergency_missions ?? []);
      setTick(payload.tick);
      setDataSource(payload.source);
    };

    throttleTimer.current = setInterval(flush, UI_THROTTLE_MS);

    // ── Step 1: Socket connection with auto-reconnect ─────────────────────────
    const connect = () => {
      if (closedRef.current) return;

      const url = `${WS_BASE_URL}/realtime/${simulationId}`;
      const ws  = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (closedRef.current) { ws.close(); return; }
        setConnected(true);
        reconnectDelay = RECONNECT_BASE_MS; // reset back-off on successful connect
        console.info("[TRAFFIX WS] connected", url);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as SimulationStreamPayload;
          // Dev-mode diagnostic: log first good frame + 3 sample edges.
          if (!loggedOnce.current && payload.traffic?.length) {
            loggedOnce.current = true;
            console.log(
              "[TRAFFIX WS] first payload — source=%s model=%s tick=%d edges=%d",
              payload.source ?? "?",
              payload.model  ?? "?",
              payload.tick,
              payload.traffic.length,
            );
            console.log(
              "[TRAFFIX WS] sample edges",
              payload.traffic.slice(0, 3).map((e) => ({
                edge_id:      e.edge_id,
                risk_score:   e.risk_score,
                congestion:   e.congestion,
                model:        e.model ?? payload.model,
              })),
            );
          }
          latestPayload.current = payload;
        } catch (err) {
          console.warn("[TRAFFIX WS] failed to parse payload", err);
        }
      };

      ws.onerror = () => {
        setConnected(false);
        // onclose fires after onerror — reconnect logic lives there.
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (closedRef.current) return; // intentional unmount — do not reconnect

        // Exponential back-off reconnect
        if (closedRef.current) return;
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_MAX_MS);
          connect();
        }, reconnectDelay);
      };
    };

    // Kick off simulation then open WS.
    // Fire-and-forget: if the simulation is already running the POST is a no-op.
    // Timeout-protected (fetchWithTimeout) rather than a raw fetch() — this
    // call previously had no bound at all, so an unreachable backend (e.g.
    // the configured port occupied by an unrelated process that accepts
    // connections but never responds) would leave it pending forever and
    // connect() — which opens the real WebSocket — would never run at all.
    fetchWithTimeout(`${API_BASE_URL}/simulation/start`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        simulation_id: simulationId,
        config: {
          scenario_type:  "demand_spike",
          location:       "Anna Nagar",
          vehicle_density: 0.65,
          rainfall:        0.1,
        },
      }),
    }, API_TIMEOUT_MS).catch(() => {
      // Simulation start is optional; the socket still connects.
    }).finally(connect);

    // ── Cleanup on unmount ────────────────────────────────────────────────────
    return () => {
      closedRef.current = true;
      if (throttleTimer.current)  clearInterval(throttleTimer.current);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [simulationId]);

  return { connected, riskByEdge, edges, vehicles, accidents, missions, tick, dataSource };
}
