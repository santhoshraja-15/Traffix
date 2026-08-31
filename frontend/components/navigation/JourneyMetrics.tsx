"use client";

import { Clock, MapPin, Gauge, CheckCircle2, Play, FlagOff } from "lucide-react";
import { RouteOption } from "../../types/route";
import { JourneySimulationState } from "../../hooks/useJourneySimulation";

interface JourneyMetricsProps {
  route: RouteOption;
  /** Real wall-clock timestamp (Date.now()) of the last "Start Journey"
   * click, or null before it's been clicked / after a different route was
   * selected (see app/page.tsx's reset-on-route-change effect). */
  journeyStartedAt: number | null;
  /** Real position/progress from hooks/useJourneySimulation — derived from
   * the route's own real geometry, real elapsed time, and real live
   * per-edge traffic. All fields are real once journeyStartedAt is set. */
  journey: JourneySimulationState;
  onStartJourney: () => void;
}

/**
 * Honesty note (see the frontend repair project's "journey progress"
 * finding, and the active-navigation follow-up): there is no backend
 * position feed independent of what useJourneySimulation itself derives —
 * so once a journey starts, EVERY field below is real (grounded in the
 * route's real geometry + real elapsed time + real live traffic), not a
 * frozen or guessed number. Before a journey starts, the planned totals
 * (Route Distance / Est. Duration / Avg Speed) are the route's real
 * backend-computed values, honestly labeled "planned" rather than implying
 * a live countdown they aren't yet.
 */
export default function JourneyMetrics({ route, journeyStartedAt, journey, onStartJourney }: JourneyMetricsProps) {
  const started = journeyStartedAt !== null;

  const distanceCoveredDisplay = started ? `${journey.distanceCoveredKm.toFixed(2)}` : "—";
  const distanceLabel = started ? "Distance Left" : "Route Distance";
  const distanceValue = started ? journey.distanceLeftKm : route.distanceKm;
  const durationLabel = started ? "Time Left" : "Est. Duration";
  const durationValue = started ? Math.max(0, Math.round(journey.etaMinutes)) : Math.round(route.etaMinutes);
  const arrivalValue = started
    ? journey.estimatedArrival
    : new Date(Date.now() + route.etaMinutes * 60_000).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
  const speedValue = started ? journey.currentSpeedKmh : route.averageSpeedKmh;
  const speedCaption = started ? (journey.arrived ? "Arrived" : "Live (traffic-aware)") : "Planned";

  const elapsedDisplay = (() => {
    if (!started) return "—";
    const totalSeconds = Math.max(0, Math.round(journey.elapsedMinutes * 60));
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  })();

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">

      {/* Time Elapsed — real wall-clock time since Start Journey */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center border border-slate-200">
          <Clock className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase flex items-center gap-1 tracking-wider">
            Time Elapsed
            {started && !journey.arrived && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
          </span>
          <span className="font-extrabold text-slate-800 text-sm">{elapsedDisplay}</span>
        </div>
      </div>

      {/* Distance Covered — real once a journey is active (derived from the
          route's real geometry + real elapsed time + real live traffic),
          honestly "not tracked" before that (see doc comment above). */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100">
          <CheckCircle2 className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Distance Covered
          </span>
          {started ? (
            <span className="font-extrabold text-slate-800 text-sm">
              {distanceCoveredDisplay} <span className="text-[10px] font-medium text-slate-500">km</span>
            </span>
          ) : (
            <span
              className="font-extrabold text-slate-400 text-sm"
              title="No live position feed before a journey starts."
            >
              Not tracked
            </span>
          )}
        </div>
      </div>

      <div className="h-6 w-px bg-slate-200 hidden sm:block" />

      {/* Route Distance (planned) / Distance Left (live once started) */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
          <MapPin className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">{distanceLabel}</span>
          <span className="font-extrabold text-emerald-700 text-sm">
            {distanceValue.toFixed(1)} <span className="text-[10px] font-medium text-slate-500">km</span>
          </span>
        </div>
      </div>

      {/* Est. Duration (planned) / Time Left (live once started) */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
          <Clock className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">{durationLabel}</span>
          <span className="font-extrabold text-amber-700 text-sm">
            {durationValue} <span className="text-[10px] font-medium text-slate-500">min</span>
          </span>
        </div>
      </div>

      {/* Est. Arrival — anchored to the real Start Journey moment once
          started; a preview (from now) before that. */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
          {journey.arrived ? <FlagOff className="w-3.5 h-3.5" /> : <Gauge className="w-3.5 h-3.5" />}
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            {journey.arrived ? "Arrived At" : "Est. Arrival"}
          </span>
          <span className="font-extrabold text-indigo-700 text-sm">{arrivalValue}</span>
        </div>
      </div>

      {/* Start Journey / live speed badge */}
      <div className="ml-auto flex items-center gap-2">
        {!started ? (
          <button
            onClick={onStartJourney}
            className="bg-sky-600 hover:bg-sky-700 text-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-sm font-bold text-xs uppercase tracking-wide transition-all"
          >
            <Play className="w-3.5 h-3.5" />
            Start Journey
          </button>
        ) : (
          <div className="bg-slate-900 text-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-sm">
            <span className="text-[10px] text-slate-400 uppercase font-bold">{speedCaption}:</span>
            <span className="font-extrabold text-sky-400 text-xs">{speedValue.toFixed(1)} km/h</span>
          </div>
        )}
      </div>

    </div>
  );
}
