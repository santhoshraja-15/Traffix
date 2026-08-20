import { apiRequest } from "./api";
import { Ambulance } from "../types/ambulance";
import { MOCK_AMBULANCES, MOCK_HOSPITALS } from "../lib/mockData";

export async function fetchAmbulances(): Promise<Ambulance[]> {
  try {
    return await apiRequest<Ambulance[]>("/ambulances");
  } catch (err) {
    return MOCK_AMBULANCES;
  }
}

export async function dispatchAmbulance(
  accidentId: string
): Promise<Ambulance> {
  try {
    return await apiRequest<Ambulance>("/ambulance/dispatch", {
      method: "POST",
      body: JSON.stringify({ accidentId }),
    });
  } catch (err) {
    console.warn("[TRAFFIX] Backend unavailable, dispatching mock Ambulance A-07");
    return {
      ...MOCK_AMBULANCES[0],
      status: "assigned",
      assignedAccidentId: accidentId,
      destinationName: "Accident Scene (Teynampet Junction)",
      destinationCoords: { lat: 13.0215, lng: 80.2210 },
      etaMinutes: 3,
      speedKmh: 55,
      routeCoordinates: [
        { lat: 13.0382, lng: 80.2458 },
        { lat: 13.0298, lng: 80.2335 },
        { lat: 13.0215, lng: 80.2210 },
      ],
      hospitalDestination: MOCK_HOSPITALS[0],
    };
  }
}
