"use client";

import { RouteOption } from "@/types/route";
import { Star, Clock, MapPin, ShieldAlert, CheckCircle2, ChevronRight } from "lucide-react";

interface RouteComparisonProps {
  routes: RouteOption[];
  activeRouteId?: string;
  onSelectRoute?: (route: RouteOption) => void;
}

export default function RouteComparison({
  routes,
  activeRouteId,
  onSelectRoute,
}: RouteComparisonProps) {
  if (routes.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col gap-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <h3 className="font-extrabold text-xs text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
          <Star className="w-4 h-4 text-sky-500 fill-sky-500" />
          <span>ROUTE OPTIMIZATION COMPARISON</span>
        </h3>
        <span className="text-[10px] text-slate-400 font-semibold">
          XGBoost v15 Model Scored
        </span>
      </div>

      {/* Side by side comparison cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {routes.map((route) => {
          const isSelected = activeRouteId === route.id;
          return (
            <div
              key={route.id}
              onClick={() => onSelectRoute && onSelectRoute(route)}
              className={`p-3.5 rounded-xl border flex flex-col justify-between gap-3 cursor-pointer transition-all ${
                isSelected
                  ? "bg-sky-50/90 border-sky-400 shadow-md ring-2 ring-sky-400/20"
                  : "bg-slate-50/60 border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              <div>
                {/* Header tag */}
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-extrabold text-xs text-slate-900 truncate">
                    {route.name}
                  </span>
                  {route.isRecommended && (
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-sky-500 text-white shadow-xs">
                      RECOMMENDED
                    </span>
                  )}
                </div>

                {/* Main ETA & Distance */}
                <div className="flex items-baseline justify-between mb-2">
                  <div className="flex items-baseline gap-1">
                    <span className="text-xl font-extrabold text-slate-900">
                      {route.etaMinutes}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">min</span>
                  </div>
                  <span className="text-xs font-bold text-slate-600">
                    {route.distanceKm.toFixed(1)} km
                  </span>
                </div>

                {/* Metrics Breakdown */}
                <div className="space-y-1 text-[11px] text-slate-600 border-t border-slate-200/60 pt-2">
                  <div className="flex justify-between">
                    <span>Average Speed:</span>
                    <strong className="text-slate-900">{route.averageSpeedKmh.toFixed(1)} km/h</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Risk Exposure:</span>
                    <strong className={route.riskScore > 0.4 ? "text-red-600" : "text-emerald-700"}>
                      {(route.riskScore * 100).toFixed(0)}%
                    </strong>
                  </div>
                  <div className="flex justify-between">
                    <span>High-Risk Segments:</span>
                    <strong className="text-slate-900">{route.highRiskEdgesCount}</strong>
                  </div>
                </div>
              </div>

              {/* Stated Reasoning */}
              <div className="bg-white p-2 rounded-lg border border-slate-200/80 text-[10px] text-slate-600 leading-tight">
                <span className="font-bold text-slate-800">Reasoning: </span>
                {route.reasoning}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
