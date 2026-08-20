import { NetworkTopology, TopologyFeature } from "./map";

const ORIGIN_LAT = 13.085;
const ORIGIN_LNG = 80.2101;
const LAT_STEP = 0.0022;
const LNG_STEP = 0.0022;
const ROWS = 6;
const COLS = 6;

function nodeId(r: number, c: number): string {
  return `n${r}_${c}`;
}

function nodeCoord(r: number, c: number): [number, number] {
  return [ORIGIN_LNG + c * LNG_STEP, ORIGIN_LAT + r * LAT_STEP];
}

function makeEdge(from: string, to: string, a: [number, number], b: [number, number]): TopologyFeature {
  const edgeId = `${from}->${to}`;
  return {
    type: "Feature",
    id: edgeId,
    properties: { edge_id: edgeId, from, to },
    geometry: { type: "LineString", coordinates: [a, b] },
  };
}

function buildAnnaNagarTopology(): NetworkTopology {
  const features: TopologyFeature[] = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const here = nodeId(r, c);
      const hereXY = nodeCoord(r, c);
      if (c + 1 < COLS) {
        const east = nodeId(r, c + 1);
        const eastXY = nodeCoord(r, c + 1);
        features.push(makeEdge(here, east, hereXY, eastXY));
        features.push(makeEdge(east, here, eastXY, hereXY));
      }
      if (r + 1 < ROWS) {
        const south = nodeId(r + 1, c);
        const southXY = nodeCoord(r + 1, c);
        features.push(makeEdge(here, south, hereXY, southXY));
        features.push(makeEdge(south, here, southXY, hereXY));
      }
    }
  }

  const maxLng = ORIGIN_LNG + (COLS - 1) * LNG_STEP;
  const maxLat = ORIGIN_LAT + (ROWS - 1) * LAT_STEP;
  return {
    type: "FeatureCollection",
    name: "Anna Nagar Road Network",
    bbox: [ORIGIN_LNG, ORIGIN_LAT, maxLng, maxLat],
    metadata: { area: "Anna Nagar, Chennai", nodes: ROWS * COLS, edges: features.length },
    features,
  };
}

export const ANNA_NAGAR_TOPOLOGY: NetworkTopology = buildAnnaNagarTopology();
