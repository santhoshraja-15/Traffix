export interface GeoBounds {
  minLng: number;
  minLat: number;
  maxLng: number;
  maxLat: number;
}

export interface NetworkTopology {
  type: "FeatureCollection";
  name?: string;
  bbox?: number[];
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

export function riskToColor(score: number): string {
  const t = Math.max(0, Math.min(1, score));
  const r = Math.round(34 + t * (239 - 34));
  const g = Math.round(197 + t * (68 - 197));
  const b = Math.round(94 + t * (68 - 94));
  return `rgb(${r},${g},${b})`;
}
