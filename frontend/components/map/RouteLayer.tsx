"use client";

import { RouteOption } from "../../types/route";

interface RouteLayerProps {
  route?: RouteOption;
  alternativeRoutes?: RouteOption[];
}

export default function RouteLayer({ route }: RouteLayerProps) {
  if (!route) return null;

  return (
    <div className="contents">
      {/* Route Info Badge */}
      <div className="bg-sky-950/90 text-sky-200 border border-sky-700/60 px-2.5 py-1 rounded-lg text-[10px] font-bold shadow-md">
        <span>{route.name}</span>
        <span className="ml-1 text-white">({route.distanceKm.toFixed(1)} km)</span>
      </div>
    </div>
  );
}
