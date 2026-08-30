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
