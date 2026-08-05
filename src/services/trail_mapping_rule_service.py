"""Business logic for creating and validating mapping rules."""

from sqlalchemy.orm import Session

from src.repositories.trail_mapping_rule_repository import (
    TrailMappingRuleRepository,
)
from src.repositories.trail_system_repository import TrailSystemRepository
from src.services.trail_mapping_service import SUPPORTED_RULE_TYPES


class TrailMappingRuleService:
    """Coordinates trail mapping rule management."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.rule_repository = TrailMappingRuleRepository(session)
        self.trail_repository = TrailSystemRepository(session)

    def create_rule(
        self,
        trail_system_id: int,
        rule_type: str,
        *,
        match_value: str | None = None,
        min_latitude: float | None = None,
        max_latitude: float | None = None,
        min_longitude: float | None = None,
        max_longitude: float | None = None,
        priority: int = 100,
        confidence: float = 0.90,
        notes: str | None = None,
    ):
        """Validate and create a trail mapping rule."""

        normalized_type = rule_type.strip().upper()

        if normalized_type not in SUPPORTED_RULE_TYPES:
            supported = ", ".join(sorted(SUPPORTED_RULE_TYPES))
            raise ValueError(
                f"Unsupported rule type '{rule_type}'. "
                f"Supported values: {supported}."
            )

        if self.trail_repository.get_by_id(trail_system_id) is None:
            raise ValueError(
                f"Trail system {trail_system_id} does not exist."
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "Confidence must be between 0.0 and 1.0."
            )

        if priority < 0:
            raise ValueError("Priority cannot be negative.")

        if normalized_type == "BOUNDING_BOX":
            values = (
                min_latitude,
                max_latitude,
                min_longitude,
                max_longitude,
            )

            if any(value is None for value in values):
                raise ValueError(
                    "Bounding-box rules require all four coordinates."
                )

            if min_latitude > max_latitude:
                raise ValueError(
                    "Minimum latitude cannot exceed maximum latitude."
                )

            if min_longitude > max_longitude:
                raise ValueError(
                    "Minimum longitude cannot exceed maximum longitude."
                )

        elif not match_value or not match_value.strip():
            raise ValueError(
                f"{normalized_type} rules require a match value."
            )

        try:
            rule = self.rule_repository.create(
                trail_system_id=trail_system_id,
                rule_type=normalized_type,
                match_value=match_value,
                min_latitude=min_latitude,
                max_latitude=max_latitude,
                min_longitude=min_longitude,
                max_longitude=max_longitude,
                priority=priority,
                confidence=confidence,
                notes=notes,
            )

            self.session.commit()
            return rule

        except Exception:
            self.session.rollback()
            raise

    def get_all_rules(self):
        """Return all mapping rules."""

        return self.rule_repository.get_all()
