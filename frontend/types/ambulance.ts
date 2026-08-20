import { GeoCoordinates } from "./common";

export type AmbulanceStatus = "idle" | "assigned" | "en_route_to_accident" | "at_accident" | "en_route_to_hospital" | "completed";

export interface Hospital {
  id: string;
  name: string;
  location: GeoCoordinates;
  availableBeds: number;
}

export interface Ambulance {
  id: string;
  callSign: string; // e.g. "Ambulance A-07"
  currentLocation: GeoCoordinates;
  status: AmbulanceStatus;
  speedKmh: number;
  assignedAccidentId?: string;
  destinationName?: string;
  destinationCoords?: GeoCoordinates;
  etaMinutes: number;
  routeCoordinates: GeoCoordinates[];
  hospitalDestination?: Hospital;
}
