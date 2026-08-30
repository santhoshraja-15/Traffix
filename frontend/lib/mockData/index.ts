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
