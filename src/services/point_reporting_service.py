"""Rebuild derived GPS reporting without modifying source streams."""
import json
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from shapely.geometry import Point, shape
from sqlalchemy import text
from src.services.reporting_local_time import DDL as LOCAL_TIME_DDL, refresh_local_times

DDL = """
CREATE TABLE IF NOT EXISTS activity_points (
 activity_point_key TEXT PRIMARY KEY,
 activity_id INTEGER NOT NULL REFERENCES activities(activity_id),
 point_index INTEGER NOT NULL,
 recorded_at_utc TEXT, date_key INTEGER,
 trail_system_key INTEGER REFERENCES trail_systems(trail_system_id),
 trail_key INTEGER REFERENCES official_trails(official_trail_id),
 incremental_distance_meters REAL, incremental_time_seconds REAL,
 quality_status TEXT NOT NULL, match_method TEXT NOT NULL,
 UNIQUE(activity_id, point_index)
);
CREATE INDEX IF NOT EXISTS ix_points_activity ON activity_points(activity_id);
CREATE INDEX IF NOT EXISTS ix_points_system ON activity_points(trail_system_key);
CREATE TABLE IF NOT EXISTS stream_index_alignment (
 activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),
 verified INTEGER NOT NULL CHECK(verified IN (0,1))
);
CREATE TABLE IF NOT EXISTS point_reporting_metadata (
 activity_id INTEGER PRIMARY KEY REFERENCES activities(activity_id),
 timezone_name TEXT
);
"""

DDL += LOCAL_TIME_DDL


def valid_point(row):
    lat, lon = row['latitude'], row['longitude']
    return (lat is not None and lon is not None and math.isfinite(lat)
            and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180)


def geometry(raw):
    data = json.loads(raw)
    if data.get('type') == 'Feature':
        data = data['geometry']
    g = shape(data)
    if not g.is_valid or g.is_empty:
        raise ValueError('Invalid or empty mapping geometry; correct it before rebuilding')
    return g


def rebuild_points(connection, max_gap_seconds=60, tolerance_feet=40,
                   ambiguity_feet=10):
    """Atomic, deterministic rebuild; caller owns the transaction.

    Intervals end at each point. Invalid/missing predecessor coordinates,
    nonpositive time, negative distance and long gaps yield NULL increments.
    """
    if max_gap_seconds <= 0 or tolerance_feet <= 0 or ambiguity_feet < 0:
        raise ValueError('Invalid matching thresholds')
    for statement in DDL.split(';'):
        if statement.strip():
            connection.exec_driver_sql(statement)
    systems = [(x['trail_system_id'], geometry(x['boundary_geojson'])) for x in
        connection.execute(text("SELECT * FROM trail_systems WHERE boundary_confirmed=1 AND boundary_geojson IS NOT NULL ORDER BY trail_system_id")).mappings()]
    trails = [(x['official_trail_id'], x['trail_system_id'], geometry(x['combined_geometry_geojson'])) for x in
        connection.execute(text("SELECT * FROM official_trails WHERE combined_geometry_geojson IS NOT NULL ORDER BY official_trail_id")).mappings()]
    refresh_local_times(connection, update_point_dates=False)
    connection.execute(text('DELETE FROM activity_points'))
    count = 0
    activities = connection.execute(text('SELECT a.*, m.timezone_name FROM activities a LEFT JOIN reporting_activity_timezones m ON m.activity_id=a.activity_id')).mappings()
    for a in activities:
        start = datetime.fromisoformat(str(a['start_date']).replace('Z','+00:00'))
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        local_zone = ZoneInfo(a['timezone_name']) if a['timezone_name'] else None
        # Project each candidate trail once per activity, not once per sample.
        from pyproj import Transformer
        from shapely.ops import transform
        anchor = connection.execute(text('SELECT longitude,latitude FROM activity_streams WHERE activity_id=:id AND latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180 LIMIT 1'), {'id':a['activity_id']}).first()
        if anchor is None:
            continue
        project = Transformer.from_crs('EPSG:4326', f'+proj=aeqd +lat_0={anchor[1]} +lon_0={anchor[0]} +datum=WGS84 +units=m', always_xy=True).transform
        projected = [(key,sys,transform(project,g)) for key,sys,g in trails]
        previous = None
        batch = []
        for p in connection.execute(text('SELECT * FROM activity_streams WHERE activity_id=:id ORDER BY point_index'), {'id':a['activity_id']}).mappings():
            if not valid_point(p):
                previous = p
                continue
            dt = dd = None
            status = 'first_point' if previous is None else 'invalid_interval'
            if previous is not None and valid_point(previous):
                if all(v is not None and math.isfinite(v) for v in [p['time_seconds'],previous['time_seconds'],p['distance_meters'],previous['distance_meters']]):
                    elapsed = p['time_seconds']-previous['time_seconds']
                    distance = p['distance_meters']-previous['distance_meters']
                    if elapsed > max_gap_seconds:
                        status = 'recording_gap'
                    elif elapsed > 0 and distance >= 0:
                        dt, dd, status = elapsed, distance, 'valid'
            point = Point(p['longitude'],p['latitude'])
            candidates = [key for key,g in systems if g.covers(point)]
            system = candidates[0] if candidates else None
            method = 'boundary_overlap_lowest_id' if len(candidates)>1 else ('boundary' if candidates else 'unmatched')
            projected_point = Point(*project(p['longitude'],p['latitude']))
            distances = sorted((g.distance(projected_point)/0.3048,key) for key,sys,g in projected if sys==system)
            trail = None
            if distances and distances[0][0] <= tolerance_feet:
                if len(distances)>1 and distances[1][0]-distances[0][0] <= ambiguity_feet:
                    method += ':ambiguous_trail'
                else:
                    trail = distances[0][1]
                    method += ':nearest_trail'
            stamp = start + timedelta(seconds=p['time_seconds']) if p['time_seconds'] is not None and math.isfinite(p['time_seconds']) and p['time_seconds'] >= 0 else None
            batch.append(dict(key=f"{a['activity_id']}:{p['point_index']}",activity=a['activity_id'],idx=p['point_index'],stamp=stamp.astimezone(timezone.utc).isoformat() if stamp else None,date=int(stamp.astimezone(local_zone).strftime('%Y%m%d')) if stamp and local_zone else None,system=system,trail=trail,dd=dd,dt=dt,status=status,method=method))
            previous = p
        if batch:
            connection.execute(text("""INSERT INTO activity_points VALUES (:key,:activity,:idx,:stamp,:date,:system,:trail,:dd,:dt,:status,:method)"""),batch)
            count += len(batch)
    return count
