"""Refresh a bounded batch of GPS activity segment efforts from Strava."""
import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
from sqlalchemy import exists, or_, select
from src.api.client import StravaApiError, StravaRateLimitError
from src.etl.segment_mapper import SegmentMappingError
from src.models import Activity, SegmentEffort
from src.models.segment_record_metadata import SegmentRecordRefresh
from src.services.segment_record_service import load_activity_segments, utcnow


@dataclass
class RecordRefreshResult:
    selected: int = 0
    refreshed: int = 0
    failed: int = 0
    rate_limit_reached: bool = False
    deferred: int = 0


def select_candidates(session, limit, refresh_before=None, activity_ids=None):
    from sqlalchemy import text
    query = (select(Activity.activity_id).outerjoin(SegmentRecordRefresh,
        SegmentRecordRefresh.activity_id == Activity.activity_id)
        .where(exists().where(SegmentEffort.activity_id == Activity.activity_id))
        .where(text('EXISTS (SELECT 1 FROM activity_points p WHERE p.activity_id=activities.activity_id)')))
    if activity_ids is not None:
        query = query.where(Activity.activity_id.in_(activity_ids))
    else:
        pending = SegmentRecordRefresh.last_refreshed_at.is_(None)
        if refresh_before:
            pending = or_(pending, SegmentRecordRefresh.last_refreshed_at < refresh_before)
        query = query.where(pending)
    # Untouched activities first, then the oldest attempted ones. Failed requests
    # do not starve unattempted history on subsequent batches.
    return list(session.scalars(query.order_by(
        SegmentRecordRefresh.last_attempted_at.asc().nullsfirst(),
        Activity.start_date.desc(), Activity.activity_id.desc()).limit(limit)))


def run_batch(session_factory, client, limit=25, refresh_before=None, activity_ids=None):
    if limit < 1:
        raise ValueError('limit must be positive')
    with session_factory() as session:
        ids = select_candidates(session, limit, refresh_before, activity_ids)
    result = RecordRefreshResult(selected=len(ids))
    for index, activity_id in enumerate(ids):
        if not client.has_read_capacity():
            result.rate_limit_reached = True
            result.deferred = len(ids)-index
            break
        with session_factory() as session:
            try:
                payload = client.get_activity(activity_id, include_all_efforts=True)
                activity = session.get(Activity, activity_id)
                load_activity_segments(session, activity, payload)
                session.commit()
                result.refreshed += 1
                print(f'Activity {activity_id}: efforts and rank metadata refreshed', flush=True)
            except StravaRateLimitError:
                session.rollback()
                result.rate_limit_reached = True
                result.deferred = len(ids)-index
                break
            except (StravaApiError, SegmentMappingError, TypeError, ValueError):
                session.rollback()
                record = session.get(SegmentRecordRefresh, activity_id)
                if record is None:
                    record = SegmentRecordRefresh(activity_id=activity_id)
                    session.add(record)
                record.last_attempted_at = utcnow()
                record.status = 'failed'
                session.commit()
                result.failed += 1
                # Do not print raw responses: errors can contain personal data.
                print(f'Activity {activity_id}: refresh failed; previous data retained', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=25)
    parser.add_argument('--dry-run', action='store_true', help='Show the next local batch without authentication or API reads')
    parser.add_argument('--refresh-before', type=datetime.fromisoformat,
                        help='Also revisit snapshots older than this naive UTC ISO date/time')
    parser.add_argument('--activity-ids', nargs='+', type=int,
                        help='Force selected stored GPS activities with efforts; still bounded by --limit')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if args.refresh_before and args.refresh_before.tzinfo:
        parser.error('--refresh-before must be a naive UTC ISO date/time')
    from src.database import SessionLocal
    from src.tools.build_segment_records import run as install
    install()
    # No network authentication when the local database has no eligible work.
    with SessionLocal() as session:
        candidates = select_candidates(session, args.limit, args.refresh_before, args.activity_ids)
        if args.dry_run:
            print({'next_batch_count':len(candidates),'activity_ids':candidates})
            return
        if not candidates:
            print('No eligible pending GPS activities with stored segment efforts.')
            return
    from src.api.authenticate import StravaAuthenticator
    from src.api.client import StravaClient
    result = run_batch(SessionLocal, StravaClient(StravaAuthenticator().get_access_token()),
                       args.limit, args.refresh_before, args.activity_ids)
    print(asdict(result), flush=True)
    print('Rerun to resume. After loading, re-export Parquet and refresh the GPS model.')
    if result.failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
