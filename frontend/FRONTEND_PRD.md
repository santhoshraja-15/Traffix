# TRAFFIX — Frontend Product Requirements Document

## 1. Product Name

**TRAFFIX**

### Tagline

*Smart Routing Copilot for Dynamic Urban Traffic*

---

## 2. Product Vision

TRAFFIX is an intelligent traffic navigation and intervention platform that does more than display traffic.

It continuously observes the simulated/real traffic environment, understands road conditions, evaluates congestion, predicts risk, calculates alternative routes, reacts to accidents, supports emergency ambulance routing, and continuously updates navigation decisions.

The frontend must make this intelligence understandable through a highly interactive, map-centric interface.

The user should feel that they are operating a live traffic intelligence system rather than using a conventional static map.

---

## 3. Primary Objective

Build a production-quality frontend that:

1. Displays the entire SUMO/TraCI traffic environment.
2. Accepts FROM and DESTINATION locations.
3. Calculates and displays the shortest route initially.
4. Shows a shortest-route notification.
5. Loads dynamic optimal-route analysis.
6. Displays the top 3 current routes.
7. Continuously updates route recommendations.
8. Recalculates routes after every important intersection.
9. Tracks the simulated user's vehicle.
10. Displays remaining distance and ETA.
11. Displays covered distance and elapsed time.
12. Displays next navigation instruction.
13. Displays traffic/congestion state.
14. Displays continuous navigation messages.
15. Allows simulation and real-time modes.
16. Allows accident simulation.
17. Visually represents accident propagation.
18. Marks accident corridors as unavailable/high-risk.
19. Automatically reroutes traffic.
20. Finds the nearest virtual ambulance.
21. Assigns an ambulance to the accident.
22. Simulates ambulance movement.
23. Routes the ambulance to the accident.
24. Routes the ambulance to the nearest appropriate hospital.
25. Provides emergency messages.
26. Simulates traffic yielding to the ambulance.
27. Displays performance metrics.
28. Displays traffic intelligence.
29. Remains functional independently even when optional modules are unavailable.

---

## 4. Target Users

### Primary User

A normal driver/user navigating from one location to another.

### Secondary User

Traffic control/operator.

### Emergency User

Traffic/emergency operator managing accident response and ambulance movement.

---

## 5. Core User Experience

The primary experience follows:

```
FROM → DESTINATION → SHORTEST PATH → OPTIMAL ROUTES → LIVE NAVIGATION → DYNAMIC REROUTING → DESTINATION
```

Emergency experience:

```
ACCIDENT → DETECTION → LOCATION → ALERT → AMBULANCE ASSIGNMENT → EMERGENCY ROUTE → RESCUE → HOSPITAL → SUCCESS
```

---

## 6. Application Modes

### 6.1 Simulation Mode

Default mode.

Data originates primarily from:

**SUMO + TraCI + project simulation state.**

Simulation mode allows:

- traffic visualization
- route simulation
- accident injection
- ambulance simulation
- congestion changes
- rerouting
- performance analysis

---

### 6.2 Real-Time Mode

Designed for future/live integration.

Potential sources:

- live sensors
- cameras
- GPS
- IoT devices
- traffic APIs

The UI architecture must support real-time mode without requiring a redesign.

---

## 7. Main Application Layout

The main screen must contain:

### Header

TRAFFIX logo/name

Mode selector:

- SIMULATION
- REAL-TIME

Navigation:

- Navigation
- Features
- Analysis

System status indicator.

---

## 8. Navigation Page

### 8.1 Search Area

- FROM
- DESTINATION
- GO button

Optional:

- Swap locations

---

### 8.2 Main Map

The map is the primary interface.

It must display:

- road network
- traffic
- vehicle positions
- user vehicle
- route
- alternative routes
- accident zones
- ambulance
- hospitals
- traffic signals where available
- road congestion
- route direction arrows
- current position
- destination

---

### 8.3 Initial Route

After FROM and DESTINATION are selected:

1. Resolve locations.
2. Map them to SUMO/TraCI nodes.
3. Calculate shortest path.
4. Display shortest path.
5. Show a popup:

> "Shortest route found"

Then transition into:

> "Analyzing live traffic..."

---

### 8.4 Optimal Route Loading

Display:

> Analyzing traffic...
> Loading optimal routes...

Evaluating:

- congestion
- traffic density
- average speed
- predicted congestion
- road risk
- route distance
- estimated travel time

---

### 8.5 Top Routes

A dedicated panel:

**TOP ROUTES**

- Route 1 — Recommended
- Route 2 — Alternative
- Route 3 — Alternative

Each route displays:

- ETA
- distance
- congestion
- risk
- route score

The recommended route must be visually emphasized.

---

## 9. Dynamic Routing

Routes must not remain static.

Whenever the user reaches an important intersection:

1. Obtain current traffic state.
2. Recalculate route scores.
3. Generate alternative routes.
4. Select best current route.
5. Update Top Routes.
6. Update route visualization.
7. Continue navigation.

The user should see the system behaving like a dynamic navigation system.

---

## 10. Navigation Information Bar

A compact navigation bar above the map must display:

**NEXT TURN**

Example:

> "Turn right onto Anna Salai"

Also:

- Distance to turn
- Time to turn
- Current speed

---

## 11. Journey Metrics

Display:

- Distance covered
- Distance remaining
- Time elapsed
- Estimated remaining time
- Current speed
- Average speed

---

## 12. Message Box

The message box continuously explains what TRAFFIX is doing.

Examples:

- "Navigation started."
- "Traffic conditions are being analyzed."
- "Alternative routes available."
- "Route optimized using current traffic."
- "Heavy congestion detected ahead."
- "Rerouting to avoid congestion."
- "Accident detected ahead."
- "Route blocked. Calculating alternatives."
- "Ambulance assigned."
- "Emergency vehicle approaching."
- "Please make way."
- "Rescue successful."

Messages should be concise and human-readable.

---

## 13. Accident Simulation

Features → Accident

The user can select:

**Choose on Map**

This opens a small map selector.

The operator selects a road/location.

Then:

**SIMULATE ACCIDENT**

---

## 14. Accident Visualization

When accident simulation starts:

1. Accident marker appears.
2. Ripple effect expands from the accident.
3. Accident zone becomes highlighted.
4. Affected corridor changes visual state.
5. Traffic risk increases.
6. Route scoring changes.
7. Existing routes are recalculated.
8. Traffic is redirected.

---

## 15. Accident Alerts

The message box must show highlighted alerts.

Example:

> ⚠ ACCIDENT DETECTED
> "Major traffic disruption detected near the selected corridor."

Then:

> "Route blocked."
> "Calculating alternate routes."

Then:

> "Navigation rerouted."

---

## 16. Ambulance System

The ambulance module must maintain virtual ambulance locations.

Possible locations:

- junctions
- hospitals
- strategic road nodes

When an accident occurs:

**FIND NEAREST AMBULANCE**

The system determines:

- nearest ambulance
- distance
- estimated arrival
- route
- current traffic

---

## 17. Ambulance Assignment

After assignment:

**AMBULANCE ASSIGNED**

Example message:

> "Ambulance A-07 assigned to the accident."

If the ambulance shares the user's route:

> "Ambulance approaching. Please make way."

Otherwise:

> "Emergency response activated."

---

## 18. Start Rescue

Button:

**START RESCUE**

The ambulance:

1. Starts at assigned node.
2. Calculates shortest feasible route.
3. Considers traffic.
4. Moves through the network.
5. Reaches accident.
6. Waits for simulated rescue duration.
7. Calculates hospital route.
8. Routes to hospital.
9. Reaches hospital.
10. Reports rescue success.

---

## 19. Traffic Yielding

During ambulance movement:

Traffic vehicles along the ambulance corridor may:

- reduce speed
- yield
- slow down
- create a visual corridor

This should be presented as a simulation rather than a claim of real-world infrastructure control.

---

## 20. Features Page

The Features page must contain:

### Traffic Simulation

- accident simulation
- traffic scenario control
- congestion visualization

### Emergency

- ambulance assignment
- emergency routing
- rescue simulation

### Routing

- shortest path
- dynamic route
- alternative routes
- rerouting

---

## 21. Analysis Page

Analysis must display:

### Performance Metrics

- average travel time
- congestion level
- average speed
- vehicles
- route efficiency
- reroutes
- accidents
- ambulance response time

### Route Comparison

Before intervention vs After intervention

---

## 22. Visual Design

The interface must be:

- light themed
- modern
- professional
- clean
- human
- map-first
- highly interactive
- responsive
- visually impressive
- suitable for a hackathon demonstration

Avoid excessive AI-generated visual effects.

The interface should resemble a sophisticated transportation command/navigation product rather than a generic AI dashboard.

---

## 23. Success Criteria

The frontend is considered complete when:

- [ ] navigation works
- [ ] map works
- [ ] route appears
- [ ] shortest route appears first
- [ ] optimal routes load
- [ ] top 3 routes appear
- [ ] route updates dynamically
- [ ] navigation metrics update
- [ ] accident simulation works
- [ ] accident visualization works
- [ ] rerouting works
- [ ] ambulance assignment works
- [ ] ambulance movement works
- [ ] hospital routing works
- [ ] message system works
- [ ] analysis page works
- [ ] simulation mode works
- [ ] real-time architecture exists
- [ ] backend integration is modular
- [ ] no existing SUMO/ML files are modified
