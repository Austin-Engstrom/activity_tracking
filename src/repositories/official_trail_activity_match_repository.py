"""Repository for GPS-derived official-trail activity matches."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.models.official_trail_activity_match import (
    OfficialTrailActivityMatch,
)


class OfficialTrailActivityMatchRepository:
    """Handles activity-to-official-trail match persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(
        self,
        official_trail_id: int,
        activity_id: int,
    ) -> OfficialTrailActivityMatch | None:
        """Return one activity-to-trail match."""

        statement = select(
            OfficialTrailActivityMatch
        ).where(
            OfficialTrailActivityMatch.official_trail_id
            == official_trail_id,
            OfficialTrailActivityMatch.activity_id
            == activity_id,
        )

        return self.session.scalar(statement)

    def add(
        self,
        match: OfficialTrailActivityMatch,
    ) -> OfficialTrailActivityMatch:
        """Add and flush a match."""

        self.session.add(match)
        self.session.flush()

        return match

    def delete_for_activity_and_trail_system(
        self,
        activity_id: int,
        official_trail_ids: list[int],
    ) -> int:
        """Delete prior matches before recalculation."""

        if not official_trail_ids:
            return 0

        statement = (
            delete(OfficialTrailActivityMatch)
            .where(
                OfficialTrailActivityMatch.activity_id
                == activity_id,
                OfficialTrailActivityMatch.official_trail_id.in_(
                    official_trail_ids
                ),
            )
        )

        result = self.session.execute(statement)

        return int(result.rowcount or 0)