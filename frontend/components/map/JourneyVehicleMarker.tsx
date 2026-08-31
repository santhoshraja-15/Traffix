"use client";

import { Navigation } from "lucide-react";

interface JourneyVehicleMarkerProps {
  /** Real bearing from hooks/useJourneySimulation — direction of travel
   * along the route's own real geometry, never guessed. */
  headingDeg: number;
  arrived: boolean;
}

/**
 * The active-journey vehicle — a small, polished GPS-puck-style marker
 * (a clean directional arrow in a soft ring), not an oversized icon or a
 * generic emoji. Distinct from the ambulance marker (🚑, a different real
 * entity from the emergency-mission system) so the two are never confused
 * on the map.
 */
export default function JourneyVehicleMarker({ headingDeg, arrived }: JourneyVehicleMarkerProps) {
  if (arrived) {
    return (
      <div className="relative flex items-center justify-center">
        <div className="w-6 h-6 rounded-full bg-emerald-500 ring-4 ring-emerald-300/50 flex items-center justify-center shadow-lg">
          <div className="w-2 h-2 rounded-full bg-white" />
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex items-center justify-center">
      {/* Soft live-motion pulse — subtle, not a full-panel effect. */}
      <div className="absolute w-7 h-7 rounded-full bg-sky-400/30 animate-ping" />
      <div
        className="relative w-6 h-6 rounded-full bg-sky-600 ring-2 ring-white flex items-center justify-center shadow-[0_2px_6px_rgba(0,0,0,0.35)]"
        style={{ transform: `rotate(${headingDeg}deg)` }}
      >
        <Navigation className="w-3.5 h-3.5 text-white" fill="white" strokeWidth={1.5} />
      </div>
    </div>
  );
}
