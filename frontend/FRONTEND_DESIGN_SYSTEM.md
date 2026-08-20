# TRAFFIX Frontend Design System

## 1. Design Philosophy

TRAFFIX should feel:

- intelligent
- calm
- professional
- human
- responsive
- trustworthy
- operational
- modern

It should **NOT** feel:

- overly futuristic
- robotic
- gaming-oriented
- generic AI dashboard
- overloaded with glowing effects

---

## 2. Theme

Primary theme: **LIGHT**

- **Background:** soft neutral / white
- **Map:** light transportation map
- **Cards:** white
- **Borders:** subtle gray
- **Accent:** blue / cyan transportation accent
- **Emergency:** red
- **Warning:** amber
- **Success:** green

---

## 3. Typography

Use:

- Inter
- or Manrope

Hierarchy:

- **Large:** 32–40px
- **Section:** 20–24px
- **Card:** 14–18px
- **Metadata:** 12–14px

---

## 4. Navigation Layout

Desktop:

```
------------------------------------------------
HEADER
------------------------------------------------
SEARCH / NAVIGATION
------------------------------------------------
|                                              |
|                  MAP                         |
|                                              |
|                         | TOP ROUTES         |
|                         | MESSAGE BOX        |
|                         |                    |
------------------------------------------------
NAVIGATION METRICS
------------------------------------------------
```

---

## 5. Header

**Left:**
- TRAFFIX
- Smart Routing Copilot

**Center/right:**
- Simulation / Real-Time
- Navigation
- Features
- Analysis
- System status

---

## 6. Search Card

```
FROM
[ Enter starting location ]

DESTINATION
[ Enter destination ]

[ GO ]
```

---

## 7. Map

Map should occupy the majority of the screen.

The map is the visual center of the application.

---

## 8. Route Colors

Use consistent semantics.

- **Recommended route:** Primary accent
- **Alternative:** Neutral secondary colors
- **Accident:** Red
- **Emergency:** Red/amber
- **Traffic:** Green → Yellow → Orange → Red

---

## 9. Top Routes Card

Title: **TOP ROUTES**

Each card:

- Route name
- ETA
- Distance
- Traffic
- Risk
- Score

---

## 10. Message Box

Header: **LIVE TRAFFIC INTELLIGENCE**

Messages appear chronologically.

Latest critical message is emphasized.

---

## 11. Navigation Bar

At top of map:

```
NEXT
Turn right
200 m
2 min
```

---

## 12. Bottom Metrics

- Distance covered
- Distance remaining
- Time elapsed
- ETA
- Current speed

---

## 13. Accident UI

Accident card:

```
ACCIDENT SIMULATION

Location
Severity
Affected corridor

[ Choose on Map ]
[ Simulate Accident ]
```

---

## 14. Ambulance UI

```
AMBULANCE RESPONSE

Nearest ambulance
Distance
ETA
Status

[ Assign Ambulance ]
[ Start Rescue ]
```

---

## 15. Animation Rules

Use animation to communicate state.

Examples:

- vehicle movement
- route transitions
- accident ripple
- ambulance pulse
- route loading
- message appearance

Do not animate every UI component continuously.

---

## 16. Accessibility

- Buttons must have readable labels.
- Contrast must remain high.
- Keyboard navigation should work.
- Icons should have accessible labels.

---

## 17. Empty States

Example:

> "No navigation route selected."
> "Enter a destination to begin."

---

## 18. Loading States

Example:

> "Finding shortest route..."
> "Analyzing traffic..."
> "Calculating alternatives..."
> "Finding nearest ambulance..."

---

## 19. Error States

Example:

> "Unable to calculate route."
> "Traffic simulation disconnected."
> "Unable to locate destination."

Always provide: **Retry**

---

## 20. Responsive Behavior

Desktop-first.

At smaller width:

- side panels collapse
- cards stack
- search becomes compact
- map remains dominant
