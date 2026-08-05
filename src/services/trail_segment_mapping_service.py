"""Spatially match Strava segments to imported OSM trail lines."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.osm_trails import OsmTrail
from src.models.segment import Segment
from src.models.trail_segment_mapping import TrailSegmentMapping
from src.repositories.trail_segment_mapping_repository import (
    TrailSegmentMappingRepository,
)
from src.utils.spatial import (
    approximate_overlap_percent,
    confidence_from_match,
    geojson_to_projected_line,
    line_distance_meters,
    segment_line_from_coordinates,
)


@dataclass(slots=True)
class TrailSegmentMappingSummary:
    """Summary of one trail-system mapping run."""

    trail_system_id: int
    osm_trails: int
    candidate_segments: int
    evaluated_pairs: int
    inserted: int
    updated: int
    unmatched_segments: int


class TrailSegmentMappingService:
    """Match Strava segments to the best nearby OSM trail."""

    def __init__(
        self,
        session: Session,
        *,
        max_distance_meters: float = 30.0,
        overlap_tolerance_meters: float = 20.0,
        minimum_overlap_percent: float = 40.0,
        minimum_confidence: float = 0.45,
    ) -> None:
        self.session = session
        self.max_distance_meters = max_distance_meters
        self.overlap_tolerance_meters = overlap_tolerance_meters
        self.minimum_overlap_percent = minimum_overlap_percent
        self.minimum_confidence = minimum_confidence
        self.mapping_repository = TrailSegmentMappingRepository(session)

    def map_trail_system(
        self,
        trail_system_id: int,
        *,
        replace_unvalidated: bool = True,
    ) -> TrailSegmentMappingSummary:
        """Map eligible Strava segments to their best OSM trail candidate."""

        trails = self._get_osm_trails(trail_system_id)
        segments = self._get_segments_for_trail_system(
            trail_system_id
        )

        if not trails:
            raise ValueError(
                f"Trail system {trail_system_id} has no imported OSM trails."
            )

        if replace_unvalidated:
            self.mapping_repository.delete_unvalidated_for_trail_system(
                trail_system_id
            )

        projected_trails = {
            trail.osm_trail_id: geojson_to_projected_line(
                trail.geometry_geojson
            )
            for trail in trails
        }

        evaluated_pairs = 0
        inserted = 0
        updated = 0
        matched_segment_ids: set[int] = set()

        try:
            for segment in segments:
                segment_line = segment_line_from_coordinates(
                    segment.start_latitude,
                    segment.start_longitude,
                    segment.end_latitude,
                    segment.end_longitude,
                )

                if segment_line is None:
                    continue

                best_match = None

                for trail in trails:
                    trail_line = projected_trails[
                        trail.osm_trail_id
                    ]

                    distance = line_distance_meters(
                        segment_line,
                        trail_line,
                    )
                    evaluated_pairs += 1

                    if distance > self.max_distance_meters:
                        continue

                    overlap = approximate_overlap_percent(
                        segment_line,
                        trail_line,
                        tolerance_meters=(
                            self.overlap_tolerance_meters
                        ),
                    )

                    if overlap < self.minimum_overlap_percent:
                        continue

                    confidence = confidence_from_match(
                        distance_meters=distance,
                        overlap_percent=overlap,
                        max_distance_meters=(
                            self.max_distance_meters
                        ),
                    )

                    if confidence < self.minimum_confidence:
                        continue

                    candidate = {
                        "trail": trail,
                        "distance": distance,
                        "overlap": overlap,
                        "confidence": confidence,
                    }

                    if (
                        best_match is None
                        or candidate["confidence"]
                        > best_match["confidence"]
                    ):
                        best_match = candidate

                if best_match is None:
                    continue

                trail = best_match["trail"]

                existing = self.mapping_repository.get_mapping(
                    trail.osm_trail_id,
                    segment.segment_id,
                )

                if existing is None:
                    self.mapping_repository.add(
                        TrailSegmentMapping(
                            osm_trail_id=trail.osm_trail_id,
                            segment_id=segment.segment_id,
                            distance_meters=best_match["distance"],
                            overlap_percent=best_match["overlap"],
                            confidence=best_match["confidence"],
                            mapping_source="endpoint_geometry",
                            validated=False,
                        )
                    )
                    inserted += 1
                else:
                    existing.distance_meters = best_match["distance"]
                    existing.overlap_percent = best_match["overlap"]
                    existing.confidence = best_match["confidence"]
                    existing.mapping_source = "endpoint_geometry"
                    updated += 1

                matched_segment_ids.add(segment.segment_id)

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return TrailSegmentMappingSummary(
            trail_system_id=trail_system_id,
            osm_trails=len(trails),
            candidate_segments=len(segments),
            evaluated_pairs=evaluated_pairs,
            inserted=inserted,
            updated=updated,
            unmatched_segments=(
                len(segments) - len(matched_segment_ids)
            ),
        )

    def _get_osm_trails(
        self,
        trail_system_id: int,
    ) -> list[OsmTrail]:
        """Return imported OSM trails for one trail system."""

        statement = (
            select(OsmTrail)
            .where(
                OsmTrail.trail_system_id == trail_system_id
            )
            .order_by(OsmTrail.osm_trail_id)
        )

        return list(self.session.scalars(statement))

    def _get_segments_for_trail_system(
        self,
        trail_system_id: int,
    ) -> list[Segment]:
        """Return Strava segments already assigned to the trail system."""

        statement = (
            select(Segment)
            .join(Segment.trail_system_mappings)
            .where(
                Segment.trail_system_mappings.any(
                    trail_system_id=trail_system_id
                )
            )
            .order_by(Segment.segment_id)
        )

        return list(self.session.scalars(statement))
