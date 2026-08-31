import { GeoCoordinates } from "../types/common";

/**
 * Pure geometry for the active-journey vehicle marker (see
 * hooks/useJourneySimulation.ts). Every function here operates only on a
 * route's own real coordinates (RouteOption.coordinates — the actual
 * backend-returned polyline) — nothing here invents a shape or a position
 * that isn't a real point on that real polyline.
 */

const EARTH_RADIUS_M = 6371000;

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}
function toDeg(rad: number): number {
  return (rad * 180) / Math.PI;
}

export function haversineMeters(a: GeoCoordinates, b: GeoCoordinates): number {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function bearingDeg(a: GeoCoordinates, b: GeoCoordinates): number {
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const dLng = toRad(b.lng - a.lng);
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

/** Cumulative real distance (meters) at each coordinate index, from the
 * route's own real polyline — cumulative[0] === 0, cumulative[last] ===
 * total route length. */
export function cumulativeDistances(coords: GeoCoordinates[]): number[] {
  const cumulative: number[] = [0];
  for (let i = 0; i < coords.length - 1; i++) {
    cumulative.push(cumulative[i] + haversineMeters(coords[i], coords[i + 1]));
  }
  return cumulative;
}

export interface PositionOnRoute {
  position: GeoCoordinates;
  headingDeg: number;
  /** Index of the coordinate segment [index, index+1] this position falls
   * within — used to split the route into "traveled" vs "remaining". */
  segmentIndex: number;
}

/**
 * The real point on the route's own polyline at `distanceM` meters from the
 * start — linearly interpolated between the two real coordinates bounding
 * that distance (never a coordinate the route didn't actually pass
 * through). Heading is the real bearing of that segment.
 */
export function positionAtDistance(
  coords: GeoCoordinates[],
  cumulative: number[],
  distanceM: number
): PositionOnRoute {
  const total = cumulative[cumulative.length - 1] ?? 0;
  const d = Math.max(0, Math.min(distanceM, total));

  // Binary search for the segment containing d (coords can be long — this
  // runs every animation tick, so O(log n) matters more than O(n) here).
  let lo = 0;
  let hi = cumulative.length - 1;
  while (lo < hi - 1) {
    const mid = (lo + hi) >> 1;
    if (cumulative[mid] <= d) lo = mid;
    else hi = mid;
  }

  const segStart = cumulative[lo];
  const segEnd = cumulative[hi] ?? segStart;
  const segLen = segEnd - segStart;
  const t = segLen > 0 ? (d - segStart) / segLen : 0;

  const a = coords[lo];
  const b = coords[hi] ?? a;
  return {
    position: { lat: a.lat + (b.lat - a.lat) * t, lng: a.lng + (b.lng - a.lng) * t },
    headingDeg: bearingDeg(a, b),
    segmentIndex: lo,
  };
}

/** Split a route's real coordinates into the traveled prefix and remaining
 * suffix at `distanceM`, both ending/starting exactly at the real
 * interpolated vehicle position (so the two halves join with no gap and no
 * overlap) — for rendering the "covered" vs "remaining" route styling. */
export function splitRouteAtDistance(
  coords: GeoCoordinates[],
  cumulative: number[],
  distanceM: number
): { traveled: GeoCoordinates[]; remaining: GeoCoordinates[] } {
  if (coords.length < 2) return { traveled: [], remaining: coords.slice() };
  const { position, segmentIndex } = positionAtDistance(coords, cumulative, distanceM);
  const traveled = [...coords.slice(0, segmentIndex + 1), position];
  const remaining = [position, ...coords.slice(segmentIndex + 1)];
  return { traveled, remaining };
}
