"""Aggregate GPS activity matches into trail-level progress."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.official_trail import OfficialTrail
from src.models.official_trail_activity_match import OfficialTrailActivityMatch
from src.models.official_trail_progress import OfficialTrailProgress


class OfficialTrailProgressService:
    """Rebuild progress for all official trails in one system."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def rebuild_trail_system(self, trail_system_id: int) -> int:
        trails = list(
            self.session.scalars(
                select(OfficialTrail)
                .where(OfficialTrail.trail_system_id == trail_system_id)
                .order_by(OfficialTrail.official_trail_id)
            )
        )

        try:
            for trail in trails:
                matches = list(
                    self.session.scalars(
                        select(OfficialTrailActivityMatch)
                        .options(
                            selectinload(
                                OfficialTrailActivityMatch.activity
                            )
                        )
                        .where(
                            OfficialTrailActivityMatch.official_trail_id
                            == trail.official_trail_id
                        )
                    )
                )

                progress = self.session.get(
                    OfficialTrailProgress,
                    trail.official_trail_id,
                )

                if progress is None:
                    progress = OfficialTrailProgress(
                        official_trail_id=trail.official_trail_id
                    )
                    self.session.add(progress)

                dates = [
                    match.activity.start_date
                    for match in matches
                    if match.activity.start_date is not None
                ]
                coverage = max(
                    (
                        match.trail_coverage_percent
                        for match in matches
                    ),
                    default=0.0,
                )

                progress.activity_count = len(
                    {match.activity_id for match in matches}
                )
                progress.first_ridden_at = min(dates) if dates else None
                progress.last_ridden_at = max(dates) if dates else None
                progress.total_ridden_distance_meters = sum(
                    match.ridden_distance_meters
                    for match in matches
                )
                progress.estimated_coverage_percent = coverage

                if not matches:
                    progress.progress_status = "unridden"
                elif coverage >= 90.0:
                    progress.progress_status = "completed"
                else:
                    progress.progress_status = "partial"

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return len(trails)
