import { GeoCoordinates } from "@/types/common";
import { TurnInstruction } from "@/types/navigation";

/**
 * Real turn-by-turn directions, derived entirely from a route's own real
 * geometry (RouteOption.coordinates — the actual polyline the backend
 * returned) and its real ordered street names (RouteOption.roadNames).
 *
 * There is no live GPS/position feed for the person planning a route in
 * this app (unlike vehicles/ambulances, which have real simulated
 * positions from SUMO) — this is a route-planning dashboard, not an
 * in-car GPS tracker. So "next instruction" can't mean "your live
 * position vs. the next turn"; instead this computes the route's real
 * maneuvers up front from its real shape, honestly.
 *
 * Turn direction and distance are computed from real haversine bearings
 * and distances between the route's actual coordinate points — never
 * guessed. Each instruction is labeled with the nearest real street name
 * by proportional position along the route (an honest best-effort
 * placement, not a claim of exact per-coordinate street attribution).
 */

const EARTH_RADIUS_M = 6371000;
const MIN_TURN_ANGLE_DEG = 25; // below this, geometry noise, not a real turn
const MIN_SEGMENT_METERS = 40; // ignore turns detected over near-zero distance

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function toDeg(rad: number): number {
  return (rad * 180) / Math.PI;
}

function haversineMeters(a: GeoCoordinates, b: GeoCoordinates): number {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(h)));
}

function bearingDeg(a: GeoCoordinates, b: GeoCoordinates): number {
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const dLng = toRad(b.lng - a.lng);
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

/** Signed smallest angle from `from` to `to`, in (-180, 180]. Positive = turning right (clockwise). */
function angleDelta(from: number, to: number): number {
  let delta = to - from;
  while (delta > 180) delta -= 360;
  while (delta <= -180) delta += 360;
  return delta;
}

function roadNameAt(roadNames: string[], fractionAlongRoute: number): string {
  if (roadNames.length === 0) return "";
  const idx = Math.min(roadNames.length - 1, Math.floor(fractionAlongRoute * roadNames.length));
  return roadNames[idx];
}

export function buildTurnInstructions(
  coordinates: GeoCoordinates[],
  roadNames: string[]
): TurnInstruction[] {
  if (coordinates.length < 2) return [];

  // Real per-segment distance and cumulative distance from real geometry.
  const segmentMeters: number[] = [];
  let totalMeters = 0;
  for (let i = 0; i < coordinates.length - 1; i++) {
    const d = haversineMeters(coordinates[i], coordinates[i + 1]);
    segmentMeters.push(d);
    totalMeters += d;
  }

  const instructions: TurnInstruction[] = [];
  let cumulativeMeters = 0;
  let lastBearing: number | null = null;
  let distanceSinceLastInstruction = 0;

  instructions.push({
    instruction: `Head toward ${roadNameAt(roadNames, 0) || "your destination"}`,
    distanceMeters: Math.round(segmentMeters[0] ?? 0),
    timeSeconds: 0, // filled in by the caller from the route's real average speed
    turnType: "straight",
    roadName: roadNameAt(roadNames, 0),
  });

  for (let i = 0; i < coordinates.length - 2; i++) {
    const bearing = bearingDeg(coordinates[i], coordinates[i + 1]);
    const nextBearing = bearingDeg(coordinates[i + 1], coordinates[i + 2]);
    cumulativeMeters += segmentMeters[i];
    distanceSinceLastInstruction += segmentMeters[i];

    if (lastBearing === null) {
      lastBearing = bearing;
      continue;
    }

    const delta = angleDelta(bearing, nextBearing);
    if (Math.abs(delta) >= MIN_TURN_ANGLE_DEG && distanceSinceLastInstruction >= MIN_SEGMENT_METERS) {
      const fraction = totalMeters > 0 ? cumulativeMeters / totalMeters : 0;
      const roadName = roadNameAt(roadNames, fraction);
      const turnType = delta > 0 ? "right" : "left";
      instructions.push({
        instruction: roadName ? `Turn ${turnType} onto ${roadName}` : `Turn ${turnType}`,
        distanceMeters: Math.round(distanceSinceLastInstruction),
        timeSeconds: 0,
        turnType,
        roadName,
      });
      distanceSinceLastInstruction = 0;
    }
    lastBearing = nextBearing;
  }

  const destinationName = roadNameAt(roadNames, 1);
  instructions.push({
    instruction: destinationName ? `Arrive via ${destinationName}` : "Arrive at destination",
    distanceMeters: Math.round(segmentMeters[segmentMeters.length - 1] ?? 0),
    timeSeconds: 0,
    turnType: "destination",
    roadName: destinationName,
  });

  return instructions;
}
