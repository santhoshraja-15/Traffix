"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { useSimulationStream } from "@/hooks/useSimulationStream";
import type { EdgeRiskMap, StreamEdge, StreamVehicle } from "@/hooks/useSimulationStream";

/**
 * App-wide WebSocket connection — established exactly once here, per
 * TECHNICAL_DEEP_DIVE.md §5 ("one connection, established once, e.g. in a
 * context/provider, not re-created per component mount").
 *
 * Previously this provider ran its own *separate* WebSocket client
 * (services/webSocketClient.ts) that connected to a nonexistent "/traci"
 * endpoint and silently fell back to a fabricated mock data feed — while
 * the map page opened a second, real connection to the actual backend via
 * useSimulationStream. That's now retired: this is the one real connection
 * for the whole app, and every consumer (map page, simulation page,
 * IoT/prediction panels, the header/status badges) reads from here instead
 * of each opening — or worse, faking — their own.
 */
interface TraffixContextValue {
  wsConnected: boolean;
  wsStep: number;
  riskByEdge: EdgeRiskMap;
  /** Full latest per-edge traffic snapshot — see hooks/useWebSocket.ts. */
  edges: StreamEdge[];
  vehicles: StreamVehicle[];
  unreadAlerts: number;
  setUnreadAlerts: (n: number) => void;
}

const TraffixContext = createContext<TraffixContextValue>({
  wsConnected: false,
  wsStep: 0,
  riskByEdge: {},
  edges: [],
  vehicles: [],
  unreadAlerts: 5,
  setUnreadAlerts: () => {},
});

export function TraffixProvider({ children }: { children: ReactNode }) {
  const { connected, tick, riskByEdge, edges, vehicles } = useSimulationStream(true);
  const [unreadAlerts, setUnreadAlerts] = useState(5);

  return (
    <TraffixContext.Provider
      value={{
        wsConnected: connected,
        wsStep: tick ?? 0,
        riskByEdge,
        edges,
        vehicles,
        unreadAlerts,
        setUnreadAlerts,
      }}
    >
      {children}
    </TraffixContext.Provider>
  );
}

export function useTraffixContext() {
  return useContext(TraffixContext);
}
