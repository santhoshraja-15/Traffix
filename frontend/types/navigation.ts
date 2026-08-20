import { GeoCoordinates } from "./common";
import { RouteOption } from "./route";

export interface TurnInstruction {
  instruction: string; // e.g. "Turn right onto Anna Salai"
  distanceMeters: number;
  timeSeconds: number;
  turnType: "straight" | "left" | "right" | "u-turn" | "destination";
  roadName: string;
}

export interface NavigationState {
  isNavigating: boolean;
  originName: string;
  destinationName: string;
  originCoords?: GeoCoordinates;
  destinationCoords?: GeoCoordinates;
  currentPosition?: GeoCoordinates;
  currentSpeedKmh: number;
  activeRoute?: RouteOption;
  nextTurn?: TurnInstruction;
  distanceCoveredKm: number;
  distanceLeftKm: number;
  timeTakenMinutes: number;
  timeLeftMinutes: number;
  estimatedReachingTime: string;
  isRecalculating: boolean;
  statusMessage: string;
}
