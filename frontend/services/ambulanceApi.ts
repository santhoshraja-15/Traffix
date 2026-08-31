import { apiGet } from "./api";
import { LocationSuggestion } from "../types/route";

interface ApiHospital {
  id: string;
  name: string;
  location: { lat: number; lng: number };
}

/** Real hospitals in Anna Nagar — extracted from the project's own OSM
 * source data (app/integrations/osm_poi_loader.py), not invented. */
export async function fetchRealHospitals(): Promise<LocationSuggestion[]> {
  const result = await apiGet<{ hospitals: ApiHospital[] }>("/emergency/hospitals");
  return result.hospitals.map((h) => ({
    name: h.name,
    lat: h.location.lat,
    lng: h.location.lng,
    edge_id: "", // hospitals are points, not edges — unused here
  }));
}

export interface AmbulanceUnit {
  ambulance_id: string;
  unit_number: string;
  hospital_name: string;
  status: "available" | "dispatched" | "at_scene" | "returning" | string;
}

/** The real ambulance fleet — one unit per real hospital, including idle
 * units with no active mission (see app/emergency/ambulance_manager.py).
 * The live WebSocket stream only carries missions currently in progress;
 * this REST call is the only way to see the whole fleet's real status. */
export async function fetchAmbulanceUnits(): Promise<AmbulanceUnit[]> {
  const result = await apiGet<{ units: AmbulanceUnit[] }>("/ambulance/units");
  return result.units;
}
