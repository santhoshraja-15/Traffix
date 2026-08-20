# TRAFFIX — MASTER FRONTEND CONSTRUCTION PROMPT

This is the most important file if you are using Figma Make, Lovable, Bolt, Cursor, Claude Code, Gemini, or another AI coding tool.

You are a senior product designer, frontend architect, React/Next.js engineer, GIS visualization engineer, UX engineer, and transportation-technology interface specialist.

Build the COMPLETE TRAFFIX frontend.

Do not create a generic dashboard.
Do not create a static mockup.

Build a functional, map-centric, intelligent traffic navigation interface that is ready to connect to the existing TRAFFIX FastAPI + SUMO + TraCI + NetworkX + XGBoost backend.

---

## PROJECT

**Name:** TRAFFIX

**Tagline:** Smart Routing Copilot for Dynamic Urban Traffic

**Purpose:** TRAFFIX observes simulated/live traffic, calculates routes, evaluates congestion, dynamically reroutes vehicles, responds to accidents, supports ambulance routing, and explains current traffic conditions.

---

## CRITICAL EXISTING SYSTEM RULE

**DO NOT** modify, delete, rename, relocate, or overwrite existing SUMO, TraCI, XGBoost, datasets, scenarios, or backend files.

The frontend is a **NEW APPLICATION LAYER**.

It must communicate with the existing backend through APIs and WebSockets.

---

## TECHNOLOGY

Use:

- Next.js
- React
- TypeScript
- Tailwind CSS
- Mapbox GL JS
- Lucide icons
- Framer Motion where appropriate
- Zustand if global state is required

---

## DESIGN

Use a **LIGHT** theme.

The product must look:

- professional
- human
- clean
- intelligent
- modern
- trustworthy
- responsive
- transportation-focused

Avoid:

- excessive gradients
- excessive neon
- overly futuristic interfaces
- generic AI dashboards
- unnecessary glassmorphism
- gaming-style interfaces

The map must dominate the screen.

---

## PRIMARY SCREEN

Create the TRAFFIX navigation screen.

**Header:**
- TRAFFIX — Smart Routing Copilot
- Mode: SIMULATION | REAL-TIME
- Navigation: Navigation / Features / Analysis
- System status: Backend Connected / Simulation Connected / Traffic Stream Active

---

## SEARCH

Create:

- FROM
- DESTINATION
- GO

The user must be able to enter locations.

Do not use hard-coded route results.

Prepare the interface for backend location resolution.

---

## MAP

Create a large interactive map.

The map must support:

- road network
- traffic
- vehicles
- user vehicle
- destination
- route lines
- alternative routes
- accident zones
- ambulances
- hospitals
- traffic states
- route direction
- current location

Use WebGL map rendering.

---

## ROUTING EXPERIENCE

When user selects FROM and DESTINATION:

**STEP 1** — Resolve locations.

**STEP 2** — Map locations to backend/SUMO nodes.

**STEP 3** — Request shortest route.

**STEP 4** — Display shortest route.

**STEP 5** — Display notification: "Shortest route found."

**STEP 6** — Show: "Analyzing live traffic..."

**STEP 7** — Show: "Loading optimal routes..."

**STEP 8** — Receive top routes.

**STEP 9** — Display TOP ROUTES: Route 1 / Route 2 / Route 3.

Each route shows: ETA, distance, traffic, risk, score.

Highlight the recommended route.

---

## DYNAMIC NAVIGATION

The interface must behave like an intelligent navigation system.

Show:

- current position
- current route
- next turn
- distance to next turn
- estimated arrival
- distance remaining
- distance covered
- current speed
- average speed

Navigation bar: `NEXT TURN — "Turn right" — "200 m"`

---

## DYNAMIC ROUTE REFRESH

At every important intersection: request updated traffic state.

Recalculate: route score, traffic, ETA, risk, alternatives.

Update TOP ROUTES.

Do not reload the entire page.

Update only relevant map layers and panels.

---

## TOP ROUTES

Create a persistent panel: **TOP ROUTES**

Example:

```
RECOMMENDED
Route A
12 min | 4.2 km | Low congestion | Risk: Low

ALTERNATIVE
Route B
14 min | 3.8 km | Moderate congestion

ALTERNATIVE
Route C
16 min | 5.1 km | High congestion
```

The recommended route must be visually obvious.

---

## LIVE MESSAGE SYSTEM

Create: **LIVE TRAFFIC INTELLIGENCE**

Messages appear chronologically.

Examples:

- "Navigation started."
- "Traffic conditions are being analyzed."
- "Recommended route selected."
- "Heavy congestion detected ahead."
- "Rerouting to avoid congestion."
- "Accident detected."
- "Route blocked."
- "Alternative route selected."
- "Ambulance assigned."
- "Emergency vehicle approaching."
- "Please make way."
- "Rescue successful."

Use appropriate visual severity.

---

## ACCIDENT SIMULATION

Features page must contain: **ACCIDENT SIMULATION**

- Location: Choose on Map
- Severity: Low / Medium / High
- Button: SIMULATE ACCIDENT

When clicked:

1. Open small map selector.
2. Allow user to select a road.
3. Confirm.
4. Return to main map.

Display: accident marker, expanding ripple, affected road, accident zone, warning notification.

Then update traffic visualization.

---

## ACCIDENT EFFECT

When accident is active: affected corridor becomes visually highlighted.

The routing engine must receive the event through the backend API.

The frontend must **not** independently calculate authoritative routing.

After backend response: update route, update top routes, update navigation, show rerouting message.

---

## AMBULANCE

Create: **AMBULANCE RESPONSE**

Button: **FIND NEAREST AMBULANCE**

Display: ambulance ID, location, distance, ETA, status.

Button: **ASSIGN AMBULANCE** → then **START RESCUE**

---

## AMBULANCE FLOW

1. Accident active.
2. Find nearest ambulance.
3. Assign ambulance.
4. Display: "Ambulance A-07 assigned."
5. Calculate emergency route.
6. Animate ambulance.
7. If ambulance shares user's corridor: "Emergency vehicle approaching. Please make way."
   Otherwise: "Emergency response activated."
8. Ambulance reaches accident. Show: "Ambulance arrived."
9. Wait simulated rescue duration.
10. Calculate hospital route.
11. Animate ambulance toward hospital.
12. At hospital: "Rescue successful."

---

## AMBULANCE VISUALIZATION

Ambulance marker: distinct emergency icon, pulse animation, route line, current position, ETA, status.

---

## TRAFFIC YIELDING

When ambulance is active: vehicles around the emergency corridor can visually slow/yield.

This is a simulation. Show: "Emergency corridor active."

---

## FEATURES PAGE

Create a page using the same application shell.

Sections: TRAFFIC SIMULATION, ACCIDENT RESPONSE, AMBULANCE RESPONSE, ROUTE OPTIMIZATION, DYNAMIC REROUTING.

Each feature should have: description, status, controls, visual state.

---

## ANALYSIS PAGE

Create: **PERFORMANCE METRICS**

Cards: average travel time, average speed, congestion, vehicles, reroutes, route efficiency, emergency response, accidents.

---

## BEFORE / AFTER

Show: Before Intervention vs After Intervention.

Metrics: travel time, congestion, average speed, route efficiency.

Use simple professional charts.

---

## MAP LAYERS

Implement logical map layers: roads, traffic, vehicles, routes, accidents, ambulances, hospitals, navigation.

---

## WEB SOCKET

Prepare: `useTrafficSocket()`

WebSocket continuously receives: vehicle positions, road states, traffic density, speed, congestion, user position, ambulance state, accident state.

Do not rerender the complete React tree for every vehicle update.

Use map sources/layers for high-frequency visualization.

---

## API LAYER

Create services: `navigationService`, `trafficService`, `accidentService`, `ambulanceService`.

Never place API calls directly inside visual components when avoidable.

---

## STATE

Maintain: `mode`, `connectionState`, `navigationState`, `trafficState`, `routeState`, `accidentState`, `ambulanceState`, `messages`, `metrics`.

---

## ERROR HANDLING

Handle: backend unavailable, SUMO unavailable, WebSocket disconnected, route unavailable, invalid destination, invalid accident location, ambulance unavailable, API timeout, map failure.

The application must never crash. Display human-readable errors.

---

## LOADING STATES

Use meaningful states:

- "Finding route..."
- "Finding shortest path..."
- "Analyzing traffic..."
- "Loading optimal routes..."
- "Updating route..."
- "Finding nearest ambulance..."
- "Dispatching emergency vehicle..."
- "Calculating hospital route..."

---

## ANIMATION

Use animation meaningfully.

Required: vehicle movement, route transition, accident ripple, ambulance pulse, loading animation, message transitions, route refresh.

Do not overanimate the interface.

---

## RESPONSIVE

Desktop-first. Target: 1366×768 and 1920×1080.

Map remains dominant. Panels must resize or collapse gracefully.

---

## COMPONENT ARCHITECTURE

Create reusable components:

`AppHeader`, `ModeSelector`, `LocationSearch`, `TrafficMap`, `UserMarker`, `VehicleLayer`, `RouteLayer`, `TopRoutes`, `NavigationBar`, `JourneyMetrics`, `MessageBox`, `AccidentPanel`, `AccidentMapSelector`, `AmbulancePanel`, `AmbulanceMarker`, `HospitalLayer`, `PerformanceMetrics`, `BeforeAfterComparison`, `SystemStatus`, `LoadingOverlay`, `ErrorBanner`.

---

## CODE QUALITY

Use TypeScript strict typing. No unnecessary `any`. No duplicated components. No hardcoded production data. Environment variables for configuration. Reusable hooks. Reusable API services.

Clear separation between: UI state, services, map, backend communication.

---

## IMPORTANT

Do not fake backend functionality as if it were real.

If backend integration is not yet available: create mock adapters behind the same interfaces.

Clearly separate: **MOCK MODE** and **REAL BACKEND MODE**.

The same UI must work with either.

---

## FINAL USER EXPERIENCE

The final application should feel like:

**Google Maps + traffic intelligence + traffic simulation + dynamic optimization + emergency response + traffic control intelligence**

But it must remain an original TRAFFIX product.

---

## DEMO SEQUENCE

Prepare the UI for this exact hackathon demonstration:

1. Load TRAFFIX.
2. Show live SUMO traffic.
3. Enter FROM.
4. Enter DESTINATION.
5. Click GO.
6. Display shortest route.
7. Show: "Shortest route found."
8. Show: "Analyzing live traffic..."
9. Show: "Loading optimal routes..."
10. Display TOP 3 ROUTES.
11. Select recommended route.
12. Start navigation.
13. Show live vehicle movement.
14. Show navigation instructions.
15. Show ETA and remaining distance.
16. Reach an intersection.
17. Refresh routes.
18. Inject accident.
19. Display ripple.
20. Highlight accident corridor.
21. Show warning.
22. Recalculate route.
23. Display new TOP 3 routes.
24. Select nearest ambulance.
25. Assign ambulance.
26. Start rescue.
27. Animate ambulance.
28. Display emergency message.
29. Show traffic yielding.
30. Reach accident.
31. Route ambulance to hospital.
32. Display: "Rescue successful."
33. Open Analysis.
34. Show Before/After metrics.

---

## FINAL QUALITY BAR

The result must **NOT** look like a student CRUD project.

It must look like a polished transportation technology product capable of being demonstrated to: hackathon judges, traffic authorities, technology companies, investors, researchers.

Every screen must have a purpose.

Every animation must communicate state.

Every panel must communicate useful information.

The map must remain the hero.

The system must communicate:

**OBSERVE → UNDERSTAND → PREDICT → OPTIMIZE → ACT → RESPOND → LEARN**

This is TRAFFIX.
