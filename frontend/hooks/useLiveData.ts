"use client";

import { useState, useEffect, useCallback } from "react";
import { getWebSocketClient } from "../services/webSocketClient";
import { fetchNetworkKpi, NetworkKpi } from "../services/trafficApi";

// ── Live KPI hook — merges REST baseline + WS delta updates ──────────────────
export function useLiveKpi(pollingIntervalMs = 5000) {
  const [kpi, setKpi] = useState<NetworkKpi>({
    activeVehicles: 1247,
    avgSpeedKmh: 34.2,
    networkHealthPct: 88,
    activeIncidents: 0,
    throughputVehPerHr: 1820,
    congestionIndex: 0.62,
  });
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStep, setWsStep] = useState<number | undefined>(undefined);
  const [isMockFeed, setIsMockFeed] = useState(false);

  // Initial REST fetch
  useEffect(() => {
    fetchNetworkKpi().then(setKpi).catch(() => {/* use default */});
  }, []);

  // Polling REST fallback
  useEffect(() => {
    const interval = setInterval(() => {
      fetchNetworkKpi().then(setKpi).catch(() => {/* keep last */});
    }, pollingIntervalMs);
    return () => clearInterval(interval);
  }, [pollingIntervalMs]);

  // WebSocket live updates
  useEffect(() => {
    const client = getWebSocketClient();
    client.connect();

    const unsubStatus = client.on<{ connected: boolean; mock?: boolean }>(
      "connection_status",
      (msg) => {
        setWsConnected(msg.payload.connected);
        setIsMockFeed(!!msg.payload.mock);
      }
    );

    const unsubStep = client.on<{ step: number; vehicleCount: number }>(
      "simulation_step",
      (msg) => {
        setWsStep(msg.payload.step);
        setKpi((prev) => ({
          ...prev,
          activeVehicles: msg.payload.vehicleCount,
        }));
      }
    );

    const unsubTraffic = client.on<{
      roadId: string;
      density: number;
      avgSpeed: number;
    }>("traffic_update", (msg) => {
      setKpi((prev) => ({
        ...prev,
        avgSpeedKmh: parseFloat(
          ((prev.avgSpeedKmh * 0.8 + msg.payload.avgSpeed * 0.2)).toFixed(1)
        ),
        congestionIndex: parseFloat(
          (msg.payload.density / 100).toFixed(2)
        ),
        networkHealthPct: Math.max(
          50,
          Math.round(100 - msg.payload.density * 0.5)
        ),
      }));
    });

    setWsConnected(client.isConnected);

    return () => {
      unsubStatus();
      unsubStep();
      unsubTraffic();
    };
  }, []);

  return { kpi, wsConnected, wsStep, isMockFeed, setKpi };
}

// ── Live message feed hook — appends WS system_alert events ──────────────────
import { IntelligenceMessage } from "../types/common";

export function useLiveMessages(initial: IntelligenceMessage[]) {
  const [messages, setMessages] = useState<IntelligenceMessage[]>(initial);

  useEffect(() => {
    const client = getWebSocketClient();

    const unsub = client.on<{
      severity: string;
      text: string;
      details?: string;
    }>("system_alert", (msg) => {
      const newMsg: IntelligenceMessage = {
        id: `ws-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString("en-IN", { hour12: false }),
        type:
          msg.payload.severity === "critical"
            ? "emergency"
            : msg.payload.severity === "warning"
            ? "warning"
            : "info",
        text: msg.payload.text,
        details: msg.payload.details,
        urgent: msg.payload.severity === "critical",
      };
      setMessages((prev) => [newMsg, ...prev].slice(0, 50));
    });

    return () => unsub();
  }, []);

  const pushMessage = useCallback((msg: IntelligenceMessage) => {
    setMessages((prev) => [msg, ...prev].slice(0, 50));
  }, []);

  return { messages, setMessages, pushMessage };
}
