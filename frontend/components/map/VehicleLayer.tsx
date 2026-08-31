"use client";

import { Vehicle } from "../../types/traffic";
import type { GeoBounds } from "../../lib/map";
import { projectToViewBox } from "../../lib/map";

interface VehicleLayerProps {
  vehicles: Vehicle[];
  bounds: GeoBounds;
  width: number;
  height: number;
}

/**
 * SVG-fallback vehicle renderer (used when no Mapbox token is configured —
 * see TrafficMap.tsx). Each vehicle is positioned from its own real/
 * interpolated lat/lng, not a shared hardcoded offset.
 */
export default function VehicleLayer({ vehicles, bounds, width, height }: VehicleLayerProps) {
  if (vehicles.length === 0) return null;

  return (
    <>
      {vehicles.map((v) => {
        const { x, y } = projectToViewBox(v.position.lng, v.position.lat, bounds, width, height);
        const heading = v.headingAngle ?? 0;
        return (
          <g key={v.id} transform={`translate(${x.toFixed(1)}, ${y.toFixed(1)})`}>
            <title>{`Vehicle ${v.id} — ${v.speedKmh.toFixed(1)} km/h on ${v.roadId}`}</title>
            <circle r={4} fill="#34d399" stroke="#0f172a" strokeWidth={1} />
            <path
              d="M 0 -6 L 3 0 L 0 -1.5 L -3 0 Z"
              fill="#34d399"
              transform={`rotate(${heading})`}
            />
          </g>
        );
      })}
    </>
  );
}
