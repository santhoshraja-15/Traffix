"use client";

import { RouteOption } from "../../types/route";
import { Star, Clock, MapPin, ShieldAlert, CheckCircle } from "lucide-react";
import { MOCK_ROUTES } from "../../lib/mockData";

interface TopRoutesProps {
  routes?: RouteOption[];
  selectedRouteId?: string;
  onSelectRoute?: (route: RouteOption) => void;
}

export default function TopRoutes({
  routes = MOCK_ROUTES,
  selectedRouteId = "route-1",
  onSelectRoute,
}: TopRoutesProps) {

  const getCongestionBadge = (congestion: string) => {
    switch (congestion) {
      case "low":
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Low</span>;
      case "moderate":
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">Moderate</span>;
      case "high":
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-50 text-orange-700 border border-orange-200">High</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700 border border-red-200">Congested</span>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm flex flex-col gap-2">
      
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <div className="flex items-center gap-1.5">
          <Star className="w-4 h-4 text-sky-500 fill-sky-500" />
          <h3 className="font-extrabold text-xs tracking-wide text-slate-900 uppercase">
            TOP ROUTES
          </h3>
        </div>
        <span className="text-[10px] text-slate-400 font-semibold">
          XGBoost Risk Scored
        </span>
      </div>

      {/* Table Headers (Time | Traffic Density | Distance) */}
      <div className="grid grid-cols-12 gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1 bg-slate-50 rounded-lg">
        <div className="col-span-5">Route Name</div>
        <div className="col-span-2 text-center">Time</div>
        <div className="col-span-3 text-center">Traffic Density</div>
        <div className="col-span-2 text-right">Distance</div>
      </div>

      {/* Route List Items */}
      <div className="flex flex-col gap-1.5">
        {routes.map((route) => {
          const isSelected = selectedRouteId === route.id;
          return (
            <div
              key={route.id}
              onClick={() => onSelectRoute && onSelectRoute(route)}
              className={`grid grid-cols-12 gap-2 items-center px-2.5 py-2 rounded-lg cursor-pointer transition-all border ${
                isSelected
                  ? "bg-sky-50/80 border-sky-300 shadow-sm"
                  : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              {/* Route Name + Recommended Tag */}
              <div className="col-span-5 flex flex-col">
                <div className="flex items-center gap-1">
                  {route.isRecommended && (
                    <Star className="w-3 h-3 text-amber-500 fill-amber-500 shrink-0" />
                  )}
                  <span className="font-bold text-xs text-slate-800 truncate">
                    {route.name}
                  </span>
                </div>
                {route.isRecommended && (
                  <span className="text-[9px] font-semibold text-sky-600">
                    ★ Recommended
                  </span>
                )}
              </div>

              {/* Time */}
              <div className="col-span-2 text-center font-extrabold text-xs text-slate-800">
                {route.etaMinutes} <span className="text-[10px] text-slate-500 font-normal">min</span>
              </div>

              {/* Traffic Density */}
              <div className="col-span-3 text-center">
                {getCongestionBadge(route.congestion)}
              </div>

              {/* Distance */}
              <div className="col-span-2 text-right font-bold text-xs text-slate-700">
                {route.distanceKm.toFixed(1)} <span className="text-[10px] text-slate-400">km</span>
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
