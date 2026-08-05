"""Rule-based automatic mapping of Strava segments to trail systems."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.segment import Segment
from src.models.segment_trail_system import SegmentTrailSystem
from src.models.trail_mapping_rule import TrailMappingRule
from src.repositories.segment_trail_system_repository import (
    SegmentTrailSystemRepository,
)
from src.repositories.trail_mapping_rule_repository import (
    TrailMappingRuleRepository,
)


SUPPORTED_RULE_TYPES = {
    "CITY",
    "STATE",
    "NAME_EQUALS",
    "NAME_CONTAINS",
    "BOUNDING_BOX",
}


@dataclass(slots=True)
class TrailMappingSummary:
    """Summary returned after an automatic mapping run."""

    total_segments: int
    already_mapped: int
    evaluated: int
    mapped: int
    unmatched: int

    @property
    def coverage_percent(self) -> float:
        """Return total mapped coverage after the run."""

        if self.total_segments == 0:
            return 100.0

        return (
            (self.already_mapped + self.mapped)
            / self.total_segments
            * 100.0
        )


class TrailMappingService:
    """Applies active mapping rules to unmapped segments."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.rule_repository = TrailMappingRuleRepository(session)
        self.mapping_repository = SegmentTrailSystemRepository(session)

    def run(self) -> TrailMappingSummary:
        """Apply the first matching active rule to each unmapped segment."""

        rules = self.rule_repository.get_active_rules()
        total_segments = self._count_segments()
        mapped_segment_ids = self._get_mapped_segment_ids()
        segments = self._get_unmapped_segments(mapped_segment_ids)

        inserted = 0

        try:
            for segment in segments:
                rule = self._find_first_match(segment, rules)

                if rule is None:
                    continue

                self.mapping_repository.create(
                    segment_id=segment.segment_id,
                    trail_system_id=rule.trail_system_id,
                    confidence=rule.confidence,
                    mapping_source=f"rule:{rule.rule_type.lower()}",
                    notes=f"Automatically mapped by rule {rule.rule_id}.",
                )

                inserted += 1

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return TrailMappingSummary(
            total_segments=total_segments,
            already_mapped=len(mapped_segment_ids),
            evaluated=len(segments),
            mapped=inserted,
            unmatched=len(segments) - inserted,
        )

    def _find_first_match(
        self,
        segment: Segment,
        rules: list[TrailMappingRule],
    ) -> TrailMappingRule | None:
        """Return the highest-priority rule matching a segment."""

        for rule in rules:
            if self._matches(segment, rule):
                return rule

        return None

    def _matches(
        self,
        segment: Segment,
        rule: TrailMappingRule,
    ) -> bool:
        """Return whether one segment matches one rule."""

        rule_type = rule.rule_type.upper()

        if rule_type not in SUPPORTED_RULE_TYPES:
            return False

        if rule_type == "CITY":
            return self._normalized(segment.city) == self._normalized(
                rule.match_value
            )

        if rule_type == "STATE":
            return self._normalized(segment.state) == self._normalized(
                rule.match_value
            )

        if rule_type == "NAME_EQUALS":
            return self._normalized(segment.name) == self._normalized(
                rule.match_value
            )

        if rule_type == "NAME_CONTAINS":
            match_value = self._normalized(rule.match_value)
            segment_name = self._normalized(segment.name)

            return bool(match_value and match_value in segment_name)

        if rule_type == "BOUNDING_BOX":
            return self._inside_bounding_box(segment, rule)

        return False

    @staticmethod
    def _inside_bounding_box(
        segment: Segment,
        rule: TrailMappingRule,
    ) -> bool:
        """Return whether both segment endpoints fall inside a rule boundary."""

        bounds = (
            rule.min_latitude,
            rule.max_latitude,
            rule.min_longitude,
            rule.max_longitude,
        )

        if any(value is None for value in bounds):
            return False

        points = (
            (segment.start_latitude, segment.start_longitude),
            (segment.end_latitude, segment.end_longitude),
        )

        if any(
            latitude is None or longitude is None
            for latitude, longitude in points
        ):
            return False

        return all(
            rule.min_latitude <= latitude <= rule.max_latitude
            and rule.min_longitude <= longitude <= rule.max_longitude
            for latitude, longitude in points
        )

    def _get_unmapped_segments(
        self,
        mapped_segment_ids: set[int],
    ) -> list[Segment]:
        """Return segments that do not yet have a mapping."""

        statement = select(Segment).order_by(
            Segment.city,
            Segment.name,
        )

        if mapped_segment_ids:
            statement = statement.where(
                Segment.segment_id.not_in(mapped_segment_ids)
            )

        return list(self.session.scalars(statement))

    def _get_mapped_segment_ids(self) -> set[int]:
        """Return all currently mapped segment IDs."""

        statement = select(
            SegmentTrailSystem.segment_id
        ).distinct()

        return set(self.session.scalars(statement))

    def _count_segments(self) -> int:
        """Return the total number of stored segments."""

        return len(list(self.session.scalars(select(Segment.segment_id))))

    @staticmethod
    def _normalized(value: str | None) -> str:
        """Normalize text for deterministic matching."""

        return value.strip().casefold() if value else ""
