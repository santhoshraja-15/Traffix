# FRONTEND_AUDIT.md — TRAFFICX Phase 0 Repository Audit

Branch: `frontend-rebuild` (created off `main`; this whole repair effort stays off `main` per user instruction). No code was changed to produce this document — read-only inspection only, per `BUILD_INSTRUCTIONS.md` Phase 0.

---

## 0. Executive summary

The backend (FastAPI + SUMO/TraCI + XGBoost) is real and partially wired, but **the routing/graph layer it actually serves from is a synthetic mock grid, not the real Anna Nagar SUMO network** — and the frontend independently hardcodes the *same* fake grid rather than ever fetching real topology. The emergency subsystem (accidents/ambulance/green corridor) has real, reasonably complete logic in `app/emergency/` and `app/services/`, but the **API endpoints the frontend calls bypass that logic entirely** and return hardcoded stub data. The frontend has two parallel, conflicting WebSocket clients — one correct and wired to the real backend stream, one legacy client that silently fabricates a mock data feed and is still used by the app-wide connection-status context. The main page's search/reroute flows are scripted `setTimeout` theater with canned text, falling back to bundled mock data whenever a real call fails. None of this is a frontend-only problem — several of the required fixes are backend gaps that need the smallest-possible additive change per `MASTER_PROMPT.md`.

This explains the "improperly connected to backend, misinterprets data, produces errors" framing in `PRD.md` §4 precisely — and gives a concrete list of what to repair phase by phase.

---

## 1. Backend — actual API & WebSocket contract (as implemented)

Framework: FastAPI (`app/main.py`), routers aggregated in `app/api/routes.py` under prefix `/api`. CORS allows `localhost:3000`/`127.0.0.1:3000` (any port) only.

### 1.1 REST endpoints (real, as implemented — not assumed)

| Method | Path | Backed by | Real or stub? |
|---|---|---|---|
| GET | `/` | `app/main.py` | Real — `{message, docs}` |
| GET | `/health` | `app/main.py` | Real — `{status, app, version}` |
| GET | `/api/network/topology` | `app/api/network.py` → `RoadNetworkGraph.to_geojson()` | **Runs, but returns fake mock-grid geometry** (§2) |
| POST | `/api/routes` | `app/api/navigation.py` → `RoutingService` | **Runs, but routes only over the fake mock grid** (§2). Accepts `source_node_id`/`destination_node_id` OR raw `source.lat/lng`/`destination.lat/lng` (auto-snapped via Haversine nearest-node, 50 km out-of-bounds guard → HTTP 400). Returns up to N `CandidateRoute` (route_id, rank, travel_time, distance, traffic_level, congestion_level, edges, coords). |
| GET | `/api/traffic/{edge_id}` | `app/api/traffic.py` | **Stub** — always returns the same hardcoded `speed=32.5, vehicle_count=48, congestion=MODERATE` regardless of `edge_id`. |
| WS | `/api/realtime/{simulation_id}` | `app/api/traffic.py` + `app/core/websocket_manager.py` | Real — see §1.2 |
| POST | `/api/accidents` | `app/api/accidents.py` | **Stub** — echoes the request back as an `AccidentReport` with a new UUID; never calls `AccidentManager`/`emergency_routing.handle_accident`. No ambulance dispatch is triggered by this endpoint. |
| POST | `/api/ambulance/dispatch` | `app/api/ambulance.py` | **Stub** — always returns `route_edges=["edge-0","edge-1","edge-2"]`, `eta_seconds=420`, `green_corridor_active=True` regardless of input. Never calls `AmbulanceDispatcher`/`AmbulanceManager`/`GreenCorridor`. |
| POST | `/api/simulation/start` | `app/api/simulation.py` | Real — starts `SimulationManager`'s per-second tick loop for a `simulation_id`. |
| POST | `/api/simulation/stop/{id}` | same | Real |
| POST | `/api/simulation/scenario` | same | Stub-ish — always targets "most recently started" simulation, doesn't actually mutate scenario mid-run |
| GET | `/api/simulation/status/{id}` | same | Real for known IDs; fabricates a plausible fallback (`active_vehicles: 120`) for unknown IDs instead of 404 ("hackathon-friendly fallback" per its own comment) |
| — | `/api/analysis/*` | `app/api/analysis.py` | Not yet audited in detail |

Frontend-consumed endpoints that **do not exist on the backend at all** (found via frontend service-layer inspection, §3): `POST /navigation/route`, `POST /navigation/reroute`, `POST /navigation/risk-eval`, `POST /navigation/resolve-location`, `POST /accidents/create`. Every one of these frontend calls will 404 and fall through to bundled mock data (see §3.2).

### 1.2 WebSocket contract (real, as implemented)

- URL: `ws://<host>/api/realtime/{simulation_id}`
- Lifecycle: client connects → accepted & registered in `WebSocketManager` (per-`simulation_id` broadcast set) → server-driven only (client's `receive_text()` loop just keeps the socket open; the socket never expects the client to send data) → clean removal on disconnect.
- Broadcast cadence: **once per second**, driven by `SimulationManager._run_simulation_loop`, identical payload fanned out to every subscriber for that `simulation_id` (no per-client drift).
- **Actual payload shape** (this is the literal contract — build frontend types from this, not from `TECH_STACK_AND_REQUIREMENTS.md`'s guessed type list):

```jsonc
{
  "type": "traffic",
  "simulation_id": "anna-nagar-live",
  "status": "running",
  "tick": 42,
  "edges_updated": 36,
  "model": "v15_xgboost" | "v16_xgboost",
  "source": "sumo" | "mock",
  "timestamp": "2026-...Z",
  "traffic": [
    {
      "type": "traffic",
      "edge_id": "n0_0->n0_1",
      "speed": 32.5,
      "vehicle_count": 12,
      "congestion": "MODERATE",       // free_flow|light|moderate|heavy|severe
      "congestion_score": 0.41,
      "edge_cost": 12.3,
      "base_cost": 22.5,
      "risk_score": 0.41,
      "model": "v15_xgboost",
      "source": "sumo"
    }
    // ...one entry per edge in the graph (currently: the 60-edge mock grid, not real SUMO edges)
  ]
}
```

- **What is NOT in this payload, at all**: individual vehicle positions/IDs/headings, accident/incident state, ambulance/emergency state, green-corridor state, traffic-signal state, simulation clock in a usable "1 sim-minute" form. None of this is broadcast today. This is the single biggest gap against `MASTER_PROMPT.md`'s requirements (live vehicle markers, accident detection, the whole 8-state emergency lifecycle) — building any of those features means extending this payload (or adding new WS event types) on the backend first, per "if required backend support is missing."

### 1.3 The core integration bug: routing graph is a fake grid, not the real SUMO network

`app/routing/graph_manager.py::RoadNetworkGraph.initialize_graph()` builds a **synthetic 6×6 grid** — node IDs `n{row}_{col}`, origin `(13.0850, 80.2101)`, constant `0.0022°` lat/lng steps, 250 m edges, capacity 120. This mock graph is the sole thing behind `/api/network/topology` and `/api/routes` (via `RoutingService`), and the sole thing `app/emergency/*` (green corridor, ambulance dispatch) computes shortest paths over. **Nothing under `app/` parses the real SUMO network file** (`2026-08-19-23-26-46/osm.net.xml.gz`, or the per-scenario copies under `scenarios/*/osm.net.xml.gz`) — confirmed by grepping the entire `app/` tree for `sumolib`/`net.xml`/`parseNetwork`: zero matches.

Consequences:
- The map, when eventually wired to `/api/network/topology`, would show a fake orthogonal grid, not Anna Nagar's real road geometry — the opposite of `MASTER_PROMPT.md`'s "never hand-draw Anna Nagar roads."
- FROM/TO routing (`/api/routes`) computes paths on the fake grid, so returned routes, ETA, and distance are meaningless relative to the real network, even though the computation pipeline (Dijkstra + ML-weighted costs) itself is legitimate.
- **Even when SUMO/TraCI is actually running**, `SimulationManager._apply_sumo_metrics_to_graph()` tries to match real TraCI edge IDs (OSM-derived, e.g. `"23144855#2"`-style) against the mock grid's `edge_id` values (`"n0_0->n0_1"`-style). These never match, so real per-edge SUMO metrics are silently dropped and never reach the graph or the broadcast payload for that edge — real SUMO data effectively can't reach the current graph/broadcast pipeline as wired. (V15 risk *scores* are computed correctly from real TraCI data upstream in the tick loop, but then looked up by the mock grid's edge IDs when building the broadcast — same mismatch, so they don't surface either.)
- This is very likely fixable with a **smallest-possible additive backend change**: load the real network once via `sumolib.net.readNet()` (SUMO's own Python netiface library, already a TraCI/SUMO-install dependency) — build `RoadNetworkGraph` nodes/edges from real SUMO edge IDs and junction coordinates, converting SUMO's internal projected X/Y to lon/lat via the network object's own `convertXY2LonLat()` (never a hand-guessed offset, exactly as `TECHNICAL_DEEP_DIVE.md` §4 requires). This is a candidate to propose explicitly before Phase 3 (map repair) begins, since Phase 3 cannot honestly satisfy "real Anna Nagar SUMO network geometry" otherwise.

### 1.4 The emergency subsystem exists but is disconnected from the API

`app/emergency/` contains real, non-trivial logic:
- `accident_manager.py` — in-memory `AccidentRecord` store (report/resolve/query).
- `ambulance_manager.py` — in-memory fleet of 3 seeded ambulances (`AMB-001..003`) at mock-grid nodes `n0_0`, `n2_3`, `n5_5`, with status `available|dispatched|at_scene|returning`.
- `ambulance_dispatcher.py` — picks nearest available unit by Dijkstra hop count.
- `green_corridor.py` — temporarily multiplies edge weights by 0.1 along the dispatch path, restores on deactivate.
- `emergency_routing.py::handle_accident()` — orchestrates all of the above into one call: report → dispatch → activate corridor.
- `emergency_events.py` + `app/core/event_manager.py` — a typed event-name/dataclass scaffold and a working in-process pub/sub bus, but **nothing anywhere calls `event_manager.publish(...)` or `event_manager.subscribe(...)`** — this bus and the emergency event types are entirely unused dead scaffolding today.
- `app/services/accident_service.py` and `app/services/ambulance_service.py` correctly wrap the above for API consumption (`report_accident` → `emergency_routing.handle_accident`, `complete_mission` → deactivate corridor + free the unit, etc.).

**But** `app/api/accidents.py` and `app/api/ambulance.py` (the only accident/ambulance endpoints that exist) import directly from `app.models.*` and never import `AccidentService`/`AmbulanceService` at all — they're stub handlers, not wired to any of the real logic above. There's also no background driver anywhere that:
- automatically detects a SUMO/TraCI-reported collision and calls `handle_accident()`,
- moves a dispatched ambulance along its route tick-by-tick,
- times a 1-simulated-minute on-site hold from the SUMO clock,
- calls `complete_mission()` on return, or
- broadcasts any of this over the WebSocket.

All of that is genuinely missing, not just "unwired" — implementing the full 8-state lifecycle from `MASTER_PROMPT.md` (Phase 8) will mean: (a) wiring the real endpoints to `AccidentService`/`AmbulanceService`, (b) adding the missing automatic-detection + tick-driven ambulance-movement + SUMO-clock-timed hold + broadcast logic, all as additive backend work, flagged for approval before building.

### 1.5 SUMO / TraCI — what's actually available

- Real network files exist: `2026-08-19-23-26-46/osm.net.xml.gz` (+ `.poly.xml.gz`, `.sumocfg`) and per-density copies under `scenarios/{low,medium,high,congested}/`. `app/integrations/sumo_bridge.py`'s `SumoBridge.connect()` currently hardcodes `scenarios/medium/traffic.sumocfg` as the config to launch — the other scenario configs are present but unused by the running bridge.
- `SumoBridge` (real, TraCI-backed, thread-affinity-correct via a dedicated 1-worker executor) currently exposes **only edge-level aggregates per tick**: `vehicle_count`, `average_speed_kmh`, `stopped_vehicles`, `average_waiting_time`, `density_veh_per_km`, `queue_length_estimate_m`, `road_length_m` — computed by iterating `traci.vehicle.getIDList()` and bucketing by `traci.vehicle.getRoadID(vid)`. It does **not** currently expose individual vehicle position/heading/ID, nor junction/traffic-light state, nor simulation clock/time, nor any collision/incident signal from TraCI — none of `traci.simulation.getCollidingVehiclesIDList()` (or similar), `traci.simulation.getTime()`, `traci.trafficlight.*`, or per-vehicle `getPosition()`/`getAngle()` are called anywhere in the codebase. All of these are legitimately obtainable from TraCI (SUMO supports every one of them) — they're just not yet surfaced, which is exactly the "smallest possible additive backend change" scenario `MASTER_PROMPT.md` anticipates for: live vehicle markers, the SUMO-clock-timed 1-minute hold, and automatic accident detection.
- SUMO connection is graceful-degrading: if `traci` isn't importable or `connect()` fails, `app.state.sumo_bridge = None` and the tick loop falls back to `_mutate_edge_sensor_data()` (randomized jitter over the mock grid) — the server always starts either way, and the broadcast payload's `source` field (`"sumo"` vs `"mock"`) honestly reflects which path is live. This part is already correct and worth preserving as-is.
- Coordinate system: confirmed **no SUMO XY→lon/lat conversion exists anywhere** in `app/` (see §1.3). `app/utils/geo.py` only has Haversine distance, bearing, and linear-interpolation helpers that assume inputs are *already* WGS84 lat/lng — it does not touch SUMO's internal network projection at all.

---

## 2. Frontend — actual structure & findings

Next.js **16.3.1** (a version newer than this assistant's training data — `frontend/AGENTS.md` explicitly warns of breaking API changes and points at `node_modules/next/dist/docs/` as the source of truth; must be consulted before touching Next.js-specific code in Phase 1), React 19.2, TypeScript, Tailwind v4, Mapbox GL JS 3.29, no dedicated state library (plain hooks/context — consistent with `TECH_STACK_AND_REQUIREMENTS.md` §2). Package manager: npm (`package-lock.json` present under `frontend/`).

### 2.1 Env config

`frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api
NEXT_PUBLIC_API_ORIGIN=http://localhost:8000
NEXT_PUBLIC_MAP_TOKEN=pk.eyJ1...example_token
```
The Mapbox token is a **placeholder ending in the literal string `example_token`**, and `TrafficMap.tsx` explicitly checks for and rejects that exact substring (`!token.includes("example_token")`) before enabling real Mapbox rendering. So today, with the checked-in env file as-is, the app **always** runs in its no-Mapbox SVG fallback mode (§2.3) — a real token needs to be supplied for the actual map library to ever activate. This needs a real token from the user before Phase 3 can be verified visually.

Root-level `.env.example` (for the Python backend) lists `MAPBOX_TOKEN` too (unused by any backend code found so far — likely leftover/aspirational) plus `SUMO_HOME`/`SUMO_BINARY`/`SUMO_CONFIG`/`MODEL_PATH`/`GEMINI_API_KEY`, none of which are read by `app/utils/config.py` as far as inspected yet — worth double-checking in Phase 1.

Stray untracked items at repo root (not part of `frontend/`, pre-existing before this session, left alone): `package.json`/`package-lock.json` (a placeholder Node manifest with no dependencies, just descriptive metadata) and `myenv/` (an apparent duplicate Python venv alongside the tracked `.venv/`). Flagging for awareness, not touching without separate approval.

### 2.2 Duplicate/conflicting WebSocket layers — the concrete Phase 2 target

Two independent WebSocket clients exist and are **both actively used**, disagreeing with each other and with the real backend contract:

**A. `hooks/useWebSocket.ts` (`useTrafficSocket`) — correct, real, well-built.**
Connects to `${WS_BASE_URL}/realtime/${simulationId}` (matches §1.2 exactly), typed to the real payload (`StreamEdge`/`SimulationStreamPayload` match the actual JSON), throttles React state updates to 1 Hz via a ref + interval (avoids per-message re-renders), exponential-backoff reconnect (1s→30s, cap), clean unmount teardown. Re-exported unchanged as `useSimulationStream` (`hooks/useSimulationStream.ts`) which just pins `simulationId` to `DEMO_SIMULATION_ID`. This is the piece to standardize on and build outward from.

**B. `services/webSocketClient.ts` (`TraffixWebSocket`/`getWebSocketClient()`) — legacy, wrong contract, fabricates data.**
Connects to `${WS_BASE_URL}/traci` — **an endpoint that does not exist on the backend at all** (only `/realtime/{simulation_id}` exists). Event schema (`incident_detected`, `vehicle_update`, `signal_phase_change`, etc.) matches nothing the backend actually sends. Critically, its `connect()` catch-block and `onerror` path call `startMockFeed()`, which **fabricates a fake `simulation_step`/`traffic_update` feed on a `setInterval`, sets `isConnected = true`, and emits `connection_status: {connected: true, mock: true}`** — i.e. it silently and indefinitely impersonates a live connection. This is a direct violation of `FLOW.md`'s "do not build a separate mock-mode UI path that could be mistaken for this real one" and of `MASTER_PROMPT.md`'s "never fabricate."

This legacy client is still wired into production UI state in three places:
- `frontend/context/TraffixContext.tsx` (`TraffixProvider`, mounted app-wide in `app/layout.tsx`) — sources `wsConnected`/`isMockFeed`/`wsStep` from client B only.
- `frontend/hooks/useLiveData.ts` (`useLiveKpi`, `useLiveMessages`) — sources live KPI deltas and the message feed from client B's fake event types.
- `frontend/app/page.tsx` — merges both: `systemConnected={simConnected || wsConnected}` in the header, meaning **the header's "LIVE — CONNECTED" indicator can read connected purely from the fake mock feed even if the real backend/WebSocket (`simConnected`, client A) is down** — a concrete, demonstrable status-indicator bug matching `TECHNICAL_DEEP_DIVE.md` §5's reconnection requirements almost exactly backwards.

Phase 2 (WebSocket rework) should standardize the whole app on client A (`useTrafficSocket`/`useSimulationStream`), retire client B and its mock feed, and re-point `TraffixContext`/`useLiveData` at real data or remove them if genuinely redundant once consolidated — flagging per the error-correction protocol since this touches architecture/socket-contract assumptions, not a typo-level fix.

`frontend/lib/websocket.ts` is an empty stub (`// TODO: implement`) — dead file, not used by anything (no imports found).

### 2.3 Map: hardcoded fake topology, never fetches the real (or even the backend's fake) network

`components/map/TrafficMap.tsx` imports `ANNA_NAGAR_TOPOLOGY` from `frontend/lib/annaNagarTopology.ts` and uses it unconditionally as the map's road network. That file **independently reconstructs the exact same synthetic 6×6 grid** as the backend's mock graph (same origin `13.085, 80.2101`, same `0.0022°` steps) — a second, frontend-side hand-authored fake network. `services/networkApi.ts::fetchNetworkTopology()` (which calls the real `/api/network/topology`) exists but **`TrafficMap.tsx` never calls it** — there's no `useEffect` anywhere invoking it. So today the map's road geometry is 100% hardcoded on the client, independent of both backend reality and even backend fakery.

Layered on top of that:
- If `NEXT_PUBLIC_MAP_TOKEN` doesn't look like a real Mapbox token (true today, see §2.1), Mapbox never initializes, and the component instead draws a **hand-rolled dark SVG grid background** plus the topology projected into an arbitrary `1000×720` SVG viewbox via `projectToViewBox` — a second, entirely separate rendering path from the Mapbox one, both driven by the same fake data.
- In that no-token fallback mode, `VehicleLayer`, `TrafficSignals`, `AccidentZone`/`RippleEffect`, `AmbulanceLayer`, `HospitalLayer` are rendered at **hardcoded absolute pixel offsets** (`left-[280px] top-[200px]`, `left-[480px] top-[140px]`, `left-[650px] top-[220px]`, etc.) — not derived from any coordinate, real or fake. `VehicleLayer`/`TrafficSignals` are fed `trafficSnapshot = MOCK_TRAFFIC_SNAPSHOT` by default (imported straight from `lib/mockData`), so in this mode the app is, quite literally, presenting canned fake vehicles/signals as if live.
- The one genuinely real piece here is `riskByEdge` (from client A, §2.2) — it's correctly threaded into both the Mapbox line-paint expression and the SVG stroke color, so per-edge risk *would* be real once the topology it's painted onto is real. That data-flow wiring is worth preserving.

This is the central Phase 3 problem: get `fetchNetworkTopology()` actually called and rendered (once the backend serves real geometry per §1.3), and retire `annaNagarTopology.ts` and the pixel-hardcoded overlay layers.

### 2.4 Main page (`app/page.tsx`) — scripted fake flows over real plumbing

- `handleSearch()` never calls the real routing endpoint until after three chained `setTimeout`s (600ms/1200ms/1800ms) that push **hardcoded, pre-written status messages** into the live message feed — `"Shortest topological route found: 4.2 km (~12 min)"`, `"Topological shortest path calculated via Anna Salai Direct."` — regardless of what the backend will actually return. This is scripted theater, not derived from any real intermediate backend response. The final `calculateRoutes()` call (see §2.5) does hit a real-looking service function, but that function itself calls a **nonexistent** endpoint (`POST /navigation/route`) and silently falls back to `MOCK_ROUTE_SEARCH_RESULT` on failure — which, given §1.1, is what happens on every single search today.
- `handleSimulateAccident()` calls `simulateAccident()` (§2.5, also hits a nonexistent endpoint and falls back to a hardcoded canned accident at a fixed lat/lng "Anna Salai (Teynampet Junction)"), then — independent of whatever `simulateAccident` returned — replaces the entire route list with a **hardcoded reshuffle of `MOCK_ROUTES`** and a canned reasoning string ("Bypasses severe accident at Teynampet Junction via Mount Flyover") after another `setTimeout(1000)`. None of this reflects any real backend rerouting event, directly contradicting `FLOW.md`'s accident/emergency flow and `ANIMATED_EFFECTS.md` §3's "only triggered by a real backend rerouting event."
- `routes`/`selectedRoute` state is seeded from `MOCK_ROUTES` (`lib/mockData`) at mount and stays that way until a search succeeds — i.e., the route panel shows fabricated data by default, not an honest empty/loading state as `UI_UX_DOCUMENT.md` §7 requires.
- `kpi` (traffic KPI overview) defaults to specific, plausible-looking hardcoded numbers (`activeVehicles: 1247, avgSpeedKmh: 34.2, ...`) before the first real fetch resolves, and permanently on fetch failure.

### 2.5 Service layer — real endpoint calls, but pointed at endpoints that don't exist, with baked-in mock fallbacks

`frontend/services/` (`api.ts`, `navigationApi.ts`, `accidentApi.ts`, `ambulanceApi.ts`, `networkApi.ts`, `predictionApi.ts`, `simulationApi.ts`, `trafficApi.ts`) is a reasonably clean centralized fetch layer (`api.ts` has retry/backoff/timeout, matches `TECHNICAL_DEEP_DIVE.md` §3's "one centralized API layer" requirement structurally). The problem is contract drift, not architecture:
- `navigationApi.ts` calls `/navigation/route`, `/navigation/reroute`, `/navigation/risk-eval`, `/navigation/resolve-location` — **none exist**; the real routing endpoint is `POST /api/routes` (§1.1) with a completely different request/response shape (`RouteRequest`/`RouteResponse`/`CandidateRoute`, not `RouteSearchResult`/`RouteOption`). Every one of these functions has a `catch` that returns bundled mock data or a hardcoded heuristic (e.g. `evaluateRouteRisk`'s fallback literally branches on `routeId === "route_1"` to decide whether to report high or low risk).
- `accidentApi.ts::simulateAccident()` calls `/accidents/create` (doesn't exist; real path is `POST /accidents`, and even that is a stub per §1.1) and falls back to a hardcoded accident record.
- `networkApi.ts::fetchNetworkTopology()` correctly targets the real `/api/network/topology` — but as noted in §2.3, nothing calls it.
- Not yet individually audited in this pass: `ambulanceApi.ts`, `predictionApi.ts`, `simulationApi.ts`, `trafficApi.ts` — flagged for a closer look in Phase 2/4 rather than blocking this document.

This means the adapter-layer *shape* the docs ask for already exists structurally; the fix is correcting endpoint paths/payload shapes to the real contract in §1.1 and removing the silent-mock-fallback behavior in favor of the explicit loading/error states `UI_UX_DOCUMENT.md` §7 specifies.

### 2.6 App structure beyond the main page

`frontend/app/` has 7 route segments beyond the root page: `navigation/`, `features/`, `emergency/`, `analysis/`, `alerts/`, `settings/`, `simulation/`, each presumably its own page. `UI_UX_DOCUMENT.md` §1 calls for "one primary screen, map-first — not a multi-page app with the map buried on one tab." These pages have **not yet been individually opened/audited** in this pass (this document is already large; going page-by-page here would be better spent as part of the Phase 11 control audit, once we know what's actually functional vs. dead after Phases 1–10 land). Flagging now so it isn't forgotten: Phase 11 needs to determine, for each of these 7 pages, whether it's load-bearing, redundant with the main page, or a placeholder to remove.

`components/` is organized by feature (`accident/`, `analysis/`, `common/`, `emergency/`, `map/`, `messages/`, `navigation/`, `routes/`, `simulation/`, `traffic/`) — a sensible structure worth preserving. `styles/` has dedicated `animations.css`, `emergency.css`, `map.css`, `navigation.css` alongside Tailwind — also worth preserving/reusing rather than replacing.

`types/` has `accident.ts`, `alerts.ts`, `ambulance.ts`, `common.ts`, `navigation.ts`, `route.ts`, `settings.ts`, `simulation.ts`, `traffic.ts` — a real start on the type list `TECH_STACK_AND_REQUIREMENTS.md` §6 asks for, but (per §2.5's contract drift) these were written against the frontend's assumed shapes, not the backend's actual response shapes — will need reshaping against §1.1/§1.2's real contract as each phase touches that data, not a wholesale rewrite.

---

## 3. Open questions / conflicts to resolve before or during later phases

1. **Real SUMO network exposure (blocks an honest Phase 3).** Confirmed missing on the backend (§1.3) and faked on the frontend (§2.3). Proposed smallest fix: load `osm.net.xml.gz` via `sumolib` once at startup (or on first SUMO connect) and build `RoadNetworkGraph` from real edges/junctions with `convertXY2LonLat()`-derived coordinates, replacing `initialize_graph()`'s synthetic grid. This is a real architectural change to a core backend module (not a typo-level fix) — needs explicit sign-off before Phase 3, per the error-correction protocol in `BUILD_INSTRUCTIONS.md`.
2. **Live vehicle markers require a new WS payload field.** TraCI can supply per-vehicle position/heading/speed/ID (`traci.vehicle.getIDList()` is already called for edge aggregation in `sumo_bridge.py` — extending it to also emit per-vehicle records is additive, not a rewrite). Needs sign-off since it changes the WS payload contract every frontend consumer relies on.
3. **Accident/ambulance/green-corridor endpoints need rewiring, not rebuilding.** `AccidentService`/`AmbulanceService` already exist and work against the mock grid; wiring `app/api/accidents.py` and `app/api/ambulance.py` to call them (instead of returning stub data) is a small, additive fix. What's genuinely new work: automatic accident detection from TraCI, tick-driven ambulance movement, the SUMO-clock 1-minute hold, and broadcasting all emergency state over the WebSocket — none of that exists yet in any form. Scope this explicitly as Phase 8's real workload, not a one-line fix.
4. **A real Mapbox token is needed** to verify Phase 3 visually — the checked-in `.env.local` value is a labeled placeholder. Will ask the user for one (or confirm the SVG fallback is acceptable) when Phase 3 starts.
5. **Which of the 7 secondary app routes are load-bearing** (§2.6) — deferred to Phase 11's control audit by design, not an oversight.
6. **Root-level stray `package.json`/`myenv/`** — pre-existing, untracked, unrelated to `frontend/`'s build; left untouched pending explicit instruction.
7. **Next.js 16.3.1 breaking-changes note** (`frontend/AGENTS.md`) — must consult `node_modules/next/dist/docs/` before making Next.js-specific changes in Phase 1, since this version postdates training data.

---

## 4. What's salvageable as-is (preserve, don't rewrite)

- `hooks/useWebSocket.ts`/`useSimulationStream.ts` — correct contract, solid throttling/reconnect design.
- `services/api.ts` — solid generic fetch wrapper (timeout, retry/backoff, typed error).
- `services/networkApi.ts` — correct endpoint, just needs to actually be called.
- The `riskByEdge` → Mapbox paint-expression / SVG stroke-color wiring in `TrafficMap.tsx` — real data flow, just painted onto fake geometry today.
- Feature-based `components/`/`styles/`/`types/` organization — keep the structure, correct the contracts within it.
- `app/main.py` lifespan/CORS/graceful-SUMO-fallback design, `SumoBridge`'s thread-affinity handling, `SimulationManager`'s tick loop skeleton, `WebSocketManager`'s broadcast fan-out — all solid, keep as-is and extend rather than replace.

---

**End of Phase 0 audit. Awaiting approval before Phase 1 (foundation repair).**
