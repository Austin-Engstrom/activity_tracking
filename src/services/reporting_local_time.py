"""Resolve reporting timezones offline and materialize UTC-offset intervals."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from sqlalchemy import text

DDL = '''
CREATE TABLE IF NOT EXISTS reporting_activity_timezones (
 activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),
 timezone_name TEXT, timezone_source TEXT NOT NULL,
 utc_start TEXT, utc_end TEXT
);
CREATE TABLE IF NOT EXISTS reporting_timezone_offsets (
 activity_id INTEGER NOT NULL REFERENCES activities(activity_id),
 utc_start TEXT NOT NULL, utc_end TEXT NOT NULL, offset_seconds INTEGER NOT NULL,
 PRIMARY KEY(activity_id,utc_start)
);
'''


def zone_name(raw):
    name = str(raw or '').split(') ',1)[-1].strip()
    if not name:
        return None
    try:
        ZoneInfo(name)
        return name
    except (ZoneInfoNotFoundError, ValueError):
        return None


@lru_cache(maxsize=1)
def finder():
    from timezonefinder import TimezoneFinder
    return TimezoneFinder()


@lru_cache(maxsize=4096)
def gps_timezone(latitude, longitude):
    return zone_name(finder().timezone_at(lat=latitude,lng=longitude))


def utc_stamp(raw):
    if raw is None:
        return None
    dt = datetime.fromisoformat(str(raw).replace('Z','+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def intervals(start, end, zone):
    """Split a UTC span at offset changes, including DST and half-hour changes."""
    tz = ZoneInfo(zone)
    offset = lambda stamp: int(stamp.astimezone(tz).utcoffset().total_seconds())
    begin = cursor = start
    current = offset(start)
    rows = []
    while cursor < end:
        probe = min(cursor+timedelta(hours=1), end)
        next_offset = offset(probe)
        if next_offset != current:
            low, high = cursor, probe
            while (high-low).total_seconds() > 1:
                mid = low + timedelta(seconds=int((high-low).total_seconds())//2)
                if offset(mid)==current: low=mid
                else: high=mid
            rows.append((begin,high,current))
            begin = high
            current = next_offset
        cursor = probe
    if begin < end: rows.append((begin,end,current))
    return rows


def refresh_local_times(conn, update_point_dates=True, lookup=None, force=False):
    """Refresh derived metadata atomically. Never overwrite source UTC timestamps."""
    for statement in DDL.split(';'):
        if statement.strip():conn.exec_driver_sql(statement)
    activities=conn.exec_driver_sql('''SELECT a.activity_id,a.start_date,a.elapsed_time_seconds,m.timezone_name,
      (SELECT latitude FROM activity_streams s WHERE s.activity_id=a.activity_id
         AND latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180 ORDER BY point_index LIMIT 1) latitude,
      (SELECT longitude FROM activity_streams s WHERE s.activity_id=a.activity_id
         AND latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180 ORDER BY point_index LIMIT 1) longitude,
      (SELECT max(time_seconds) FROM activity_streams s WHERE s.activity_id=a.activity_id) stream_seconds,
      (SELECT min(start_date) FROM segment_efforts e WHERE e.activity_id=a.activity_id) effort_start,
      (SELECT max(datetime(start_date, printf('+%d seconds',elapsed_time_seconds))) FROM segment_efforts e WHERE e.activity_id=a.activity_id) effort_end
      FROM activities a LEFT JOIN point_reporting_metadata m USING(activity_id)''').mappings().all()
    summary={}
    for activity in activities:
        key=activity['activity_id'];zone=zone_name(activity['timezone_name']);basis='strava'
        if zone is None and activity['latitude'] is not None:
            zone=(lookup or gps_timezone)(activity['latitude'],activity['longitude'])
            zone=zone_name(zone);basis='first_gps'
        if zone is None: basis='unresolved'
        start=utc_stamp(activity['start_date'])
        if start is None: continue
        duration=max([float(v) for v in [activity['elapsed_time_seconds'],activity['stream_seconds'],0]
                      if v is not None and isfinite(float(v)) and float(v)>=0])
        end=start+timedelta(seconds=duration+1)
        if activity['effort_start']:start=min(start,utc_stamp(activity['effort_start']))
        if activity['effort_end']:end=max(end,utc_stamp(activity['effort_end'])+timedelta(seconds=1))
        values={'id':key,'zone':zone,'basis':basis,'start':start.strftime('%Y-%m-%d %H:%M:%S'),'end':end.strftime('%Y-%m-%d %H:%M:%S')}
        previous=conn.execute(text('SELECT * FROM reporting_activity_timezones WHERE activity_id=:id'),values).mappings().first()
        changed=force or previous is None or any(previous[col]!=values[param] for col,param in [('timezone_name','zone'),('timezone_source','basis'),('utc_start','start'),('utc_end','end')])
        if changed:
            conn.execute(text('INSERT INTO reporting_activity_timezones VALUES (:id,:zone,:basis,:start,:end) ON CONFLICT(activity_id) DO UPDATE SET timezone_name=:zone,timezone_source=:basis,utc_start=:start,utc_end=:end'),values)
            conn.execute(text('DELETE FROM reporting_timezone_offsets WHERE activity_id=:id'),values)
            if zone:
                rows=[{'id':key,'start':lo.strftime('%Y-%m-%d %H:%M:%S'),'end':hi.strftime('%Y-%m-%d %H:%M:%S'),'offset':seconds} for lo,hi,seconds in intervals(start,end,zone)]
                conn.execute(text('INSERT INTO reporting_timezone_offsets VALUES (:id,:start,:end,:offset)'),rows)
        if update_point_dates and changed:
            if zone:
                # Update only when a date changed. Offset intervals remain valid across DST.
                for row in conn.execute(text('SELECT * FROM reporting_timezone_offsets WHERE activity_id=:id'),values).mappings():
                    conn.execute(text('''UPDATE activity_points SET date_key=cast(strftime('%Y%m%d',recorded_at_utc,printf('%+d seconds',:offset)) AS INTEGER)
                        WHERE activity_id=:id AND datetime(recorded_at_utc)>=:start AND datetime(recorded_at_utc)<:end
                        AND date_key IS NOT cast(strftime('%Y%m%d',recorded_at_utc,printf('%+d seconds',:offset)) AS INTEGER)'''),
                        {'id':key,'offset':row['offset_seconds'],'start':row['utc_start'],'end':row['utc_end']})
            else:
                conn.execute(text('UPDATE activity_points SET date_key=NULL WHERE activity_id=:id AND date_key IS NOT NULL'),values)
        summary[basis]=summary.get(basis,0)+1
    return summary
