"""Load a complete activity effort response and its rank-observation provenance."""
from datetime import datetime, timezone
from src.etl.segment_mapper import SegmentMapper, SegmentMappingError
from src.models.segment_record_metadata import SegmentEffortRecordMetadata, SegmentRecordRefresh
from src.repositories.segment_repository import SegmentRepository


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def load_activity_segments(session, activity, payload, retrieved_at=None):
    """Stage one complete response atomically; the caller commits or rolls back.

    Missing/invalid effort arrays must never mean 'delete all stored efforts'.
    Empty arrays explicitly returned by include_all_efforts are valid replacements.
    """
    if payload.get('id') != activity.activity_id:
        raise SegmentMappingError('Activity response ID does not match the requested activity.')
    raw = payload.get('segment_efforts')
    if not isinstance(raw, list):
        raise SegmentMappingError('Complete segment_efforts array was not returned; existing efforts retained.')
    if any(not isinstance(item, dict) for item in raw):
        raise SegmentMappingError('Invalid segment effort entry.')
    from src.services.reporting_local_time import zone_name
    zone = zone_name(payload.get('timezone'))
    if zone:
        from sqlalchemy import text
        session.execute(text('INSERT INTO point_reporting_metadata VALUES (:id,:zone) ON CONFLICT(activity_id) DO UPDATE SET timezone_name=:zone'), {'id':activity.activity_id,'zone':zone})
    stamp = retrieved_at or utcnow()
    segments = [SegmentMapper.segment_from_effort(item) for item in raw]
    efforts = [SegmentMapper.effort_from_api(activity.activity_id, item) for item in raw]
    ids = [effort.segment_effort_id for effort in efforts]
    if any(e.segment_effort_id < 1 or e.segment_id < 1 for e in efforts):
        raise SegmentMappingError('Effort and segment IDs must be positive.')
    if len(ids) != len(set(ids)):
        raise SegmentMappingError('Duplicate effort IDs in activity response.')
    for item, effort in zip(raw, efforts):
        if isinstance(item.get('activity'), dict) and item['activity'].get('id') not in (None, activity.activity_id):
            raise SegmentMappingError('Effort belongs to a different activity.')
        for key in ['pr_rank', 'kom_rank']:
            rank = item.get(key)
            if rank is not None and (isinstance(rank, bool) or not isinstance(rank, int) or rank < 1):
                raise SegmentMappingError(f'Invalid {key}; expected a positive integer or null.')
        existing = session.get(type(effort), effort.segment_effort_id)
        if existing is not None and existing.activity_id != activity.activity_id:
            raise SegmentMappingError('Effort ID already belongs to another stored activity.')
    result = SegmentRepository(session).upsert_activity_segments(activity.activity_id, segments, efforts)
    session.flush()
    for item, effort in zip(raw, efforts):
        session.merge(SegmentEffortRecordMetadata(
            segment_effort_id=effort.segment_effort_id, retrieved_at=stamp,
            pr_rank_returned='pr_rank' in item, kom_rank_returned='kom_rank' in item))
    session.merge(SegmentRecordRefresh(activity_id=activity.activity_id,
        last_attempted_at=stamp, last_refreshed_at=stamp, status='completed'))
    activity.segments_loaded_at = stamp
    return result
