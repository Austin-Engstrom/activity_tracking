"""OpenStreetMap boundary discovery through the public Nominatim API."""

from dataclasses import dataclass
from typing import Any

import requests


NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
ALLOWED_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}


@dataclass(slots=True)
class OsmBoundaryCandidate:
    """One OpenStreetMap search result."""

    display_name: str
    osm_type: str
    osm_id: int
    category: str | None
    feature_type: str | None
    latitude: float
    longitude: float
    geojson: dict[str, Any] | None

    @property
    def geometry_type(self) -> str | None:
        """Return the GeoJSON geometry type."""

        return self.geojson.get("type") if self.geojson else None

    @property
    def usable_boundary(self) -> bool:
        """Return whether the result contains polygon geometry."""

        return self.geometry_type in ALLOWED_GEOMETRY_TYPES


class OsmBoundaryService:
    """Search OpenStreetMap for trail-system boundary candidates."""

    def __init__(
        self,
        *,
        user_agent: str,
        contact_email: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        if not user_agent.strip():
            raise ValueError("A descriptive user agent is required.")

        self.user_agent = user_agent.strip()
        self.contact_email = contact_email.strip() if contact_email else None
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        country_codes: str | None = "us",
    ) -> list[OsmBoundaryCandidate]:
        """Search Nominatim and return normalized candidates."""

        if not query.strip():
            raise ValueError("Search text is required.")

        params: dict[str, str | int] = {
            "q": query.strip(),
            "format": "jsonv2",
            "polygon_geojson": 1,
            "addressdetails": 1,
            "limit": max(1, min(limit, 20)),
        }

        if country_codes:
            params["countrycodes"] = country_codes

        if self.contact_email:
            params["email"] = self.contact_email

        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params=params,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        candidates: list[OsmBoundaryCandidate] = []

        for item in response.json():
            candidates.append(
                OsmBoundaryCandidate(
                    display_name=item.get(
                        "display_name",
                        "Unnamed OSM result",
                    ),
                    osm_type=item.get("osm_type", "unknown"),
                    osm_id=int(item["osm_id"]),
                    category=item.get("category"),
                    feature_type=item.get("type"),
                    latitude=float(item["lat"]),
                    longitude=float(item["lon"]),
                    geojson=item.get("geojson"),
                )
            )

        return candidates
