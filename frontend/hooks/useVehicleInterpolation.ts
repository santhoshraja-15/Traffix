"use client";

/**
 * useVehicleInterpolation(vehicles)
 * ====================================
 * Implements ANIMATED_EFFECTS.md §2's vehicle-movement rule: tween smoothly
 * toward each vehicle's next real reported position over the expected
 * update interval (the backend broadcasts once per second — see
 * FRONTEND_AUDIT.md §1.2), purely for visual continuity — never extrapolate
 * a guessed future position, and always snap/correct immediately if a new
 * real update arrives before the previous tween finishes.
 *
 * Input `vehicles` is the latest AUTHORITATIVE snapshot from the real
 * WebSocket stream (StreamVehicle[], see hooks/useWebSocket.ts) — this hook
 * never invents a vehicle or a position that wasn't reported.
 */

import { useEffect, useRef, useState } from "react";
import type { StreamVehicle } from "./useWebSocket";
import type { Vehicle } from "../types/traffic";

// Matches SimulationManager's broadcast cadence (app/core/simulation_manager.py).
const EXPECTED_UPDATE_INTERVAL_MS = 1000;

interface TweenState {
  fromLat: number;
  fromLng: number;
  fromHeading: number;
  toLat: number;
  toLng: number;
  toHeading: number;
  startedAt: number;
  speedKmh: number;
  edgeId: string;
}

function shortestHeadingDelta(from: number, to: number): number {
  let delta = (to - from) % 360;
  if (delta > 180) delta -= 360;
  if (delta < -180) delta += 360;
  return delta;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function useVehicleInterpolation(vehicles: StreamVehicle[]): Vehicle[] {
  const tweens = useRef<Map<string, TweenState>>(new Map());
  const [rendered, setRendered] = useState<Vehicle[]>([]);
  const rafRef = useRef<number | null>(null);

  // A new authoritative snapshot arrived — (re)target every tween, snapping
  // immediately for vehicles the previous tween hadn't finished reaching.
  useEffect(() => {
    const now = performance.now();
    const seen = new Set<string>();

    for (const v of vehicles) {
      seen.add(v.id);
      const existing = tweens.current.get(v.id);

      if (!existing) {
        // Brand-new vehicle — appear at its real position immediately,
        // nothing to tween from.
        tweens.current.set(v.id, {
          fromLat: v.lat, fromLng: v.lng, fromHeading: v.heading,
          toLat: v.lat, toLng: v.lng, toHeading: v.heading,
          startedAt: now, speedKmh: v.speed_kmh, edgeId: v.edge_id,
        });
        continue;
      }

      // Snap: start the new tween from wherever the vehicle actually is
      // right now (mid-tween or not), never from a stale target.
      const elapsed = now - existing.startedAt;
      const t = Math.min(1, elapsed / EXPECTED_UPDATE_INTERVAL_MS);
      const currentLat = lerp(existing.fromLat, existing.toLat, t);
      const currentLng = lerp(existing.fromLng, existing.toLng, t);
      const currentHeading = existing.fromHeading + shortestHeadingDelta(existing.fromHeading, existing.toHeading) * t;

      tweens.current.set(v.id, {
        fromLat: currentLat, fromLng: currentLng, fromHeading: currentHeading,
        toLat: v.lat, toLng: v.lng, toHeading: v.heading,
        startedAt: now, speedKmh: v.speed_kmh, edgeId: v.edge_id,
      });
    }

    // Vehicles no longer reported (left the network) — remove their marker.
    for (const id of tweens.current.keys()) {
      if (!seen.has(id)) tweens.current.delete(id);
    }
  }, [vehicles]);

  // Continuous rAF loop — purely visual interpolation, never invents a
  // position beyond the current tween's real target.
  //
  // Bug fixed here: this used to call setRendered(next) unconditionally on
  // EVERY frame (up to 60fps), even when there were zero vehicles to
  // animate — `next` is a fresh array reference each tick, so React never
  // bails out on equality, and every TrafficMap consumer (the whole SVG
  // fallback tree, including all ~3187 road paths) re-rendered continuously
  // as a result. Since mock mode (this project's mode the entire session —
  // "MOCK SIMULATION MODE" — real per-vehicle data only exists once SUMO is
  // connected) always reports zero vehicles, this ran at up to 60fps
  // forever on every load. Now skipped whenever there's nothing to animate,
  // with exactly one settle-to-empty commit on the real 0-vehicle
  // transition so a departing fleet still visibly clears.
  useEffect(() => {
    let wasEmpty = true; // `rendered` starts as []
    const tick = () => {
      if (tweens.current.size === 0) {
        if (!wasEmpty) {
          setRendered([]);
          wasEmpty = true;
        }
        rafRef.current = requestAnimationFrame(tick);
        return;
      }
      wasEmpty = false;

      const now = performance.now();
      const next: Vehicle[] = [];

      tweens.current.forEach((tw, id) => {
        const t = Math.min(1, (now - tw.startedAt) / EXPECTED_UPDATE_INTERVAL_MS);
        next.push({
          id,
          position: {
            lat: lerp(tw.fromLat, tw.toLat, t),
            lng: lerp(tw.fromLng, tw.toLng, t),
          },
          headingAngle: tw.fromHeading + shortestHeadingDelta(tw.fromHeading, tw.toHeading) * t,
          speedKmh: tw.speedKmh,
          roadId: tw.edgeId,
          waitingTimeSec: 0,
        });
      });

      setRendered(next);
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return rendered;
}
