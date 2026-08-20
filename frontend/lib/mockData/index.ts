import { RouteOption, RouteSearchResult } from "../../types/route";
import { TrafficStateSnapshot, Vehicle, RoadSegment, TrafficSignal } from "../../types/traffic";
import { Accident } from "../../types/accident";
import { Ambulance, Hospital } from "../../types/ambulance";
import { IntelligenceMessage } from "../../types/common";

/* -------------------------------------------------------------------------- */
/*  MOCK DATA: Centralized Mock Repository for TRAFFIX Frontend               */
/* -------------------------------------------------------------------------- */

export const MOCK_INITIAL_MESSAGES: IntelligenceMessage[] = [
  {
    id: "msg-1",
    timestamp: "16:45:00",
    type: "system",
    text: "TRAFFIX Engine Initialized",
    details: "Connected to SUMO TraCI Simulation stream.",
  },
  {
    id: "msg-2",
    timestamp: "16:45:02",
    type: "info",
    text: "Observing Anna Salai Traffic Network",
    details: "142 active vehicles tracked across 38 road segments.",
  },
];

export const MOCK_HOSPITALS: Hospital[] = [
  {
    id: "hosp-1",
    name: "Apollo Hospital (Greams Road)",
    location: { lat: 13.0603, lng: 80.2529 },
    availableBeds: 14,
  },
  {
    id: "hosp-2",
    name: "MGM Healthcare (Aminjikarai)",
    location: { lat: 13.0722, lng: 80.2241 },
    availableBeds: 8,
  },
  {
    id: "hosp-3",
    name: "MIOT International (Manapakkam)",
    location: { lat: 13.0232, lng: 80.1873 },
    availableBeds: 21,
  },
];

export const MOCK_AMBULANCES: Ambulance[] = [
  {
    id: "amb-1",
    callSign: "Ambulance A-07",
    currentLocation: { lat: 13.0382, lng: 80.2458 },
    status: "idle",
    speedKmh: 0,
    etaMinutes: 0,
    routeCoordinates: [],
  },
  {
    id: "amb-2",
    callSign: "Ambulance B-12",
    currentLocation: { lat: 13.0185, lng: 80.2195 },
    status: "idle",
    speedKmh: 0,
    etaMinutes: 0,
    routeCoordinates: [],
  },
];

export const MOCK_ROUTES: RouteOption[] = [
  {
    id: "route-1",
    name: "Route 1 (Anna Salai Direct)",
    roadName: "Anna Salai Direct",
    coordinates: [
      { lat: 13.0067, lng: 80.2020 },
      { lat: 13.0215, lng: 80.2210 },
      { lat: 13.0382, lng: 80.2458 },
      { lat: 13.0522, lng: 80.2505 },
    ],
    roadIds: ["road_anna_1", "road_anna_2", "road_anna_3"],
    distanceKm: 4.2,
    etaMinutes: 12,
    averageSpeedKmh: 38.5,
    congestion: "low",
    riskScore: 0.12,
    score: 94.5,
    isRecommended: true,
    reasoning: "Fastest flow with 0 predicted bottlenecks on XGBoost Risk Engine.",
    highRiskEdgesCount: 0,
  },
  {
    id: "route-2",
    name: "Route 2 (Mount Flyover Bypass)",
    roadName: "Mount Flyover Bypass",
    coordinates: [
      { lat: 13.0067, lng: 80.2020 },
      { lat: 13.0185, lng: 80.2195 },
      { lat: 13.0335, lng: 80.2380 },
      { lat: 13.0522, lng: 80.2505 },
    ],
    roadIds: ["road_mount_1", "road_mount_2"],
    distanceKm: 4.8,
    etaMinutes: 15,
    averageSpeedKmh: 32.0,
    congestion: "moderate",
    riskScore: 0.28,
    score: 82.0,
    isRecommended: false,
    reasoning: "Alternative path with moderate queue build-up at Saidapet junction.",
    highRiskEdgesCount: 1,
  },
  {
    id: "route-3",
    name: "Route 3 (Inner Ring Road Detour)",
    roadName: "Inner Ring Road Detour",
    coordinates: [
      { lat: 13.0067, lng: 80.2020 },
      { lat: 13.0290, lng: 80.2100 },
      { lat: 13.0450, lng: 80.2310 },
      { lat: 13.0522, lng: 80.2505 },
    ],
    roadIds: ["road_ring_1", "road_ring_2", "road_ring_3"],
    distanceKm: 5.6,
    etaMinutes: 19,
    averageSpeedKmh: 28.4,
    congestion: "high",
    riskScore: 0.54,
    score: 68.0,
    isRecommended: false,
    reasoning: "Longer distance with heavy signal delays near Guindy West.",
    highRiskEdgesCount: 2,
  },
];

export const MOCK_ROUTE_SEARCH_RESULT: RouteSearchResult = {
  shortestRoute: MOCK_ROUTES[0],
  optimalRoutes: MOCK_ROUTES,
  recommendedRoute: MOCK_ROUTES[0],
  timestamp: new Date().toISOString(),
};

export const MOCK_TRAFFIC_SNAPSHOT: TrafficStateSnapshot = {
  timestamp: new Date().toISOString(),
  step: 420,
  totalVehicles: 142,
  averageSpeedKmh: 36.2,
  stoppedVehicles: 12,
  averageWaitingTimeSec: 8.4,
  congestionLevel: "low",
  roads: {
    road_anna_1: {
      id: "road_anna_1",
      name: "Anna Salai Sec 1",
      coordinates: [
        { lat: 13.0067, lng: 80.2020 },
        { lat: 13.0215, lng: 80.2210 },
      ],
      congestion: "low",
      averageSpeedKmh: 42.0,
      vehicleCount: 24,
      riskScore: 0.08,
    },
    road_anna_2: {
      id: "road_anna_2",
      name: "Anna Salai Sec 2 (Teynampet)",
      coordinates: [
        { lat: 13.0215, lng: 80.2210 },
        { lat: 13.0382, lng: 80.2458 },
      ],
      congestion: "moderate",
      averageSpeedKmh: 34.0,
      vehicleCount: 38,
      riskScore: 0.22,
    },
  },
  vehicles: [
    {
      id: "v-101",
      position: { lat: 13.0120, lng: 80.2090 },
      speedKmh: 40.5,
      roadId: "road_anna_1",
      type: "passenger",
      waitingTimeSec: 0,
      headingAngle: 45,
    },
    {
      id: "v-102",
      position: { lat: 13.0250, lng: 80.2260 },
      speedKmh: 32.0,
      roadId: "road_anna_2",
      type: "passenger",
      waitingTimeSec: 3.5,
      headingAngle: 45,
    },
  ],
  signals: [
    {
      id: "sig-1",
      name: "Saidapet Signal",
      location: { lat: 13.0215, lng: 80.2210 },
      state: "green",
      cycleTimeSec: 60,
      remainingPhaseSec: 18,
    },
    {
      id: "sig-2",
      name: "Teynampet Junction Signal",
      location: { lat: 13.0382, lng: 80.2458 },
      state: "red",
      cycleTimeSec: 90,
      remainingPhaseSec: 12,
    },
  ],
};
