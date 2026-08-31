"use client";

import { createContext, useContext, ReactNode } from "react";
import { useSimulationStream } from "@/hooks/useSimulationStream";
import type { EdgeRiskMap, StreamAccident, StreamEdge, StreamMission, StreamVehicle } from "@/hooks/useSimulationStream";
import { useLiveMessages } from "@/hooks/useLiveData";
import type { IntelligenceMessage } from "@/types/common";
import { MOCK_INITIAL_MESSAGES } from "@/lib/mockData";

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
 *
 * The intelligence-message feed also lives here now (previously local to
 * app/page.tsx) so the header's "unread" badge and /alerts page share the
 * exact same real event log the main page pushes into — instead of the
 * header showing a permanently-hardcoded "5" that never changed.
 */
interface TraffixContextValue {
  wsConnected: boolean;
  wsStep: number;
  /** The real broadcast source for the current tick — "sumo" | "mock" |
   * undefined (before the first frame). See hooks/useWebSocket.ts. Never
   * conflate this with wsConnected — a mock-mode stream connects fine too. */
  dataSource: string | undefined;
  riskByEdge: EdgeRiskMap;
  /** Full latest per-edge traffic snapshot — see hooks/useWebSocket.ts. */
  edges: StreamEdge[];
  vehicles: StreamVehicle[];
  /** Real, currently-active accidents — see app/services/accident_service.py. */
  accidents: StreamAccident[];
  /** Real, currently-active emergency missions — see app/emergency/mission_manager.py. */
  missions: StreamMission[];
  messages: IntelligenceMessage[];
  pushMessage: (msg: IntelligenceMessage) => void;
  acknowledgeMessage: (id: string) => void;
  dismissMessage: (id: string) => void;
  acknowledgeAllMessages: () => void;
  /** Real count of messages neither acknowledged nor dismissed — drives the
   * ALERTS nav badge. Never a hardcoded placeholder. */
  unreadAlerts: number;
}

const TraffixContext = createContext<TraffixContextValue>({
  wsConnected: false,
  wsStep: 0,
  dataSource: undefined,
  riskByEdge: {},
  edges: [],
  vehicles: [],
  accidents: [],
  missions: [],
  messages: [],
  pushMessage: () => {},
  acknowledgeMessage: () => {},
  dismissMessage: () => {},
  acknowledgeAllMessages: () => {},
  unreadAlerts: 0,
});

export function TraffixProvider({ children }: { children: ReactNode }) {
  const { connected, tick, dataSource, riskByEdge, edges, vehicles, accidents, missions } =
    useSimulationStream(true);
  const {
    messages,
    pushMessage,
    acknowledgeMessage,
    dismissMessage,
    acknowledgeAllMessages,
    unreadCount,
  } = useLiveMessages(MOCK_INITIAL_MESSAGES);

  return (
    <TraffixContext.Provider
      value={{
        wsConnected: connected,
        wsStep: tick ?? 0,
        dataSource,
        riskByEdge,
        edges,
        vehicles,
        accidents,
        missions,
        messages,
        pushMessage,
        acknowledgeMessage,
        dismissMessage,
        acknowledgeAllMessages,
        unreadAlerts: unreadCount,
      }}
    >
      {children}
    </TraffixContext.Provider>
  );
}

export function useTraffixContext() {
  return useContext(TraffixContext);
}
