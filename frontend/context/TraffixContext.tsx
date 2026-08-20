"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { getWebSocketClient } from "@/services/webSocketClient";

interface TraffixContextValue {
  wsConnected: boolean;
  isMockFeed: boolean;
  wsStep: number;
  unreadAlerts: number;
  setUnreadAlerts: (n: number) => void;
}

const TraffixContext = createContext<TraffixContextValue>({
  wsConnected: false,
  isMockFeed: false,
  wsStep: 0,
  unreadAlerts: 5,
  setUnreadAlerts: () => {},
});

export function TraffixProvider({ children }: { children: ReactNode }) {
  const [wsConnected, setWsConnected] = useState(false);
  const [isMockFeed, setIsMockFeed] = useState(false);
  const [wsStep, setWsStep] = useState(0);
  const [unreadAlerts, setUnreadAlerts] = useState(5);

  useEffect(() => {
    const client = getWebSocketClient();

    const unsubStatus = client.on<{ connected: boolean; mock?: boolean }>(
      "connection_status",
      (msg) => {
        setWsConnected(msg.payload.connected);
        setIsMockFeed(!!msg.payload.mock);
      }
    );

    const unsubStep = client.on<{ step: number }>(
      "simulation_step",
      (msg) => setWsStep(msg.payload.step)
    );

    setWsConnected(client.isConnected);

    return () => {
      unsubStatus();
      unsubStep();
    };
  }, []);

  return (
    <TraffixContext.Provider
      value={{ wsConnected, isMockFeed, wsStep, unreadAlerts, setUnreadAlerts }}
    >
      {children}
    </TraffixContext.Provider>
  );
}

export function useTraffixContext() {
  return useContext(TraffixContext);
}
