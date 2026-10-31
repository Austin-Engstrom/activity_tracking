"""Resume paged Strava timezone backfill and update point dates without spatial matching."""
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy import text
from src.database.connection import engine

ROOT = Path(__file__).resolve().parents[2]


def parse_zone(raw):
    name = str(raw or '').split(') ', 1)[-1].strip()
    if not name:
        return None
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None
    return name


def local_date_key(stamp, zone):
    if stamp is None:
        return None
    parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.astimezone(ZoneInfo(zone)).strftime('%Y%m%d'))


def apply_timezones(conn, activities):
    conn.connection.driver_connection.create_function('local_date_key', 2, local_date_key, deterministic=True)
    updated = 0
    for activity in activities:
        zone = parse_zone(activity.get('timezone'))
        if zone is None:
            continue
        activity_id = activity['id']
        exists = conn.execute(text('SELECT 1 FROM activities WHERE activity_id=:id'), {'id':activity_id}).scalar()
        if not exists:
            continue
        previous = conn.execute(text('SELECT timezone_name FROM point_reporting_metadata WHERE activity_id=:id'), {'id':activity_id}).scalar()
        if previous == zone:
            continue
        # Metadata and date changes commit together. No coordinates or assignments change.
        conn.execute(text('UPDATE activity_points SET date_key=local_date_key(recorded_at_utc,:zone) WHERE activity_id=:id'), {'zone':zone,'id':activity_id})
        conn.execute(text('INSERT INTO point_reporting_metadata VALUES (:id,:zone) ON CONFLICT(activity_id) DO UPDATE SET timezone_name=excluded.timezone_name'), {'id':activity_id,'zone':zone})
        updated += 1
    return updated


def run(max_pages=2, restart=False, client=None):
    if client is None:
        from src.api.authenticate import StravaAuthenticator
        from src.api.client import StravaClient
        client = StravaClient(StravaAuthenticator().get_access_token())
    from src.api.client import StravaRateLimitError
    with engine.begin() as conn:
        conn.exec_driver_sql('''CREATE TABLE IF NOT EXISTS timezone_backfill_progress (
            id INTEGER PRIMARY KEY CHECK(id=1), before_epoch INTEGER NOT NULL,
            next_page INTEGER NOT NULL, exhausted INTEGER NOT NULL)''')
        if restart:
            conn.execute(text('DELETE FROM timezone_backfill_progress'))
        conn.execute(text('INSERT OR IGNORE INTO timezone_backfill_progress VALUES (1,:before,1,0)'), {'before':int(time.time())+1})
    for _ in range(max_pages):
        with engine.connect() as conn:
            state = conn.execute(text('SELECT * FROM timezone_backfill_progress WHERE id=1')).mappings().one()
        if state['exhausted']:
            print('Finished traversing Strava history. Use --restart to check again after new imports.',flush=True)
            break
        if not client.has_read_capacity():
            print('Stopped: Strava read capacity reserved. Resume later.',flush=True)
            break
        print(f'[START] Strava activity page {state["next_page"]}',flush=True)
        try:
            activities = client.get_activities_page(page=state['next_page'], per_page=200, before=state['before_epoch'])
        except StravaRateLimitError:
            print('Stopped: Strava rate limit reached. Resume later.',flush=True)
            break
        with engine.begin() as conn:
            updated = apply_timezones(conn, activities)
            conn.execute(text('UPDATE timezone_backfill_progress SET next_page=next_page+1,exhausted=:done WHERE id=1'), {'done':int(len(activities)<200)})
        print(f'[COMPLETED] {len(activities)} summaries read; {updated} local activities updated',flush=True)
    with engine.connect() as conn:
        missing = conn.execute(text('''SELECT count(*) FROM activities a WHERE EXISTS
            (SELECT 1 FROM activity_points p WHERE p.activity_id=a.activity_id)
            AND NOT EXISTS (SELECT 1 FROM point_reporting_metadata m
                            WHERE m.activity_id=a.activity_id AND m.timezone_name IS NOT NULL)''')).scalar()
    print(f'GPS activities still using UTC fallback: {missing}',flush=True)
    print('Date keys are updated. Re-export Parquet and refresh Power BI; no spatial rebuild needed.',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-pages',type=int,default=2,help='Up to 200 summaries per request; reruns resume automatically')
    parser.add_argument('--restart',action='store_true',help='Restart pagination without deleting timezone metadata')
    args=parser.parse_args()
    if args.max_pages<1: parser.error('--max-pages must be positive')
    run(args.max_pages,args.restart)
