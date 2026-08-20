# TRAFFIX Frontend Documentation Pack

This folder is the single source of truth for building the TRAFFIX frontend
without inventing features, breaking backend integration, or losing the
simulation/emergency/navigation workflows.

## 1. The six documents

| Document | Purpose | Authority |
|---|---|---|
| [`FRONTEND_PRD.md`](./FRONTEND_PRD.md) | What must be built | Product requirements |
| [`FRONTEND_TECHNICAL_DEEP_DIVE.md`](./FRONTEND_TECHNICAL_DEEP_DIVE.md) | How it connects technically | Architecture |
| [`FRONTEND_BUILD_INSTRUCTIONS.md`](./FRONTEND_BUILD_INSTRUCTIONS.md) | How developers actually build it | Execution |
| [`FRONTEND_FLOW.md`](./FRONTEND_FLOW.md) | How every feature behaves | Logic/workflow |
| [`FRONTEND_DESIGN_SYSTEM.md`](./FRONTEND_DESIGN_SYSTEM.md) | How it looks | Visual/UX |
| [`FRONTEND_MASTER_PROMPT.md`](./FRONTEND_MASTER_PROMPT.md) | Instruction to AI coding/design tools | Construction |

The six files should not compete with each other — each one has a specific,
non-overlapping authority as listed above.

## 2. Most important rule

When using an AI coding tool, **do not give it only the master prompt.**

Give it the documents as project context, in this order:

```
FRONTEND_PRD.md
      ↓
FRONTEND_TECHNICAL_DEEP_DIVE.md
      ↓
FRONTEND_FLOW.md
      ↓
FRONTEND_DESIGN_SYSTEM.md
      ↓
FRONTEND_BUILD_INSTRUCTIONS.md
      ↓
FRONTEND_MASTER_PROMPT.md
      ↓
GENERATE FRONTEND
```

This prevents the AI from producing a beautiful UI that doesn't actually
correspond to the SUMO/TraCI + XGBoost + routing architecture underneath it.

## 3. One critical architectural decision

**The frontend does not own the intelligence.**

```
                              TRAFFIX
                                 │
                  ┌──────────────┴──────────────┐
                  │                              │
              FRONTEND                        BACKEND
                  │                              │
            Visualization                   Intelligence
                  │                              │
        ┌─────────┼─────────┐         ┌──────────┼──────────┐
        │         │         │         │          │          │
       Map   Navigation    UI       SUMO        ML       Routing
        │         │         │         │          │          │
        │         │         │       TraCI     XGBoost   NetworkX
        │         │         │         │          │          │
        └─────────┴─────────┘         └──────────┴──────────┘
                  │                              │
                  └──────── REST + WebSocket ─────┘
```

- **SUMO/TraCI** → generates/streams the traffic world.
- **XGBoost** → predicts traffic/congestion/risk.
- **NetworkX/A\*** → calculates routes.
- **Backend** → orchestrates everything.
- **Frontend** → makes the intelligence visible and interactive.

This separation matters because the project already has a substantial
working SUMO/ML environment. **Do not rebuild the ML pipeline inside the
frontend.**

## 4. The experience the frontend must deliver

```
TRAFFIX
Smart Routing Copilot
──────────────────────────────────────────────
Simulation ●     Navigation   Features   Analysis
──────────────────────────────────────────────

FROM [_________________]
DESTINATION [____________]
                                      [ GO ]

┌───────────────────────────────────────┬──────────────┐
│                                        │ TOP ROUTES   │
│                                        │              │
│                                        │ ★ Route A    │
│              LIVE CITY MAP             │ 12 min       │
│                                        │ 4.2 km       │
│        🚗 🚗 🚗                        │ Low traffic  │
│             🚗                         │              │
│      ────────────────                 │ Route B      │
│          🚗                            │ 14 min       │
│                                        │              │
│                    🚑                  │ Route C      │
│                                        │ 16 min       │
│                                        │              │
│                                        ├──────────────┤
│                                        │ LIVE         │
│                                        │ INTELLIGENCE │
│                                        │              │
│                                        │ Traffic      │
│                                        │ normal       │
└───────────────────────────────────────┴──────────────┘

NEXT: Turn Right in 200 m

4.2 km covered | 2.8 km remaining | ETA 12 min | 38 km/h
```

And when the accident is triggered:

```
⚠ ACCIDENT DETECTED
                     ◉
                 ~~~~~~~
             ~~~~~~~~~~~~~
          ~~~~~ ACCIDENT ~~~~
     ───────── X ─────────
          BLOCKED ROAD

REROUTING TRAFFIC...

TOP ROUTES
★ Route B — 13 min   Low congestion
  Route C — 15 min
  Route D — 17 min
```

Then:

```
🚑
EMERGENCY RESPONSE ACTIVE
Ambulance A-07 assigned
ETA: 2 min 20 sec

"Emergency vehicle approaching.
 Please make way."

        ↓
    ACCIDENT
        ↓
     RESCUE
        ↓
    HOSPITAL
        ↓
✓ RESCUE SUCCESSFUL
```

That is the frontend story the judges should experience: not a collection
of screens, but one continuous intelligent system.

The strongest positioning remains:

> TRAFFIX doesn't simply tell a driver where the traffic is. It
> continuously understands how traffic is changing, determines what
> should happen next, and turns those decisions into an adaptive
> navigation and emergency-response experience.
