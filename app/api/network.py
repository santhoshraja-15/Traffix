"""Static road-network topology for the React map (no live stream)."""
from __future__ import annotations

from fastapi import APIRouter

from app.integrations.sumo_network_loader import get_named_locations
from app.models.route_models import LocationSuggestion, LocationsResponse
from app.routing.graph_manager import get_road_network_graph

router = APIRouter(tags=["network"])


@router.get("/network/topology")
async def get_network_topology() -> dict:
    """Return the Anna Nagar road graph as GeoJSON for the base map."""
    graph = get_road_network_graph()
    if not graph.is_initialized:
        graph.initialize_graph()
    return graph.to_geojson()


@router.get("/network/locations", response_model=LocationsResponse)
async def get_network_locations() -> LocationsResponse:
    """
    Real, searchable FROM/TO locations for the navigation search — one entry
    per unique real OSM street name found in the loaded network. Empty list
    if the real network isn't loaded (never a fabricated/hardcoded list).
    """
    raw = get_named_locations()
    return LocationsResponse(
        locations=[LocationSuggestion(**loc) for loc in raw]  # type: ignore[arg-type]
    )
