"""Audit GPS reporting and optionally verify historical stream alignment."""
import argparse
import csv
import json
import math
from pathlib import Path
from sqlalchemy import text
from src.database.connection import engine

ROOT = Path(__file__).resolve().parents[2]


def verify_alignment(stored, payload):
    """Require original-size arrays and exact historical sample correspondence.

    Never infer original indexing from effort endpoint bounds alone.
    """
    streams = [payload.get(key) or {} for key in ('time', 'latlng')]
    for stream in streams:
        data = stream.get('data')
        if not isinstance(data, list) or not data:
            return False, 'missing_stream'
        if stream.get('original_size') != len(data):
            return False, 'resampled_stream'
        if stream.get('series_type') not in ('time', 'distance'):
            return False, 'unknown_series'
    times, gps = [s['data'] for s in streams]
    if streams[0]['series_type'] != streams[1]['series_type']:
        return False, 'different_series'
    if len(times) != len(gps) or len(stored) != len(times):
        return False, 'sample_count_changed'
    for index, (row, seconds, coords) in enumerate(zip(stored, times, gps)):
        if row['point_index'] != index or row['time_seconds'] != seconds:
            return False, 'time_index_changed'
        if not isinstance(coords, (list, tuple)) or len(coords) != 2:
            return False, 'invalid_coordinate'
        for actual, expected in zip((row['latitude'], row['longitude']), coords):
            if actual is None or expected is None:
                if actual != expected:
                    return False, 'coordinates_changed'
            elif not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-7):
                return False, 'coordinates_changed'
    return True, 'original_arrays_match'


def backfill(limit):
    from src.api.authenticate import StravaAuthenticator
    from src.api.client import StravaClient, StravaApiError, StravaRateLimitError
    client = StravaClient(StravaAuthenticator().get_access_token())
    with engine.begin() as conn:
        conn.exec_driver_sql("""CREATE TABLE IF NOT EXISTS stream_alignment_checks (
            activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),
            checked_at TEXT NOT NULL, reason TEXT NOT NULL)""")
        ids = conn.execute(text('''SELECT DISTINCT p.activity_id FROM activity_points p
            JOIN segment_efforts e ON e.activity_id=p.activity_id
            LEFT JOIN stream_index_alignment m ON m.activity_id=p.activity_id
            LEFT JOIN stream_alignment_checks checks ON checks.activity_id=p.activity_id
            WHERE coalesce(m.verified,0)=0 ORDER BY checks.checked_at IS NOT NULL, checks.checked_at, p.activity_id DESC LIMIT :limit'''), {'limit':limit}).scalars().all()
    for activity_id in ids:
        if not client.has_read_capacity():
            print('Stopped: Strava read capacity reserved. Rerun later to resume.')
            break
        try:
            payload = client.get_activity_streams(activity_id, ['time','latlng'])
        except StravaRateLimitError:
            print('Stopped: Strava rate limit reached. Rerun later to resume.')
            break
        except StravaApiError:
            print(f'{activity_id}: API request failed; no alignment change')
            continue
        with engine.begin() as conn:
            stored = conn.execute(text('SELECT point_index,time_seconds,latitude,longitude FROM activity_streams WHERE activity_id=:id ORDER BY point_index'), {'id':activity_id}).mappings().all()
            verified, reason = verify_alignment(stored, payload)
            # Invalidate stale verification if effort bounds do not fit these arrays.
            bad = conn.execute(text('''SELECT count(*) FROM segment_efforts WHERE activity_id=:id
                AND (start_index IS NULL OR end_index IS NULL OR start_index<0
                OR end_index<start_index OR end_index>=:size)'''), {'id':activity_id,'size':len(stored)}).scalar()
            if bad:
                verified, reason = False, 'invalid_effort_indexes'
            conn.execute(text('INSERT INTO stream_index_alignment VALUES (:id,:verified) ON CONFLICT(activity_id) DO UPDATE SET verified=excluded.verified'), {'id':activity_id,'verified':int(verified)})
            conn.execute(text("INSERT INTO stream_alignment_checks VALUES (:id,strftime('%Y-%m-%dT%H:%M:%fZ','now'),:reason) ON CONFLICT(activity_id) DO UPDATE SET checked_at=excluded.checked_at,reason=excluded.reason"), {'id':activity_id,'reason':reason})
        print(f'{activity_id}: {reason}; verified={verified}')


def audit(output):
    output.mkdir(parents=True, exist_ok=True)
    with engine.connect() as conn:
        summary = {}
        for table in ['activities','activity_streams','activity_points','view_activity','view_activity_point_segments']:
            summary[table] = conn.execute(text(f'SELECT count(*) FROM {table}')).scalar()
        summary['quality'] = dict(conn.execute(text('SELECT quality_status,count(*) FROM activity_points GROUP BY quality_status')).all())
        summary['matches'] = dict(conn.execute(text('SELECT match_method,count(*) FROM activity_points GROUP BY match_method')).all())
        summary['utc_fallback_points'] = conn.execute(text("SELECT count(*) FROM view_activity_points WHERE date_basis='utc_fallback'")).scalar()
        summary['duplicate_point_keys'] = conn.execute(text('SELECT count(*) FROM (SELECT activity_point_key FROM view_activity_points GROUP BY activity_point_key HAVING count(*)>1)')).scalar()
        missing = {}
        for key, view in [('activity_key','view_activity'),('gear_key','view_gear'),('activity_type_key','view_activity_type'),('date_key','view_date'),('trail_key','view_trail'),('trail_system_key','view_trail_system')]:
            missing[key] = conn.execute(text(f'SELECT count(*) FROM view_activity_points p WHERE p.{key} IS NOT NULL AND NOT EXISTS (SELECT 1 FROM {view} d WHERE d.{key}=p.{key})')).scalar()
        summary['orphan_dimension_keys'] = missing
        queries = {
            'activity_mileage': '''SELECT a.activity_id,a.name,a.distance_meters/1609.344 AS source_miles,
                sum(p.incremental_distance_meters)/1609.344 AS point_miles,
                (sum(p.incremental_distance_meters)-a.distance_meters)/1609.344 AS difference_miles,
                count(*) AS gps_points,sum(p.quality_status NOT IN ('valid','first_point')) AS uncertain_intervals
                FROM activities a JOIN activity_points p USING(activity_id) GROUP BY a.activity_id
                ORDER BY abs(coalesce(sum(p.incremental_distance_meters),0)-a.distance_meters) DESC''',
            'trail_system_mileage': '''SELECT t.trail_system_name,p.trail_system_key,count(*) AS points,
                sum(p.incremental_distance_miles) AS miles FROM view_activity_points p
                LEFT JOIN view_trail_system t USING(trail_system_key) GROUP BY p.trail_system_key ORDER BY miles DESC''',
            'trail_mileage': '''SELECT t.trail_name,p.trail_key,count(*) AS points,
                sum(p.incremental_distance_miles) AS miles FROM view_activity_points p
                LEFT JOIN view_trail t USING(trail_key) GROUP BY p.trail_key ORDER BY miles DESC'''
        }
        for name, sql in queries.items():
            result = conn.execute(text(sql))
            with (output / (name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
                writer=csv.writer(f);writer.writerow(result.keys());writer.writerows(result)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print(f'Audit files: {output.resolve()}')
    if summary['duplicate_point_keys'] or any(missing.values()):
        raise SystemExit('Validation failed: duplicate point keys or orphan dimension keys')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-streams',action='store_true',help='Read original arrays from Strava and update alignment metadata only')
    parser.add_argument('--limit',type=int,default=5,help='Maximum activities to verify per run; repeat to resume')
    parser.add_argument('--output',type=Path,default=ROOT/'exports'/'validation')
    args=parser.parse_args()
    if args.limit<1: parser.error('--limit must be positive')
    if args.verify_streams: backfill(args.limit)
    audit(args.output)
