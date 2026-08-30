"use client";

import { Clock, MapPin, Gauge, CheckCircle2 } from "lucide-react";
import { NavigationState } from "../../types/navigation";

interface JourneyMetricsProps {
  metrics: Partial<NavigationState>;
}

export default function JourneyMetrics({ metrics }: JourneyMetricsProps) {
  const {
    distanceCoveredKm = 0,
    timeTakenMinutes = 0,
    distanceLeftKm = 0,
    timeLeftMinutes = 0,
    estimatedReachingTime = "—",
    currentSpeedKmh = 0,
  } = metrics;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
      
      {/* Distance Covered */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center border border-sky-100">
          <CheckCircle2 className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Distance Covered
          </span>
          <span className="font-extrabold text-slate-800 text-sm">
            {distanceCoveredKm.toFixed(1)} <span className="text-[10px] font-medium text-slate-500">km</span>
          </span>
        </div>
      </div>

      {/* Time Taken */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center border border-slate-200">
          <Clock className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Time Elapsed
          </span>
          <span className="font-extrabold text-slate-800 text-sm">
            {timeTakenMinutes} <span className="text-[10px] font-medium text-slate-500">min</span>
          </span>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-200 hidden sm:block" />

      {/* Distance Left */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
          <MapPin className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Distance Left
          </span>
          <span className="font-extrabold text-emerald-700 text-sm">
            {distanceLeftKm.toFixed(1)} <span className="text-[10px] font-medium text-slate-500">km</span>
          </span>
        </div>
      </div>

      {/* Time Left */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
          <Clock className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Time Left
          </span>
          <span className="font-extrabold text-amber-700 text-sm">
            {timeLeftMinutes} <span className="text-[10px] font-medium text-slate-500">min</span>
          </span>
        </div>
      </div>

      {/* Estimated Reaching Time */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
          <Gauge className="w-3.5 h-3.5" />
        </div>
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">
            Est. Arrival
          </span>
          <span className="font-extrabold text-indigo-700 text-sm">
            {estimatedReachingTime}
          </span>
        </div>
      </div>

      {/* Live Speed Badge */}
      <div className="ml-auto bg-slate-900 text-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-sm">
        <span className="text-[10px] text-slate-400 uppercase font-bold">Speed:</span>
        <span className="font-extrabold text-sky-400 text-xs">
          {currentSpeedKmh.toFixed(1)} km/h
        </span>
      </div>

    </div>
  );
}
