export interface TurnInstruction {
  instruction: string; // e.g. "Turn right onto Anna Salai"
  distanceMeters: number;
  timeSeconds: number;
  turnType: "straight" | "left" | "right" | "u-turn" | "destination";
  roadName: string;
}

// NavigationState (isNavigating/currentPosition/distanceCoveredKm/etc.) used
// to live here but implied a live per-user position feed that doesn't
// exist anywhere in the backend — removed when JourneyMetrics.tsx was
// rebuilt around what's actually real: real elapsed time since a genuine
// "Start Journey" click, plus the route's real planned totals, honestly
// labeled as planned rather than live. See JourneyMetrics.tsx's own doc
// comment for the full reasoning.
