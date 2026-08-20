# TRAFFIX Frontend Technical Deep Dive

## 1. Architecture

**Frontend:**
- Next.js
- React
- TypeScript
- Map rendering
- WebSocket client
- REST API client

**Backend:**
- FastAPI
- SUMO
- TraCI
- NetworkX
- XGBoost
- Routing engine
- Emergency engine

**Communication:**
- REST → commands / requests
- WebSocket → continuous traffic state

---

## 2. Frontend Technology Stack

### Framework
Next.js

### Language
TypeScript

### UI
React

### Styling
Tailwind CSS

### Components
Reusable React components

### Map
Mapbox GL JS or equivalent WebGL map renderer.

### Animation
- CSS animations
- Framer Motion where useful
- Map-based animations should primarily be handled by the map rendering engine.

### State Management
React state initially.

Use Zustand if application-wide state becomes complex.

---

## 3. Frontend Directory

```
frontend/
├── app/
│   ├── page.tsx
│   ├── navigation/
│   │   └── page.tsx
│   ├── features/
│   │   └── page.tsx
│   ├── analysis/
│   │   └── page.tsx
│   └── layout.tsx
│
├── components/
│   ├── layout/
│   ├── map/
│   ├── navigation/
│   ├── routes/
│   ├── traffic/
│   ├── accident/
│   ├── ambulance/
│   ├── analysis/
│   ├── messages/
│   └── common/
│
├── hooks/
│   ├── useTrafficSocket.ts
│   ├── useNavigation.ts
│   ├── useRoute.ts
│   ├── useAccident.ts
│   └── useAmbulance.ts
│
├── services/
│   ├── api.ts
│   ├── navigationService.ts
│   ├── trafficService.ts
│   ├── accidentService.ts
│   └── ambulanceService.ts
│
├── lib/
│   ├── map.ts
│   ├── websocket.ts
│   ├── formatters.ts
│   └── constants.ts
│
├── types/
│   ├── traffic.ts
│   ├── route.ts
│   ├── navigation.ts
│   ├── accident.ts
│   └── ambulance.ts
│
└── styles/
    └── globals.css
```

---

## 4. Backend Integration

The frontend must **NEVER** directly manipulate SUMO.

Frontend requests:

```
POST /navigation/route
```

Backend handles:

- SUMO
- TraCI
- NetworkX
- XGBoost routing

Frontend only visualizes the result.

---

## 5. Suggested API Contract

### `POST /api/navigation/route`

Request:

```json
{
  "origin": {
    "lat": 0,
    "lon": 0
  },
  "destination": {
    "lat": 0,
    "lon": 0
  },
  "mode": "simulation"
}
```

Response:

```json
{
  "shortest_route": {},
  "optimal_routes": [],
  "recommended_route": {}
}
```

---

## 6. Dynamic Traffic WebSocket

Example:

```
/ws/traffic
```

Messages contain:

- vehicle positions
- road state
- speed
- density
- congestion
- traffic signals
- user position
- ambulance position
- accident status

---

## 7. Route Model

A route contains:

- `id`
- `road_ids`
- `coordinates`
- `distance`
- `eta`
- `average_speed`
- `congestion`
- `risk`
- `score`
- `recommended`

---

## 8. Traffic State

Traffic state:

- `vehicle_count`
- `density`
- `average_speed`
- `congestion_level`
- `road_status`
- `predicted_congestion`
- `timestamp`

---

## 9. Accident Model

Accident:

- `id`
- `location`
- `road_id`
- `severity`
- `status`
- `affected_roads`
- `created_at`

---

## 10. Ambulance Model

Ambulance:

- `id`
- `current_node`
- `status`
- `speed`
- `route`
- `destination`
- `eta`
- `assigned_accident`

---

## 11. State Architecture

Global application state:

- `mode`
- `trafficState`
- `navigationState`
- `routeState`
- `accidentState`
- `ambulanceState`
- `messages`
- `analysisMetrics`

---

## 12. Important Principle

The frontend must **degrade gracefully**.

If **XGBoost unavailable** → use backend fallback route scoring.

If **WebSocket unavailable** → show connection warning and retain last known state.

If **Map service unavailable** → show system error instead of crashing.

If **ambulance module unavailable** → navigation must still work.

---

## 13. Performance

Target: **60 FPS map interaction.**

Avoid React re-rendering for every vehicle update.

Use:

- Mapbox sources/layers
- `requestAnimationFrame`
- memoized components
- batched state updates

---

## 14. Security

API keys belong in environment variables.

Never expose private backend credentials.

Frontend `.env`:

```
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_WS_URL=
NEXT_PUBLIC_MAP_TOKEN=
```

---

## 15. Responsive Design

Primary target: **Laptop/Desktop**

Secondary: **Tablet**

The hackathon demo should prioritize a **1366×768** or **1920×1080** display.

---

## 16. Error Handling

Every backend operation requires:

- loading state
- success state
- failure state
- retry option

The UI must never silently fail.
