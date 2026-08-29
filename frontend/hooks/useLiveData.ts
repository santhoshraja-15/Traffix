"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchNetworkKpi, NetworkKpi } from "../services/trafficApi";

// ── Live KPI hook — REST baseline + polling ───────────────────────────────────
// Previously also merged in delta updates from services/webSocketClient.ts, a
// second WebSocket client that connected to a nonexistent endpoint and
// silently fabricated data when it failed. That client has been retired
// (see TraffixContext.tsx) — this hook is now honestly what it does: a
// polled REST fetch. Live per-edge data flows through the real socket via
// useTraffixContext()/useSimulationStream instead.
export function useLiveKpi(pollingIntervalMs = 5000, enabled = true) {
  const [kpi, setKpi] = useState<NetworkKpi>({
    activeVehicles: 1247,
    avgSpeedKmh: 34.2,
    networkHealthPct: 88,
    activeIncidents: 0,
    throughputVehPerHr: 1820,
    congestionIndex: 0.62,
  });

  // Initial REST fetch
  useEffect(() => {
    if (!enabled) return;
    fetchNetworkKpi().then(setKpi).catch(() => {/* use default */});
  }, [enabled]);

  // Polling REST fallback
  useEffect(() => {
    if (!enabled) return;
    const interval = setInterval(() => {
      fetchNetworkKpi().then(setKpi).catch(() => {/* keep last */});
    }, pollingIntervalMs);
    return () => clearInterval(interval);
  }, [pollingIntervalMs, enabled]);

  return { kpi, setKpi };
}

// ── Live message feed hook ────────────────────────────────────────────────────
// Previously also subscribed to a fabricated "system_alert" WS event from the
// retired legacy client. The backend doesn't broadcast any alert/event stream
// today (see FRONTEND_AUDIT.md §1.2) — messages are pushed explicitly by
// real client-side events (e.g. route search, accident simulation) via
// pushMessage() until a real backend event stream exists to wire up here.
import { IntelligenceMessage } from "../types/common";

export function useLiveMessages(initial: IntelligenceMessage[]) {
  const [messages, setMessages] = useState<IntelligenceMessage[]>(initial);

  const pushMessage = useCallback((msg: IntelligenceMessage) => {
    setMessages((prev) => [msg, ...prev].slice(0, 50));
  }, []);

  return { messages, setMessages, pushMessage };
}
