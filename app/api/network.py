"""Static road-network topology for the React map (no live stream)."""
from __future__ import annotations

from fastapi import APIRouter

from app.routing.graph_manager import get_road_network_graph

router = APIRouter(tags=["network"])


@router.get("/network/topology")
async def get_network_topology() -> dict:
    """Return the Anna Nagar road graph as GeoJSON for the base map."""
    graph = get_road_network_graph()
    if not graph.is_initialized:
        graph.initialize_graph()
    return graph.to_geojson()
