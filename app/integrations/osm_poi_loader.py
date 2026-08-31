"""
Real hospital locations for the Anna Nagar network.

SUMO's netconvert only imports road infrastructure (edges/junctions) and
building footprints (osm.poly.xml.gz has no name tags) — arbitrary POI
nodes like hospitals aren't carried into the SUMO network at all. They ARE
present in the raw pre-conversion OSM extract though
(2026-08-19-23-26-46/osm_bbox.osm.xml.gz), tagged amenity=hospital /
healthcare=hospital with real names and real WGS84 lat/lon — no projection
conversion needed, unlike the SUMO network data.

This is real data extracted from the project's own OSM source, not
invented: 15 real hospitals/clinics in Anna Nagar (Sri Devi Speciality
Hospital, K.H.M. Hospital, Firm Hospital, Sundaram Medical Foundation,
etc.) — matches what's visible on the actual OpenStreetMap view of the
area. Parsed once and cached, same pattern as sumo_network_loader.py.
"""
from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_OSM_RAW_PATH = (
    Path(__file__).resolve().parents[2] / "2026-08-19-23-26-46" / "osm_bbox.osm.xml.gz"
)


@dataclass
class RealHospital:
    osm_id: str
    name: str
    lat: float
    lng: float


_cached_hospitals: Optional[List[RealHospital]] = None
_load_attempted = False


def get_real_hospitals(osm_path: Path = DEFAULT_OSM_RAW_PATH) -> List[RealHospital]:
    """Cached accessor — parses once per process, returns [] (never raises)
    on failure so callers degrade gracefully instead of crashing."""
    global _cached_hospitals, _load_attempted
    if _cached_hospitals is not None:
        return _cached_hospitals
    if _load_attempted:
        return []
    _load_attempted = True

    if not osm_path.exists():
        logger.error(
            "get_real_hospitals: raw OSM source not found at %s — "
            "no real hospital data available.",
            osm_path,
        )
        return []

    try:
        with gzip.open(osm_path, "rt", encoding="utf-8") as f:
            root = ET.fromstring(f.read())
    except Exception as exc:  # noqa: BLE001
        logger.error("get_real_hospitals: failed to parse %s: %s", osm_path, exc)
        return []

    hospitals: List[RealHospital] = []
    for node in root.findall("node"):
        tags = {t.get("k"): t.get("v") for t in node.findall("tag")}
        if tags.get("amenity") != "hospital" and tags.get("healthcare") != "hospital":
            continue
        name = tags.get("name")
        lat = node.get("lat")
        lon = node.get("lon")
        if not name or lat is None or lon is None:
            continue  # skip unnamed/uncoordinated entries rather than guess
        hospitals.append(RealHospital(osm_id=node.get("id", ""), name=name, lat=float(lat), lng=float(lon)))

    logger.info("get_real_hospitals: loaded %d real hospitals from %s", len(hospitals), osm_path)
    _cached_hospitals = hospitals
    return hospitals
