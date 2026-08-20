# TRAFFIX Frontend Build Instructions

## Phase 1 — Environment

Install:

- Node.js LTS
- VS Code
- Git
- Browser
- Mapbox account/token if Mapbox is used.

---

## Phase 2 — Create Frontend

Inside `TRAFFIX`:

```bash
npx create-next-app@latest frontend
```

Choose:

- TypeScript: **Yes**
- ESLint: **Yes**
- Tailwind: **Yes**
- App Router: **Yes**

---

## Phase 3 — Install Dependencies

```bash
npm install mapbox-gl lucide-react framer-motion zustand axios clsx tailwind-merge
```

---

## Phase 4 — Establish Backend Connection

Configure:

```
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_WS_URL
NEXT_PUBLIC_MAP_TOKEN
```

Test:

```
GET /health
```

The frontend must display:

- **Backend Connected**

or

- **Backend Offline**

---

## Phase 5 — Build Application Shell

Create:

- Header
- Sidebar/navigation
- Map container
- Message panel
- Route panel
- Status bar

---

## Phase 6 — Build Map

First display the SUMO road network.

Then:

- vehicles
- roads
- user marker
- destination
- routes
- accident zones
- ambulance
- hospitals

---

## Phase 7 — Build Navigation

Implement:

- FROM
- DESTINATION
- GO

Flow:

```
input → API → shortest route → display → optimal route analysis → Top Routes
```

---

## Phase 8 — Dynamic Navigation

Every relevant intersection:

Request current route recommendation.

Update:

- recommended route
- top routes
- ETA
- distance
- next instruction

---

## Phase 9 — Message System

Implement centralized message manager.

Message types:

- INFO
- SUCCESS
- WARNING
- ACCIDENT
- EMERGENCY
- ROUTING
- SYSTEM

Messages must have timestamps.

---

## Phase 10 — Accident

Build:

- Accident panel
- "Choose on Map" modal
- Accident marker
- Ripple animation
- Affected corridor
- Alert
- Reroute

---

## Phase 11 — Ambulance

Build:

- Find ambulance
- Assignment card
- Start rescue
- Ambulance marker
- Emergency route
- Hospital route
- Rescue success

---

## Phase 12 — Analysis

Create:

- Metrics cards
- Before/after comparison
- Traffic charts
- Route performance
- Emergency response

---

## Phase 13 — Polish

Add:

- micro animations
- hover states
- smooth transitions
- loading indicators
- empty states
- error states
- responsive behavior

---

## Phase 14 — Testing

Test:

- Normal navigation
- Invalid destination
- No route
- Heavy congestion
- Accident
- Rerouting
- Ambulance
- Hospital
- WebSocket disconnect
- Backend disconnect
- Mode switching
- Page refresh

---

## Phase 15 — Demo Preparation

Prepare one deterministic scenario:

1. Start simulation.
2. Select origin.
3. Select destination.
4. Show shortest route.
5. Show optimal routes.
6. Start navigation.
7. Inject accident.
8. Show congestion.
9. Show rerouting.
10. Assign ambulance.
11. Start rescue.
12. Ambulance reaches accident.
13. Ambulance reaches hospital.
14. Show performance improvement.
