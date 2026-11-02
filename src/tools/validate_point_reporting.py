"""Audit GPS reporting and optionally verify historical stream alignment."""
import argparse
import csv
import json
import math
import time
from datetime import datetime, timezone
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


def select_verification_activities(conn, limit, candidate_file=None):
    rows = conn.execute(text("""SELECT a.activity_id, checks.checked_at FROM activities a
        LEFT JOIN stream_index_alignment m ON m.activity_id=a.activity_id
        LEFT JOIN stream_alignment_checks checks ON checks.activity_id=a.activity_id
        WHERE coalesce(m.verified,0)=0
        AND EXISTS (SELECT 1 FROM activity_points p WHERE p.activity_id=a.activity_id)
        AND EXISTS (SELECT 1 FROM segment_efforts e WHERE e.activity_id=a.activity_id)
        ORDER BY checks.checked_at IS NOT NULL, checks.checked_at, a.activity_id DESC""")).mappings().all()
    if candidate_file is None:
        return [row['activity_id'] for row in rows[:limit]]
    with Path(candidate_file).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if 'activity_id' not in (reader.fieldnames or []):
            raise ValueError('Candidate CSV must contain activity_id')
        ordered = []
        for row in reader:
            activity_id = int(row['activity_id'])
            if activity_id <= 0:
                raise ValueError('Candidate activity IDs must be positive integers')
            if activity_id not in ordered:
                ordered.append(activity_id)
    eligible = {row['activity_id']: row['checked_at'] for row in rows}
    ranks = {activity_id: rank for rank, activity_id in enumerate(ordered)}
    selected = [activity_id for activity_id in ordered if activity_id in eligible]
    # Unattempted candidates first, then older failed attempts. Within each group,
    # preserve audit ranking; successful verification is always skipped.
    selected.sort(key=lambda activity_id: (eligible[activity_id] is not None,
                  eligible[activity_id] or '', ranks[activity_id]))
    return selected[:limit]


def backfill(limit, candidate_file=None):
    # Check the local file before making any authenticated requests.
    if candidate_file is not None and not Path(candidate_file).is_file():
        raise FileNotFoundError(candidate_file)
    with engine.begin() as conn:
        conn.exec_driver_sql("""CREATE TABLE IF NOT EXISTS stream_alignment_checks (
            activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),
            checked_at TEXT NOT NULL, reason TEXT NOT NULL)""")
        ids = select_verification_activities(conn, limit, candidate_file)
    if not ids:
        print('No eligible unverified candidates remain in this selection.', flush=True)
        return
    from src.api.authenticate import StravaAuthenticator
    from src.api.client import StravaClient, StravaApiError, StravaRateLimitError
    client = StravaClient(StravaAuthenticator().get_access_token())
    print(f'Verifying {len(ids)} activities'+(' in coverage-priority order.' if candidate_file else '.'),flush=True)
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


DIMENSIONS = [
    ('activity_key', 'view_activity'), ('gear_key', 'view_gear'),
    ('activity_type_key', 'view_activity_type'), ('date_key', 'view_date'),
    ('trail_key', 'view_trail'), ('trail_system_key', 'view_trail_system'),
]

KEY_COUNTS_SQL = """SELECT activity_key, gear_key, activity_type_key, date_key,
    trail_key, trail_system_key, count(*) AS points,
    sum(incremental_distance_miles) AS miles,
    sum(date_basis='utc_fallback') AS utc_fallback_points,
    sum(date_basis='unresolved' OR recorded_at IS NULL) AS unresolved_local_points,
    sum(quality_status NOT IN ('valid','first_point')) AS uncertain_intervals
    FROM view_activity_points
    GROUP BY activity_key, gear_key, activity_type_key, date_key,
             trail_key, trail_system_key"""


class AuditProgress:
    """Flush progress and persist timings, including failed/interrupted steps."""

    def __init__(self, output, conn, explain=False):
        self.output, self.conn, self.explain = output, conn, explain
        self.started = time.perf_counter()
        self.state = {'started_at': datetime.now(timezone.utc).isoformat(),
                      'status': 'running', 'steps': []}
        self.plans = {}

    def save(self):
        self.state['elapsed_seconds'] = round(time.perf_counter()-self.started, 3)
        self.state['updated_at'] = datetime.now(timezone.utc).isoformat()
        temporary = self.output/'audit_status.json.tmp'
        temporary.write_text(json.dumps(self.state, indent=2)+'\n')
        temporary.replace(self.output/'audit_status.json')

    def run(self, label, action, sql=None):
        started = last_heartbeat = time.perf_counter()
        step = {'name': label, 'status': 'running'}
        self.state['steps'].append(step)
        self.save()
        print(f'[START] {label}', flush=True)
        raw = self.conn.connection.driver_connection

        def heartbeat():
            nonlocal last_heartbeat
            now = time.perf_counter()
            if now-last_heartbeat >= 5:
                step['elapsed_seconds'] = round(now-started, 3)
                print(f'[RUNNING] {label}: {now-started:.1f}s (SQLite active)', flush=True)
                self.save()
                last_heartbeat = now
            return 0

        raw.set_progress_handler(heartbeat, 100000)
        try:
            if self.explain and sql:
                self.plans[label] = [list(row) for row in self.conn.execute(text('EXPLAIN QUERY PLAN '+sql))]
                (self.output/'query_plans.json').write_text(json.dumps(self.plans, indent=2)+'\n')
            result = action()
            step['status'] = 'completed'
            return result
        except BaseException as error:
            step['status'] = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'failed'
            self.state['status'] = step['status']
            raise
        finally:
            raw.set_progress_handler(None, 0)
            step['elapsed_seconds'] = round(time.perf_counter()-started, 3)
            self.save()
            print(f'[{step["status"].upper()}] {label}: {step["elapsed_seconds"]:.2f}s', flush=True)


def audit(output, explain=False):
    output.mkdir(parents=True, exist_ok=True)
    print(f'Audit output: {output.resolve()}', flush=True)
    with engine.connect() as conn:
        progress = AuditProgress(output, conn, explain)

        def scalar(label, sql):
            return progress.run(label, lambda: conn.execute(text(sql)).scalar(), sql)

        summary = {}
        for table in ['activities','activity_streams','activity_points','view_activity','view_activity_point_segments']:
            summary[table] = scalar(f'Count {table}', f'SELECT count(*) FROM {table}')
        for name, column in [('quality','quality_status'), ('matches','match_method')]:
            sql = f'SELECT {column},count(*) FROM activity_points GROUP BY {column}'
            summary[name] = progress.run(f'Summarize {name}', lambda: dict(conn.execute(text(sql)).all()), sql)

        # Read point/source joins once and reduce millions of samples to key groups.
        # All work tables are connection-local TEMP tables; source data is unchanged.
        conn.exec_driver_sql('DROP TABLE IF EXISTS temp.audit_key_counts')
        progress.run('Group point keys and mileage once',
                     lambda: conn.exec_driver_sql('CREATE TEMP TABLE audit_key_counts AS '+KEY_COUNTS_SQL), KEY_COUNTS_SQL)
        summary['utc_fallback_points'] = scalar('Count UTC fallback points',
            'SELECT coalesce(sum(utc_fallback_points),0) FROM audit_key_counts')
        summary['unresolved_local_points'] = scalar('Count unresolved local timestamps',
            'SELECT coalesce(sum(unresolved_local_points),0) FROM audit_key_counts')
        summary['duplicate_point_keys'] = scalar('Check reporting point uniqueness',
            'SELECT count(*) FROM (SELECT activity_point_key FROM view_activity_points GROUP BY activity_point_key HAVING count(*)>1)')
        missing = {}
        for key, view in DIMENSIONS:
            table = 'audit_dim_'+key
            conn.exec_driver_sql(f'DROP TABLE IF EXISTS temp.{table}')
            sql = f'SELECT DISTINCT {key} FROM {view} WHERE {key} IS NOT NULL'

            def materialize(table=table, key=key, sql=sql):
                conn.exec_driver_sql(f'CREATE TEMP TABLE {table} AS '+sql)
                conn.exec_driver_sql(f'CREATE UNIQUE INDEX {table}_key ON {table}({key})')

            progress.run(f'Materialize {view} keys', materialize, sql)
            sql = f"""SELECT coalesce(sum(p.points),0) FROM audit_key_counts p
                LEFT JOIN {table} d ON d.{key}=p.{key}
                WHERE p.{key} IS NOT NULL AND d.{key} IS NULL"""
            missing[key] = scalar(f'Check {key} references', sql)
        summary['orphan_dimension_keys'] = missing
        queries = {
            'activity_mileage': """WITH totals AS (
                SELECT activity_key,sum(miles) AS miles,sum(points) AS points,
                sum(uncertain_intervals) AS uncertain FROM audit_key_counts GROUP BY activity_key)
                SELECT a.activity_id,a.name,a.distance_meters/1609.344 AS source_miles,
                t.miles AS point_miles,t.miles-a.distance_meters/1609.344 AS difference_miles,
                t.points AS gps_points,t.uncertain AS uncertain_intervals
                FROM totals t JOIN activities a ON a.activity_id=t.activity_key
                ORDER BY abs(coalesce(t.miles,0)-a.distance_meters/1609.344) DESC""",
            'trail_system_mileage': """SELECT t.trail_system_name,p.trail_system_key,
                sum(p.points) AS points,sum(p.miles) AS miles FROM audit_key_counts p
                LEFT JOIN view_trail_system t USING(trail_system_key)
                GROUP BY p.trail_system_key ORDER BY miles DESC""",
            'trail_mileage': """SELECT t.trail_name,p.trail_key,
                sum(p.points) AS points,sum(p.miles) AS miles FROM audit_key_counts p
                LEFT JOIN view_trail t USING(trail_key) GROUP BY p.trail_key ORDER BY miles DESC"""
        }
        for name, sql in queries.items():
            def write_csv(name=name, sql=sql):
                result = conn.execute(text(sql))
                temporary = output/(name+'.csv.tmp')
                with temporary.open('w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.writer(f)
                    writer.writerow(result.keys())
                    writer.writerows(result)
                temporary.replace(output/(name+'.csv'))
            progress.run(f'Write {name}.csv', write_csv, sql)
        failed = summary['duplicate_point_keys'] or any(missing.values())
        (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        progress.state['status'] = 'validation_failed' if failed else 'completed'
        progress.save()
    print(json.dumps(summary,indent=2), flush=True)
    print(f'Audit completed in {progress.state["elapsed_seconds"]:.2f}s. Files: {output.resolve()}', flush=True)
    if failed:
        raise SystemExit('Validation failed: duplicate point keys or orphan dimension keys')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--explain', action='store_true', help='Save SQLite query plans alongside audit timings')
    parser.add_argument('--verify-streams',action='store_true',help='Read original arrays from Strava and update alignment metadata only')
    parser.add_argument('--limit',type=int,default=5,help='Maximum activities to verify per run; repeat to resume')
    parser.add_argument('--candidate-file',type=Path,help='Prioritize eligible activities using coverage audit CSV order')
    parser.add_argument('--output',type=Path,default=ROOT/'exports'/'validation')
    args=parser.parse_args()
    if args.limit<1: parser.error('--limit must be positive')
    if args.candidate_file and not args.verify_streams: parser.error('--candidate-file requires --verify-streams')
    if args.verify_streams: backfill(args.limit,args.candidate_file)
    audit(args.output, explain=args.explain)
