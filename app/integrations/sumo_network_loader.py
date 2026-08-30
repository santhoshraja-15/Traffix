"""
Real Anna Nagar SUMO network loader.

Parses the actual netconvert-produced network file (``scenarios/medium/
osm.net.xml.gz`` — the same file ``SumoBridge`` connects TraCI to, so edge
IDs learned here are guaranteed to match what TraCI reports at runtime) via
``sumolib`` — a pure-Python package that reads/queries a SUMO network
without requiring a running SUMO process or the ``traci`` package. Only the
coordinate conversion needs an extra dependency (``pyproj``, for the
UTM→WGS84 inverse projection the network's own ``<location>`` metadata
specifies) — never a hand-guessed offset/scale, per
``TECHNICAL_DEEP_DIVE.md`` §4.

Loaded once and cached: parsing ~1200 nodes / ~3200 edges takes well under a
second, so every caller (the static topology graph, and per-tick vehicle
position conversion in ``SumoBridge``) shares one instance instead of each
re-parsing the file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.utils.logging import get_logger

logger = get_logger(__name__)

# The exact file SumoBridge.connect() launches TraCI against
# (scenarios/medium/traffic.sumocfg's <net-file>) — see FRONTEND_AUDIT.md §1.3.
DEFAULT_NET_PATH = Path(__file__).resolve().parents[2] / "scenarios" / "medium" / "osm.net.xml.gz"


class NetworkLoadError(RuntimeError):
    """Raised when the real network can't be parsed — callers should fall back gracefully."""


@dataclass
class RealNode:
    node_id: str
    lat: float
    lng: float


@dataclass
class RealEdge:
    edge_id: str
    from_node: str
    to_node: str
    length_m: float
    speed_limit_kmh: float
    lane_count: int
    shape: List[Tuple[float, float]]  # [(lng, lat), ...] — full geometry, not just endpoints
    # Real OSM street name, when netconvert kept one (~44% of edges in the
    # Anna Nagar network do) — e.g. "Park Road", "Thiruvalluvar Street".
    # Empty string when the edge has none; never invented.
    name: str = ""


@dataclass
class RealNetwork:
    nodes: List[RealNode]
    edges: List[RealEdge]
    bbox: Tuple[float, float, float, float]  # (min_lng, min_lat, max_lng, max_lat)
    # The underlying sumolib Net, kept so SumoBridge can convert live vehicle
    # positions with the exact same projection — never re-derive it.
    net: object = field(repr=False)


_cached_network: Optional[RealNetwork] = None
_load_attempted: bool = False


def load_real_network(net_path: Path = DEFAULT_NET_PATH) -> RealNetwork:
    """
    Parse *net_path* into a ``RealNetwork``. Raises ``NetworkLoadError`` on
    any failure (missing file, missing sumolib/pyproj, unparseable network,
    network without geo-projection metadata) — callers decide the fallback.
    """
    try:
        import sumolib  # noqa: PLC0415 — optional dependency, imported lazily
    except ImportError as exc:
        raise NetworkLoadError(
            "sumolib is not installed — add it to requirements.txt / the venv."
        ) from exc

    if not net_path.exists():
        raise NetworkLoadError(f"Network file not found: {net_path}")

    try:
        net = sumolib.net.readNet(str(net_path))
    except Exception as exc:  # noqa: BLE001
        raise NetworkLoadError(f"Failed to parse {net_path}: {exc}") from exc

    def to_lonlat(x: float, y: float) -> Tuple[float, float]:
        try:
            return net.convertXY2LonLat(x, y)
        except Exception as exc:  # noqa: BLE001
            raise NetworkLoadError(
                f"Network has no usable geo-projection ({exc}) — "
                "is pyproj installed and does the net have a <location> tag?"
            ) from exc

    nodes: List[RealNode] = []
    for sumo_node in net.getNodes():
        x, y = sumo_node.getCoord()
        lng, lat = to_lonlat(x, y)
        nodes.append(RealNode(node_id=sumo_node.getID(), lat=lat, lng=lng))

    edges: List[RealEdge] = []
    seen_pairs: set[Tuple[str, str]] = set()
    skipped_duplicates = 0
    for sumo_edge in net.getEdges():
        # getEdges() already excludes internal (":"-prefixed) junction edges
        # by default — matches SumoBridge's own filter, kept here for safety.
        if sumo_edge.getID().startswith(":"):
            continue

        from_id = sumo_edge.getFromNode().getID()
        to_id = sumo_edge.getToNode().getID()
        pair = (from_id, to_id)
        if pair in seen_pairs:
            # A handful of junction pairs have >1 parallel edge in this
            # network (58 of 3245, spot-checked during Phase 3 audit). The
            # graph is a plain nx.DiGraph (one edge per (u, v)) — an
            # intentional existing choice, not something to silently change
            # here — so keep the first edge seen and log the rest.
            skipped_duplicates += 1
            continue
        seen_pairs.add(pair)

        shape_xy = sumo_edge.getShape()
        shape_lonlat = [to_lonlat(x, y) for x, y in shape_xy]

        edges.append(
            RealEdge(
                edge_id=sumo_edge.getID(),
                from_node=from_id,
                to_node=to_id,
                length_m=float(sumo_edge.getLength()),
                speed_limit_kmh=float(sumo_edge.getSpeed()) * 3.6,
                lane_count=int(sumo_edge.getLaneNumber()),
                shape=shape_lonlat,
                name=sumo_edge.getName() or "",
            )
        )

    if skipped_duplicates:
        logger.warning(
            "load_real_network: skipped %d parallel edge(s) sharing a "
            "(from, to) junction pair already represented in the graph.",
            skipped_duplicates,
        )

    if not nodes or not edges:
        raise NetworkLoadError(f"Parsed {net_path} but found no usable nodes/edges.")

    lngs = [n.lng for n in nodes]
    lats = [n.lat for n in nodes]
    bbox = (min(lngs), min(lats), max(lngs), max(lats))

    logger.info(
        "load_real_network: loaded real Anna Nagar network from %s — "
        "%d nodes, %d edges (bbox lng %.4f..%.4f, lat %.4f..%.4f).",
        net_path,
        len(nodes),
        len(edges),
        bbox[0], bbox[2], bbox[1], bbox[3],
    )
    return RealNetwork(nodes=nodes, edges=edges, bbox=bbox, net=net)


def get_named_locations(net_path: Path = DEFAULT_NET_PATH) -> List[Dict[str, float | str]]:
    """
    Real, searchable FROM/TO locations — one entry per unique real OSM street
    name found in the network, at the average midpoint of every edge sharing
    that name. Never invents a place name: if the real network has none
    (e.g. it failed to load), returns an empty list.
    """
    real = get_real_network(net_path)
    if real is None:
        return []

    by_name: Dict[str, List[Tuple[float, float]]] = {}
    for edge in real.edges:
        if not edge.name:
            continue
        mid = edge.shape[len(edge.shape) // 2] if edge.shape else None
        if mid is None:
            continue
        by_name.setdefault(edge.name, []).append(mid)

    locations: List[Dict[str, float | str]] = []
    for name, points in sorted(by_name.items()):
        avg_lng = sum(p[0] for p in points) / len(points)
        avg_lat = sum(p[1] for p in points) / len(points)
        locations.append({"name": name, "lat": avg_lat, "lng": avg_lng})
    return locations


def get_real_network(net_path: Path = DEFAULT_NET_PATH) -> Optional[RealNetwork]:
    """
    Cached accessor — loads once per process, returns ``None`` (never raises)
    on failure so callers can fall back without a try/except at every call
    site. Logs the failure loudly exactly once.
    """
    global _cached_network, _load_attempted
    if _cached_network is not None:
        return _cached_network
    if _load_attempted:
        return None

    _load_attempted = True
    try:
        _cached_network = load_real_network(net_path)
        return _cached_network
    except NetworkLoadError as exc:
        logger.error(
            "get_real_network: could not load the real network (%s) — "
            "falling back to the synthetic placeholder grid. This means the "
            "map and routing will NOT reflect real Anna Nagar geometry.",
            exc,
        )
        return None
