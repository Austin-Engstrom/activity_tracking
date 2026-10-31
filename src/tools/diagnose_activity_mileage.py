"""Read-only interval reconciliation for selected activities; no API requests."""
import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from sqlalchemy import text
from src.database.connection import engine
from src.services.point_reporting_service import valid_point

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IDS = [3783144977, 3014709305, 13754599440, 4025354177, 15584208194]
METERS_PER_MILE = 1609.344


def finite(value):
    return value is not None and math.isfinite(value)


def miles(value):
    return value / METERS_PER_MILE if finite(value) else None


def analyze(activity, rows, gap_seconds=60):
    """Explain observed stored totals separately from hypothetical gap policies."""
    intervals = []
    previous = None
    for row in rows:
        delta_time = delta_distance = None
        if previous is not None:
            if all(finite(x['time_seconds']) for x in (previous, row)):
                delta_time = row['time_seconds'] - previous['time_seconds']
            if all(finite(x['distance_meters']) for x in (previous, row)):
                delta_distance = row['distance_meters'] - previous['distance_meters']
        both_gps = previous is not None and valid_point(previous) and valid_point(row)
        if previous is None:
            reason = 'first_sample'
        elif not both_gps:
            reason = 'missing_or_invalid_coordinates'
        elif delta_time is None or delta_distance is None:
            reason = 'missing_or_nonfinite_time_or_distance'
        elif delta_time > gap_seconds:
            reason = 'recording_gap'
        elif delta_time <= 0:
            reason = 'nonpositive_elapsed_time'
        elif delta_distance < 0:
            reason = 'negative_distance_increment'
        else:
            reason = 'eligible_interval'
        included = finite(row['stored_increment_meters'])
        intervals.append(dict(
            point_index=row['point_index'],
            previous_point_index=previous['point_index'] if previous is not None else None,
            elapsed_time_seconds=row['time_seconds'],
            cumulative_distance_miles=miles(row['distance_meters']),
            delta_time_seconds=delta_time,
            delta_distance_miles=miles(delta_distance),
            implied_speed_mph=delta_distance/delta_time*3600/METERS_PER_MILE
                if delta_distance is not None and delta_time is not None and delta_time>0 else None,
            has_valid_gps=valid_point(row), both_endpoints_valid_gps=both_gps,
            present_in_reporting=row['reporting_index'] is not None,
            stored_quality_status=row['quality_status'],
            stored_increment_miles=miles(row['stored_increment_meters']),
            diagnostic_reason=reason,
            excluded_signed_distance_miles=miles(delta_distance) if not included else 0.0,
            is_moving=row['is_moving']))
        previous = row
    stored = [r['stored_increment_meters'] for r in rows if finite(r['stored_increment_meters'])]
    gps = [r for r in rows if valid_point(r)]
    known_deltas = [r['delta_distance_miles'] for r in intervals if r['delta_distance_miles'] is not None]
    excluded = [r['excluded_signed_distance_miles'] for r in intervals if r['excluded_signed_distance_miles'] is not None]
    first = rows[0] if rows else None
    last = rows[-1] if rows else None
    point_total = miles(sum(stored)) if stored else None
    source = miles(activity['distance_meters'])
    last_distance = miles(last['distance_meters']) if last else None
    scenarios = {}
    for threshold in [60, 120, 300, None]:
        candidates = [r['delta_distance_miles'] for r in intervals
            if r['both_endpoints_valid_gps'] and r['delta_time_seconds'] is not None
            and r['delta_time_seconds']>0 and r['delta_distance_miles'] is not None
            and r['delta_distance_miles']>=0
            and (threshold is None or r['delta_time_seconds']<=threshold)]
        scenarios[str(threshold) if threshold else 'no_time_gap_limit'] = sum(candidates) if candidates else None
    summary = dict(activity_id=activity['activity_id'], activity_name=activity['name'],
        source_miles=source, stored_point_miles=point_total,
        source_minus_stored_point_miles=source-point_total if source is not None and point_total is not None else None,
        stream_rows=len(rows), valid_gps_rows=len(gps), included_intervals=len(stored),
        first_stream_index=first['point_index'] if first else None,
        last_stream_index=last['point_index'] if last else None,
        first_stream_elapsed_seconds=first['time_seconds'] if first else None,
        last_stream_elapsed_seconds=last['time_seconds'] if last else None,
        source_elapsed_seconds=activity['elapsed_time_seconds'],
        first_stream_distance_miles=miles(first['distance_meters']) if first else None,
        last_stream_distance_miles=last_distance,
        source_minus_last_stream_miles=source-last_distance if source is not None and last_distance is not None else None,
        first_gps_index=gps[0]['point_index'] if gps else None,
        last_gps_index=gps[-1]['point_index'] if gps else None,
        first_gps_distance_miles=miles(gps[0]['distance_meters']) if gps else None,
        last_gps_distance_miles=miles(gps[-1]['distance_meters']) if gps else None,
        known_stream_delta_sum_miles=sum(known_deltas),
        excluded_signed_delta_sum_miles=sum(excluded),
        intervals_without_known_distance_delta=sum(r['previous_point_index'] is not None and r['delta_distance_miles'] is None for r in intervals),
        negative_distance_intervals=sum(r['delta_distance_miles'] is not None and r['delta_distance_miles']<0 for r in intervals),
        diagnostic_reason_counts=dict(Counter(r['diagnostic_reason'] for r in intervals)),
        diagnostic_gap_seconds=gap_seconds,
        hypothetical_point_miles_by_gap_seconds=scenarios)
    summary['excluded_signed_miles_by_reason'] = {
        reason: sum(r['excluded_signed_distance_miles'] or 0 for r in intervals if r['diagnostic_reason']==reason)
        for reason in summary['diagnostic_reason_counts']}
    return summary, intervals


def run(ids, output, gap_seconds=60):
    output.mkdir(parents=True, exist_ok=True)
    summaries = []
    with engine.connect() as conn:
        for activity_id in ids:
            print(f'[START] Diagnose activity {activity_id}', flush=True)
            activity = conn.execute(text('SELECT activity_id,name,distance_meters,elapsed_time_seconds FROM activities WHERE activity_id=:id'), {'id':activity_id}).mappings().first()
            if activity is None:
                raise ValueError(f'Activity {activity_id} does not exist')
            rows = conn.execute(text('''SELECT s.*, p.point_index AS reporting_index,
                p.quality_status,p.incremental_distance_meters AS stored_increment_meters
                FROM activity_streams s LEFT JOIN activity_points p
                ON p.activity_id=s.activity_id AND p.point_index=s.point_index
                WHERE s.activity_id=:id ORDER BY s.point_index'''), {'id':activity_id}).mappings().all()
            summary, intervals = analyze(activity, rows, gap_seconds)
            summaries.append(summary)
            if intervals:
                target=output/f'{activity_id}_intervals.csv'
                temporary=target.with_suffix('.csv.tmp')
                with temporary.open('w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.DictWriter(f,fieldnames=intervals[0].keys())
                    writer.writeheader();writer.writerows(intervals)
                temporary.replace(target)
            print(json.dumps(summary,indent=2,allow_nan=False),flush=True)
    temporary=output/'summary.json.tmp'
    temporary.write_text(json.dumps(summaries,indent=2,allow_nan=False)+'\n')
    temporary.replace(output/'summary.json')
    print(f'Diagnostics: {output.resolve()}',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activity-ids',type=int,nargs='+',default=DEFAULT_IDS)
    parser.add_argument('--output',type=Path,default=ROOT/'exports'/'validation'/'mileage_diagnostics')
    parser.add_argument('--gap-seconds',type=float,default=60,
        help='Diagnostic reason threshold only; does not change stored reporting')
    args=parser.parse_args()
    if not math.isfinite(args.gap_seconds) or args.gap_seconds<=0:
        parser.error('--gap-seconds must be finite and positive')
    run(args.activity_ids,args.output,args.gap_seconds)
