"""Explain missing segment associations without changing data or using Strava."""
import argparse
import csv
import json
from pathlib import Path
from sqlalchemy import text
from src.database.connection import engine
from src.tools.validate_point_reporting import AuditProgress

ROOT=Path(__file__).resolve().parents[2]


GPS_SQL='''SELECT activity_id,count(*) AS gps_points,
    sum(trail_system_key IS NOT NULL) AS system_points,
    sum(trail_key IS NOT NULL) AS trail_points
    FROM activity_points GROUP BY activity_id'''
EFFORTS_SQL='''SELECT e.segment_id AS segment_key,count(*) AS efforts,
    count(DISTINCT e.activity_id) AS activities,
    sum(coalesce(a.verified,0)=1) AS verified_efforts
    FROM segment_efforts e JOIN coverage_gps g ON g.activity_id=e.activity_id
    LEFT JOIN stream_index_alignment a ON a.activity_id=e.activity_id
    GROUP BY e.segment_id'''
MEMBERSHIP_SQL='''SELECT m.segment_key,count(*) AS memberships,
    sum(p.trail_key IS NOT NULL) AS trail_memberships,
    sum(p.trail_system_key IS NOT NULL) AS system_memberships,
    sum(p.match_method LIKE '%ambiguous_trail%') AS ambiguous_memberships
    FROM view_activity_point_segments m
    JOIN activity_points p ON p.activity_point_key=m.activity_point_key
    GROUP BY m.segment_key'''
SEGMENTS_SQL='''SELECT s.segment_key,s.segment_name,
    coalesce(e.efforts,0) AS efforts,coalesce(e.activities,0) AS activities,
    coalesce(e.verified_efforts,0) AS verified_efforts,
    coalesce(m.memberships,0) AS memberships,
    coalesce(m.trail_memberships,0) AS trail_memberships,
    coalesce(m.system_memberships,0) AS system_memberships,
    coalesce(m.ambiguous_memberships,0) AS ambiguous_memberships,
    CASE WHEN m.trail_memberships>0 THEN 'named_trail_observed'
         WHEN m.system_memberships>0 THEN 'system_only_observed'
         WHEN m.memberships>0 THEN 'verified_points_outside_mapped_systems'
         WHEN e.verified_efforts>0 THEN 'verified_efforts_without_gps_memberships'
         WHEN e.efforts>0 THEN 'awaiting_verification'
         ELSE 'no_gps_efforts' END AS coverage_status
    FROM view_segment s LEFT JOIN coverage_efforts e USING(segment_key)
    LEFT JOIN coverage_memberships m USING(segment_key)'''
CANDIDATES_SQL='''SELECT e.activity_id,a.name AS activity_name,
    count(DISTINCT CASE WHEN c.trail_memberships=0 THEN e.segment_id END)
        AS candidate_uncovered_segments,
    count(DISTINCT e.segment_id) AS segments_in_activity,
    g.gps_points,g.system_points,g.trail_points
    FROM segment_efforts e JOIN coverage_gps g ON g.activity_id=e.activity_id
    JOIN coverage_segments c ON c.segment_key=e.segment_id
    JOIN activities a ON a.activity_id=e.activity_id
    LEFT JOIN stream_index_alignment v ON v.activity_id=e.activity_id
    WHERE coalesce(v.verified,0)=0
    GROUP BY e.activity_id
    ORDER BY g.trail_points>0 DESC,candidate_uncovered_segments DESC,
             g.system_points>0 DESC,e.activity_id DESC'''
SYSTEMS_SQL='''SELECT s.trail_system_id,s.name,
    count(t.official_trail_id) AS catalog_trails,
    sum(t.combined_geometry_geojson IS NOT NULL) AS trails_with_geometry,
    s.boundary_confirmed,s.boundary_geojson IS NOT NULL AS has_boundary
    FROM trail_systems s LEFT JOIN official_trails t USING(trail_system_id)
    GROUP BY s.trail_system_id ORDER BY s.name'''


def run(output, explain=False):
    output.mkdir(parents=True,exist_ok=True)
    with engine.connect() as conn:
        progress=AuditProgress(output,conn,explain)
        for table,sql in [('coverage_gps',GPS_SQL),('coverage_efforts',EFFORTS_SQL),
                          ('coverage_memberships',MEMBERSHIP_SQL),('coverage_segments',SEGMENTS_SQL)]:
            conn.exec_driver_sql('DROP TABLE IF EXISTS temp.'+table)
            progress.run('Build '+table,lambda table=table,sql=sql:
                conn.exec_driver_sql('CREATE TEMP TABLE '+table+' AS '+sql),sql)
            key='activity_id' if table=='coverage_gps' else 'segment_key'
            conn.exec_driver_sql(f'CREATE UNIQUE INDEX {table}_key ON {table}({key})')
        status_sql='SELECT coverage_status,count(*) FROM coverage_segments GROUP BY coverage_status'
        statuses=progress.run('Summarize segment coverage',lambda:dict(conn.execute(text(status_sql)).all()),status_sql)
        total=sum(statuses.values())
        summary={'segments':total,'coverage_status_counts':statuses,
            'named_trail_segments':statuses.get('named_trail_observed',0),
            'system_associated_segments':statuses.get('named_trail_observed',0)+statuses.get('system_only_observed',0)}
        summary['named_trail_coverage_percent']=100*summary['named_trail_segments']/total if total else None
        for filename,sql in [('segments', 'SELECT * FROM coverage_segments ORDER BY coverage_status,segment_key'),
                             ('verification_candidates',CANDIDATES_SQL),('system_geometry',SYSTEMS_SQL)]:
            def write(filename=filename,sql=sql):
                result=conn.execute(text(sql))
                target=output/(filename+'.csv')
                temporary=target.with_suffix('.csv.tmp')
                with temporary.open('w',newline='',encoding='utf-8-sig') as f:
                    writer=csv.writer(f);writer.writerow(result.keys());writer.writerows(result)
                temporary.replace(target)
            progress.run('Write '+filename+'.csv',write,sql)
        progress.state['status']='completed';progress.save()
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)
    print(f'Coverage files: {output.resolve()}',flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'exports/validation/segment_coverage')
    parser.add_argument('--explain',action='store_true')
    args=parser.parse_args()
    run(args.output,args.explain)
