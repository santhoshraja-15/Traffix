"use client";

import { Clock, MapPin, Gauge, CheckCircle2, Play } from "lucide-react";
import { RouteOption } from "../../types/route";

interface JourneyMetricsProps {
  route: RouteOption;
  /** Real wall-clock timestamp (Date.now()) of the last "Start Journey"
   * click, or null before it's been clicked / after a different route was
   * selected (see app/page.tsx's reset-on-route-change effect). Never a
   * guessed/simulated value. */
  journeyStartedAt: number | null;
  /** Real elapsed minutes since journeyStartedAt, ticking once per second —
   * null exactly when journeyStartedAt is null. This is the one field on
   * this panel that is genuinely live; see the honesty note below. */
  elapsedMinutes: number | null;
  onStartJourney: () => void;
}

/**
 * Honesty note (see the frontend repair project's "journey progress"
 * finding): there is no live GPS/position feed for the person planning a
 * route here — unlike SUMO's bulk vehicles or the emergency mission
 * system's real tick-interpolated position, nothing in the backend tracks
 * an ordinary user's progress along their chosen route. So:
 *  - Time Elapsed is genuinely real (wall-clock time since Start Journey).
 *  - Distance Covered cannot be honestly derived at all without a position
 *    feed — shown as "not tracked" rather than a fake/frozen number.
 *  - Route Distance / Est. Duration / Avg Speed / Est. Arrival are the
 *    route's real planned figures (from the backend's routing computation),
 *    labeled "planned" so they don't read as a live-decrementing countdown
 *    they aren't.
 */
export default function JourneyMetrics({ route, journeyStartedAt, elapsedMinutes, onStartJourney }: JourneyMetricsProps) {
  const started = journeyStartedAt !== null;

  const estimatedReachingTime = new Date(
    (journeyStartedAt ?? Date.now()) + route.etaMinutes * 60_000
  ).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });

  const elapsedDisplay = (() => {
    if (elapsedMinutes === null) return "—";
    const totalSeconds = Math.max(0, Math.round(elapsedMinutes * 60));
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  })();

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">

      {/* Time Elapsed — the one genuinely live field on this panel */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center border border-slate-200">
          <Clock className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase flex items-center gap-1 tracking-wider">
            Time Elapsed
            {started && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
          </span>
          <span className="font-extrabold text-slate-800 text-sm">{elapsedDisplay}</span>
        </div>
      </div>

      {/* Distance Covered — honestly not trackable without a live position
          feed (see doc comment above); never a frozen fake number. */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100">
          <CheckCircle2 className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Distance Covered
          </span>
          <span className="font-extrabold text-slate-400 text-sm" title="No live position feed for this trip — only real elapsed time can be shown honestly.">
            Not tracked
          </span>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-200 hidden sm:block" />

      {/* Route Distance — the route's real planned total, not a live-
          decrementing "remaining" figure. */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
          <MapPin className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Route Distance
          </span>
          <span className="font-extrabold text-emerald-700 text-sm">
            {route.distanceKm.toFixed(1)} <span className="text-[10px] font-medium text-slate-500">km</span>
          </span>
        </div>
      </div>

      {/* Est. Duration — the route's real planned total travel time. */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
          <Clock className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Est. Duration
          </span>
          <span className="font-extrabold text-amber-700 text-sm">
            {Math.round(route.etaMinutes)} <span className="text-[10px] font-medium text-slate-500">min</span>
          </span>
        </div>
      </div>

      {/* Est. Arrival — anchored to the real Start Journey moment once
          started; a preview (from now) before that. */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
          <Gauge className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Est. Arrival
          </span>
          <span className="font-extrabold text-indigo-700 text-sm">{estimatedReachingTime}</span>
        </div>
      </div>

      {/* Start Journey / planned-speed badge */}
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
            <span className="text-[10px] text-slate-400 uppercase font-bold">Avg Speed (planned):</span>
            <span className="font-extrabold text-sky-400 text-xs">
              {route.averageSpeedKmh.toFixed(1)} km/h
            </span>
          </div>
        )}
      </div>

    </div>
  );
}
