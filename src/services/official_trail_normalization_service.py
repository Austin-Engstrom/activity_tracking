"""Normalize imported OSM ways into logical official trails."""

import json
import re
from collections import Counter
from dataclasses import dataclass

from shapely.geometry import LineString, mapping
from shapely.ops import linemerge, unary_union
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.official_trail import OfficialTrail
from src.models.osm_trails import OsmTrail
from src.repositories.official_trail_repository import (
    OfficialTrailRepository,
)


@dataclass(slots=True)
class OfficialTrailNormalizationSummary:
    """Summary of one normalization run."""

    trail_system_id: int
    imported_sections: int
    named_sections: int
    unnamed_sections: int
    official_trails: int
    created: int
    updated: int
    orphaned_unnamed_sections: int
    deleted_empty: int


class OfficialTrailNormalizationService:
    """Group named OSM ways into normalized logical trails."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = OfficialTrailRepository(session)

    def normalize_trail_system(
        self,
        trail_system_id: int,
    ) -> OfficialTrailNormalizationSummary:
        """Group imported OSM ways by normalized name."""

        sections = self._get_sections(trail_system_id)

        named_sections = [
            section
            for section in sections
            if section.name and section.name.strip()
        ]

        unnamed_sections = [
            section
            for section in sections
            if not section.name or not section.name.strip()
        ]

        grouped: dict[str, list[OsmTrail]] = {}

        for section in named_sections:
            normalized_name = self.normalize_name(section.name)
            grouped.setdefault(
                normalized_name,
                [],
            ).append(section)

        created = 0
        updated = 0

        try:
            for normalized_name, trail_sections in grouped.items():
                display_name = self._preferred_display_name(
                    trail_sections
                )

                official_trail = self.repository.get_by_name(
                    trail_system_id,
                    normalized_name,
                )

                if official_trail is None:
                    official_trail = OfficialTrail(
                        trail_system_id=trail_system_id,
                        name=display_name,
                        normalized_name=normalized_name,
                    )
                    self.repository.add(official_trail)
                    created += 1
                else:
                    official_trail.name = display_name
                    updated += 1

                self._apply_aggregate_values(
                    official_trail,
                    trail_sections,
                )

                for section in trail_sections:
                    section.official_trail_id = (
                        official_trail.official_trail_id
                    )

            orphaned = self._assign_unnamed_sections(
                unnamed_sections,
                named_sections,
            )

            self._refresh_all_aggregates(trail_system_id)

            deleted_empty = (
                self.repository.delete_empty_for_trail_system(
                    trail_system_id
                )
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        official_trails = self.repository.get_by_trail_system(
            trail_system_id
        )

        return OfficialTrailNormalizationSummary(
            trail_system_id=trail_system_id,
            imported_sections=len(sections),
            named_sections=len(named_sections),
            unnamed_sections=len(unnamed_sections),
            official_trails=len(official_trails),
            created=created,
            updated=updated,
            orphaned_unnamed_sections=orphaned,
            deleted_empty=deleted_empty,
        )

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize names for stable grouping."""

        value = name.casefold().strip()
        value = value.replace("’", "'")
        value = re.sub(r"\s+", " ", value)
        value = re.sub(r"[^\w\s'&-]", "", value)

        return value

    def _get_sections(
        self,
        trail_system_id: int,
    ) -> list[OsmTrail]:
        """Return imported OSM ways for one trail system."""

        statement = (
            select(OsmTrail)
            .where(
                OsmTrail.trail_system_id == trail_system_id
            )
            .order_by(OsmTrail.osm_trail_id)
        )

        return list(self.session.scalars(statement))

    @staticmethod
    def _preferred_display_name(
        sections: list[OsmTrail],
    ) -> str:
        """Choose the most common original name."""

        names = [
            section.name.strip()
            for section in sections
            if section.name and section.name.strip()
        ]

        return Counter(names).most_common(1)[0][0]

    @staticmethod
    def _mode(
        values: list[str | None],
    ) -> str | None:
        """Return the most common nonblank value."""

        clean_values = [
            value
            for value in values
            if value
        ]

        if not clean_values:
            return None

        return Counter(clean_values).most_common(1)[0][0]

    def _apply_aggregate_values(
        self,
        official_trail: OfficialTrail,
        sections: list[OsmTrail],
    ) -> None:
        """Update official-trail aggregates."""

        official_trail.total_length_meters = sum(
            section.length_meters or 0.0
            for section in sections
        )

        official_trail.section_count = len(sections)

        official_trail.primary_surface = self._mode(
            [
                section.surface
                for section in sections
            ]
        )

        official_trail.bicycle_access = self._mode(
            [
                section.bicycle_access
                for section in sections
            ]
        )

        official_trail.mtb_scale = self._mode(
            [
                section.mtb_scale
                for section in sections
            ]
        )

        official_trail.mtb_type = self._mode(
            [
                section.mtb_type
                for section in sections
            ]
        )

        official_trail.combined_geometry_geojson = (
            self._combine_geometry(sections)
        )

    @staticmethod
    def _combine_geometry(
        sections: list[OsmTrail],
    ) -> str | None:
        """Combine section geometry into one LineString or MultiLineString."""

        lines = []

        for section in sections:
            geometry = json.loads(
                section.geometry_geojson
            )

            coordinates = geometry.get("coordinates")

            if (
                geometry.get("type") == "LineString"
                and coordinates
            ):
                lines.append(
                    LineString(coordinates)
                )

        if not lines:
            return None

        merged = linemerge(
            unary_union(lines)
        )

        return json.dumps(
            mapping(merged),
            separators=(",", ":"),
        )

    def _assign_unnamed_sections(
        self,
        unnamed_sections: list[OsmTrail],
        named_sections: list[OsmTrail],
        *,
        max_endpoint_distance_meters: float = 15.0,
    ) -> int:
        """Attach unnamed sections when they touch a named section.

        This first version intentionally avoids broad nearest-neighbor
        assignment. Unnamed sections remain orphaned unless their endpoint
        coordinates exactly or nearly connect to a named section after
        projection is added in a later enhancement.
        """

        # Conservative first implementation:
        # do not auto-assign unnamed ways based only on proximity.
        for section in unnamed_sections:
            section.official_trail_id = None

        return len(unnamed_sections)

    def _refresh_all_aggregates(
        self,
        trail_system_id: int,
    ) -> None:
        """Refresh aggregates after section assignments."""

        trails = self.repository.get_by_trail_system(
            trail_system_id
        )

        for trail in trails:
            self._apply_aggregate_values(
                trail,
                list(trail.osm_sections),
            )
