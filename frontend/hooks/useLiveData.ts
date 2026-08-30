"use client";

import { useState, useEffect, useCallback } from "react";
import type { StreamEdge } from "./useWebSocket";
import { computeTrafficAggregates, TrafficAggregates } from "../lib/trafficAggregates";

// ── Live KPI hook — computed from the real WebSocket edge stream ─────────────
// Previously polled a /traffic/kpi REST endpoint that never existed on the
// backend and silently fell back to hardcoded numbers. There's no need for
// a dedicated aggregate endpoint at all: the real per-edge snapshot is
// already pushed to the client every second (see TraffixContext.tsx /
// hooks/useWebSocket.ts) — this just derives the network-wide KPIs and
// congestion breakdown from it (lib/trafficAggregates.ts), so the panel
// updates exactly as often as the backend actually pushes new data.
export function useLiveKpi(edges: StreamEdge[]) {
  const [kpi, setKpi] = useState<TrafficAggregates>(() => computeTrafficAggregates(edges));

  useEffect(() => {
    setKpi(computeTrafficAggregates(edges));
  }, [edges]);

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

  // Real acknowledge/dismiss state, driven by an actual user action (the
  // /alerts page) — powers both that page and the header's unread badge
  // from the same real event log, instead of two separate fake counts.
  const acknowledgeMessage = useCallback((id: string) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, acknowledged: true } : m)));
  }, []);

  const dismissMessage = useCallback((id: string) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, dismissed: true } : m)));
  }, []);

  const acknowledgeAllMessages = useCallback(() => {
    setMessages((prev) => prev.map((m) => ({ ...m, acknowledged: true })));
  }, []);

  const unreadCount = messages.filter((m) => !m.acknowledged && !m.dismissed).length;

  return {
    messages,
    setMessages,
    pushMessage,
    acknowledgeMessage,
    dismissMessage,
    acknowledgeAllMessages,
    unreadCount,
  };
}
