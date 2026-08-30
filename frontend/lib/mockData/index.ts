import { IntelligenceMessage } from "../../types/common";

/* -------------------------------------------------------------------------- */
/*  Seed data — shown only until the first real message arrives; everything  */
/*  else the app renders comes from the real backend. See hooks/useLiveData.ts */
/* -------------------------------------------------------------------------- */

// Deliberately makes no specific factual claim (no vehicle counts, no named
// roads) — it's shown for the brief moment before the first real message
// (backend health check / WebSocket connect, see app/page.tsx) arrives and
// replaces it.
export const MOCK_INITIAL_MESSAGES: IntelligenceMessage[] = [
  {
    id: "msg-1",
    timestamp: "--:--:--",
    type: "system",
    text: "TRAFFIX Engine Initializing",
    details: "Establishing connection to the live simulation stream…",
  },
];
