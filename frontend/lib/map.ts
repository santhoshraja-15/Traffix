export interface GeoBounds {
  minLng: number;
  minLat: number;
  maxLng: number;
  maxLat: number;
}

export interface NetworkTopology {
  type: "FeatureCollection";
  name?: string;
  bbox?: [number, number, number, number];
  metadata?: { area?: string; nodes?: number; edges?: number };
  features: TopologyFeature[];
}

export interface TopologyFeature {
  type: "Feature";
  id?: string;
  properties: {
    edge_id: string;
    from?: string;
    to?: string;
    weight?: number;
    base_weight?: number;
    congestion?: number;
    length_m?: number;
  };
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
}

export function boundsFromTopology(topology: NetworkTopology, pad = 0.08): GeoBounds {
  if (topology.bbox && topology.bbox.length === 4) {
    const [minLng, minLat, maxLng, maxLat] = topology.bbox;
    const lngPad = (maxLng - minLng) * pad || 0.001;
    const latPad = (maxLat - minLat) * pad || 0.001;
    return {
      minLng: minLng - lngPad,
      minLat: minLat - latPad,
      maxLng: maxLng + lngPad,
      maxLat: maxLat + latPad,
    };
  }
  return { minLng: 80.205, minLat: 13.08, maxLng: 80.225, maxLat: 13.1 };
}

export function projectToViewBox(
  lng: number,
  lat: number,
  bounds: GeoBounds,
  width: number,
  height: number
): { x: number; y: number } {
  const x = ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * width;
  const y = (1 - (lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * height;
  return { x, y };
}

// ── Interactive camera (SVG-fallback map) ──────────────────────────────────
// The SVG renderer used whenever no real Mapbox token is configured (see
// TrafficMap.tsx — this project has never had one) previously projected
// every point through the network's full fixed bounds on every render, with
// no concept of pan/zoom at all: no wheel-zoom, no drag, no fit-to-route,
// and a "Reset Camera" button that called a Mapbox API which never existed
// in this mode. This section adds a real, minimal camera model — pan center
// + zoom scale, expressed as a lng/lat window derived from the network's
// reference bounds — so the existing SVG renderer gains genuine navigation-
// map interactivity without introducing a new mapping library.

export interface CameraState {
  lng: number;
  lat: number;
  /** 1 = the reference (fit-to-network) span; >1 zooms in, <1 zooms out. */
  scale: number;
}

export const MIN_MAP_SCALE = 0.6;
export const MAX_MAP_SCALE = 40;

export function clampScale(scale: number): number {
  return Math.min(MAX_MAP_SCALE, Math.max(MIN_MAP_SCALE, scale));
}

export function centerOfBounds(bounds: GeoBounds): { lng: number; lat: number } {
  return {
    lng: (bounds.minLng + bounds.maxLng) / 2,
    lat: (bounds.minLat + bounds.maxLat) / 2,
  };
}

/**
 * The lng/lat span (at scale=1) that exactly fills a container of the given
 * real on-screen aspect ratio, without stretching the network's shape —
 * grows whichever geographic axis (lng or lat) is proportionally shorter
 * than the container, rather than the old fixed-1000x720-viewBox approach
 * that always stretched to fill it regardless of the real panel's actual
 * shape (the direct cause of "network occupies only part of the viewport" —
 * a real container wider/shorter than 1000:720 was letterboxed by the SVG's
 * own preserveAspectRatio, wasting real screen space).
 *
 * `latCorrection` accounts for a degree of longitude covering less real
 * distance than a degree of latitude away from the equator (small but real
 * at Chennai's ~13°N) — without it, the network's true shape is skewed.
 */
export function baseSpanForAspect(
  referenceBounds: GeoBounds,
  containerAspect: number
): { lngSpan: number; latSpan: number } {
  const refLngSpan = referenceBounds.maxLng - referenceBounds.minLng;
  const refLatSpan = referenceBounds.maxLat - referenceBounds.minLat;
  const latCorrection = Math.cos(
    ((referenceBounds.minLat + referenceBounds.maxLat) / 2) * (Math.PI / 180)
  );
  const refAspect = (refLngSpan * latCorrection) / refLatSpan;

  if (containerAspect > refAspect) {
    return { lngSpan: (refLatSpan * containerAspect) / latCorrection, latSpan: refLatSpan };
  }
  return { lngSpan: refLngSpan, latSpan: (refLngSpan * latCorrection) / containerAspect };
}

/** The actual lng/lat window to render this frame, from the reference
 * (fit-to-network) bounds, the live camera (pan + zoom), and the real
 * container aspect ratio. */
export function computeViewBounds(
  referenceBounds: GeoBounds,
  camera: CameraState,
  containerAspect: number
): GeoBounds {
  const { lngSpan: baseLng, latSpan: baseLat } = baseSpanForAspect(referenceBounds, containerAspect);
  const lngSpan = baseLng / camera.scale;
  const latSpan = baseLat / camera.scale;
  return {
    minLng: camera.lng - lngSpan / 2,
    maxLng: camera.lng + lngSpan / 2,
    minLat: camera.lat - latSpan / 2,
    maxLat: camera.lat + latSpan / 2,
  };
}

/** Inverse of projectToViewBox — screen px -> lng/lat (drag-pan, zoom-at-cursor). */
export function unprojectFromViewBox(
  x: number,
  y: number,
  bounds: GeoBounds,
  width: number,
  height: number
): { lng: number; lat: number } {
  return {
    lng: bounds.minLng + (x / width) * (bounds.maxLng - bounds.minLng),
    lat: bounds.minLat + (1 - y / height) * (bounds.maxLat - bounds.minLat),
  };
}

/** Tight bounds around an arbitrary set of points, e.g. a route's real
 * coordinates — used for "fit route into view." */
export function boundsFromPoints(
  points: { lng: number; lat: number }[],
  pad = 0.25
): GeoBounds | null {
  if (points.length === 0) return null;
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
  for (const p of points) {
    if (p.lng < minLng) minLng = p.lng;
    if (p.lng > maxLng) maxLng = p.lng;
    if (p.lat < minLat) minLat = p.lat;
    if (p.lat > maxLat) maxLat = p.lat;
  }
  const lngPad = (maxLng - minLng) * pad || 0.003;
  const latPad = (maxLat - minLat) * pad || 0.003;
  return {
    minLng: minLng - lngPad,
    minLat: minLat - latPad,
    maxLng: maxLng + lngPad,
    maxLat: maxLat + latPad,
  };
}

/** The camera scale (relative to referenceBounds at scale=1) that makes
 * targetBounds fill the view — the more constraining axis wins, same
 * "fit bounds" logic real map libraries use. */
export function scaleToFit(
  referenceBounds: GeoBounds,
  targetBounds: GeoBounds,
  containerAspect: number
): number {
  const { lngSpan: baseLng, latSpan: baseLat } = baseSpanForAspect(referenceBounds, containerAspect);
  const targetLngSpan = Math.max(targetBounds.maxLng - targetBounds.minLng, 1e-9);
  const targetLatSpan = Math.max(targetBounds.maxLat - targetBounds.minLat, 1e-9);
  return clampScale(Math.min(baseLng / targetLngSpan, baseLat / targetLatSpan));
}

export function riskToColor(score: number): string {
  const t = Math.max(0, Math.min(1, score));
  const r = Math.round(34 + t * (239 - 34));
  const g = Math.round(197 + t * (68 - 197));
  const b = Math.round(94 + t * (68 - 94));
  return `rgb(${r},${g},${b})`;
}
