"""Repository for trail-system mapping rules."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.trail_mapping_rule import TrailMappingRule


class TrailMappingRuleRepository:
    """Handles persistence operations for mapping rules."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
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
        active: bool = True,
        notes: str | None = None,
    ) -> TrailMappingRule:
        """Create a mapping rule."""

        rule = TrailMappingRule(
            trail_system_id=trail_system_id,
            rule_type=rule_type.strip().upper(),
            match_value=match_value.strip() if match_value else None,
            min_latitude=min_latitude,
            max_latitude=max_latitude,
            min_longitude=min_longitude,
            max_longitude=max_longitude,
            priority=priority,
            confidence=confidence,
            active=active,
            notes=notes.strip() if notes else None,
        )

        self.session.add(rule)
        self.session.flush()

        return rule

    def get_by_id(self, rule_id: int) -> TrailMappingRule | None:
        """Return a mapping rule by primary key."""

        return self.session.get(TrailMappingRule, rule_id)

    def get_active_rules(self) -> list[TrailMappingRule]:
        """Return active rules in evaluation order."""

        statement = (
            select(TrailMappingRule)
            .options(selectinload(TrailMappingRule.trail_system))
            .where(TrailMappingRule.active.is_(True))
            .order_by(
                TrailMappingRule.priority,
                TrailMappingRule.rule_id,
            )
        )

        return list(self.session.scalars(statement))

    def get_all(self) -> list[TrailMappingRule]:
        """Return all rules in evaluation order."""

        statement = (
            select(TrailMappingRule)
            .options(selectinload(TrailMappingRule.trail_system))
            .order_by(
                TrailMappingRule.priority,
                TrailMappingRule.rule_id,
            )
        )

        return list(self.session.scalars(statement))

    def delete(self, rule: TrailMappingRule) -> None:
        """Delete a mapping rule."""

        self.session.delete(rule)
        self.session.flush()
