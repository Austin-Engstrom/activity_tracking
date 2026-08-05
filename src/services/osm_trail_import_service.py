"""Import OSM trail ways for confirmed trail-system polygons."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pyproj import Geod
from shapely.geometry import LineString, shape
from sqlalchemy.orm import Session

from src.api.overpass_client import OverpassClient
from src.models.osm_trails import OsmTrail
from src.models.trail_systems import TrailSystem
from src.repositories.osm_trail_repository import OsmTrailRepository
from src.repositories.trail_system_repository import TrailSystemRepository


GEOD = Geod(ellps="WGS84")


@dataclass(slots=True)
class OsmTrailImportSummary:
    """Summary of one OSM trail import."""

    trail_system_name: str
    endpoint: str
    returned_elements: int
    accepted_ways: int
    inserted: int
    updated: int
    deleted: int
    unnamed: int
    cache_path: str


class OsmTrailImportService:
    """Retrieve, normalize, cache, and upsert OSM ways."""

    def __init__(
        self,
        session: Session,
        client: OverpassClient,
        *,
        cache_directory: Path,
    ) -> None:
        self.session = session
        self.client = client
        self.cache_directory = cache_directory
        self.trail_repository = OsmTrailRepository(session)
        self.trail_system_repository = TrailSystemRepository(session)

    def import_trail_system(
        self,
        trail_system_id: int,
        *,
        delete_missing: bool = False,
    ) -> OsmTrailImportSummary:
        """Import trail-like ways intersecting a confirmed polygon."""

        trail_system = self.trail_system_repository.get_by_id(
            trail_system_id
        )

        if trail_system is None:
            raise ValueError(
                f"Trail system {trail_system_id} does not exist."
            )

        if (
            not trail_system.boundary_confirmed
            or not trail_system.boundary_geojson
        ):
            raise ValueError(
                f"{trail_system.name} has no confirmed boundary."
            )

        boundary = shape(
            json.loads(trail_system.boundary_geojson)
        )

        min_lon, min_lat, max_lon, max_lat = boundary.bounds

        query = self._build_query(
            min_lat,
            min_lon,
            max_lat,
            max_lon,
        )

        response = self.client.execute(query)
        payload = response.payload
        cache_path = self._write_cache(
            trail_system,
            payload,
        )

        accepted: list[dict[str, Any]] = []

        for element in payload.get("elements", []):
            normalized = self._normalize_way(
                element,
                boundary,
            )

            if normalized is not None:
                accepted.append(normalized)

        inserted = 0
        updated = 0
        unnamed = 0
        retained_keys: set[tuple[str, int]] = set()

        try:
            for values in accepted:
                key = (
                    values["osm_element_type"],
                    values["osm_element_id"],
                )
                retained_keys.add(key)

                existing = self.trail_repository.get_by_osm_element(
                    trail_system_id,
                    *key,
                )

                if values["name"] is None:
                    unnamed += 1

                if existing is None:
                    self.trail_repository.add(
                        OsmTrail(
                            trail_system_id=trail_system_id,
                            **values,
                        )
                    )
                    inserted += 1
                else:
                    for field_name, value in values.items():
                        setattr(existing, field_name, value)
                    updated += 1

            deleted = 0

            if delete_missing:
                deleted = self.trail_repository.delete_missing(
                    trail_system_id,
                    retained_keys,
                )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return OsmTrailImportSummary(
            trail_system_name=trail_system.name,
            endpoint=response.endpoint,
            returned_elements=len(
                payload.get("elements", [])
            ),
            accepted_ways=len(accepted),
            inserted=inserted,
            updated=updated,
            deleted=deleted,
            unnamed=unnamed,
            cache_path=str(cache_path),
        )

    @staticmethod
    def _build_query(
        south: float,
        west: float,
        north: float,
        east: float,
    ) -> str:
        """Build a bounded Overpass trail query."""

        return f"""
[out:json][timeout:120];
(
  way({south},{west},{north},{east})
    ["highway"~"^(path|track|cycleway|bridleway)$"];
);
out meta geom;
""".strip()

    @staticmethod
    def _normalize_way(
        element: dict[str, Any],
        boundary,
    ) -> dict[str, Any] | None:
        """Convert an intersecting way to database values."""

        if element.get("type") != "way":
            return None

        coordinates = [
            (float(node["lon"]), float(node["lat"]))
            for node in element.get("geometry", [])
            if "lon" in node and "lat" in node
        ]

        if len(coordinates) < 2:
            return None

        line = LineString(coordinates)

        if not line.intersects(boundary):
            return None

        tags = element.get("tags") or {}
        timestamp = element.get("timestamp")

        longitudes = [point[0] for point in coordinates]
        latitudes = [point[1] for point in coordinates]

        return {
            "osm_element_type": "way",
            "osm_element_id": int(element["id"]),
            "name": tags.get("name"),
            "highway_type": tags.get("highway"),
            "surface": tags.get("surface"),
            "bicycle_access": tags.get("bicycle"),
            "access": tags.get("access"),
            "mtb_scale": tags.get("mtb:scale"),
            "mtb_scale_uphill": tags.get("mtb:scale:uphill"),
            "mtb_type": tags.get("mtb:type"),
            "oneway": tags.get("oneway"),
            "length_meters": float(
                GEOD.line_length(
                    longitudes,
                    latitudes,
                )
            ),
            "vertex_count": len(coordinates),
            "is_loop": coordinates[0] == coordinates[-1],
            "geometry_geojson": json.dumps(
                {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
                separators=(",", ":"),
            ),
            "tags_json": json.dumps(
                tags,
                sort_keys=True,
                separators=(",", ":"),
            ),
            "source_updated_at": (
                datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
                if timestamp
                else None
            ),
        }

    def _write_cache(
        self,
        trail_system: TrailSystem,
        payload: dict[str, Any],
    ) -> Path:
        """Persist the raw API response."""

        safe_name = "".join(
            char.lower() if char.isalnum() else "_"
            for char in trail_system.name
        ).strip("_")

        timestamp = datetime.now(UTC).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = self.cache_directory / (
            f"{safe_name}_{timestamp}.json"
        )

        path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

        return path
