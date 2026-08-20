import { WS_BASE_URL } from "../lib/constants";

// ── Event types from SUMO TraCI WebSocket feed ───────────────────────────────
export type WsEventType =
  | "traffic_update"
  | "incident_detected"
  | "signal_phase_change"
  | "vehicle_update"
  | "simulation_step"
  | "system_alert"
  | "connection_status";

export interface WsMessage<T = unknown> {
  type: WsEventType;
  timestamp: string;
  payload: T;
}

export type WsHandler<T = unknown> = (msg: WsMessage<T>) => void;

// ── WebSocket adapter ────────────────────────────────────────────────────────
export class TraffixWebSocket {
  private ws: WebSocket | null = null;
  private handlers = new Map<WsEventType, Set<WsHandler>>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 2000;
  private maxReconnectDelay = 30000;
  private intentionallyClosed = false;
  public isConnected = false;

  constructor(private endpoint: string = "/traci") {}

  // ── Connect ────────────────────────────────────────────────────────────────
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const url = `${WS_BASE_URL}${this.endpoint}`;
    this.intentionallyClosed = false;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectDelay = 2000;
        this.emit("connection_status", { connected: true });
        console.info("[TRAFFIX WS] Connected to", url);
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WsMessage;
          this.dispatch(msg);
        } catch {
          console.warn("[TRAFFIX WS] Failed to parse message:", event.data);
        }
      };

      this.ws.onerror = () => {
        console.warn("[TRAFFIX WS] Connection error — falling back to mock mode");
        this.isConnected = false;
        this.emit("connection_status", { connected: false });
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        if (!this.intentionallyClosed) {
          this.scheduleReconnect();
        }
      };
    } catch {
      console.warn("[TRAFFIX WS] WebSocket not available in this environment");
      this.startMockFeed();
    }
  }

  // ── Reconnect ──────────────────────────────────────────────────────────────
  private scheduleReconnect(): void {
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 1.5,
        this.maxReconnectDelay
      );
      this.connect();
    }, this.reconnectDelay);
  }

  // ── Mock feed (used when WebSocket unavailable) ──────────────────────────
  private mockInterval: ReturnType<typeof setInterval> | null = null;

  private startMockFeed(): void {
    this.isConnected = true;
    this.emit("connection_status", { connected: true, mock: true });

    let step = 420;
    this.mockInterval = setInterval(() => {
      step++;
      this.dispatch({
        type: "simulation_step",
        timestamp: new Date().toISOString(),
        payload: { step, vehicleCount: 347 + Math.floor(Math.random() * 20) - 10 },
      });

      // Occasionally emit traffic update
      if (step % 5 === 0) {
        this.dispatch({
          type: "traffic_update",
          timestamp: new Date().toISOString(),
          payload: {
            roadId: "road_anna_2",
            density: 73 + Math.floor(Math.random() * 6) - 3,
            avgSpeed: 22 + Math.floor(Math.random() * 4) - 2,
          },
        });
      }
    }, 1000);
  }

  // ── Subscribe ──────────────────────────────────────────────────────────────
  on<T>(event: WsEventType, handler: WsHandler<T>): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler as WsHandler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(event)?.delete(handler as WsHandler);
    };
  }

  // ── Dispatch ───────────────────────────────────────────────────────────────
  private dispatch(msg: WsMessage): void {
    this.handlers.get(msg.type)?.forEach((h) => h(msg));
  }

  // ── Emit (for internal / mock events) ─────────────────────────────────────
  private emit(type: WsEventType, payload: unknown): void {
    this.dispatch({ type, timestamp: new Date().toISOString(), payload });
  }

  // ── Send ───────────────────────────────────────────────────────────────────
  send(type: WsEventType, payload: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  // ── Disconnect ─────────────────────────────────────────────────────────────
  disconnect(): void {
    this.intentionallyClosed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.mockInterval) clearInterval(this.mockInterval);
    this.ws?.close();
    this.ws = null;
    this.isConnected = false;
  }
}

// ── Singleton instance ────────────────────────────────────────────────────────
let _instance: TraffixWebSocket | null = null;

export function getWebSocketClient(): TraffixWebSocket {
  if (!_instance) {
    _instance = new TraffixWebSocket("/traci");
  }
  return _instance;
}
