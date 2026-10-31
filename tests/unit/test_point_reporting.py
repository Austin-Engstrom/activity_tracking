"""Offline regression checks for GPS grain and mileage attribution."""
import json
import unittest
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from src.models import Base
from src.services.point_reporting_service import DDL, rebuild_points

ROOT = Path(__file__).resolve().parents[2]

class PointReportingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.c = self.engine.connect()
        for sql in DDL.split(';'):
            if sql.strip(): self.c.exec_driver_sql(sql)
        self.c.exec_driver_sql("CREATE TABLE activity_type_categories(activity_type TEXT PRIMARY KEY,activity_category TEXT)")
        self.c.exec_driver_sql("INSERT INTO activities(activity_id,athlete_id,name,sport_type,start_date,distance_meters,moving_time_seconds,elapsed_time_seconds,total_elevation_gain_meters,trainer,commute,created_at,updated_at) VALUES (1,1,'ride','Ride','2026-01-02 00:00:00',100,20,20,0,0,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),(2,1,'indoor','Ride','2026-01-02 00:00:00',100,20,20,0,1,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        polygon=json.dumps({'type':'Polygon','coordinates':[[[-94,40],[-92,40],[-92,42],[-94,42],[-94,40]]]})
        for key in [1,2]:
            self.c.execute(text("INSERT INTO trail_systems(trail_system_id,name,country,boundary_confirmed,boundary_geojson,created_at,updated_at) VALUES (:id,:name,'US',1,:g,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"),dict(id=key,name=f'system{key}',g=polygon))
        line=json.dumps({'type':'LineString','coordinates':[[-93,40],[-93,42]]})
        self.c.execute(text("INSERT INTO official_trails(official_trail_id,trail_system_id,name,normalized_name,total_length_meters,section_count,combined_geometry_geojson,created_at,updated_at) VALUES (1,1,'trail','trail',100,1,:g,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"),dict(g=line))
        self.c.exec_driver_sql("INSERT INTO point_reporting_metadata VALUES (1,'America/Chicago')")

    def tearDown(self):
        self.c.close();self.engine.dispose()

    def streams(self, rows):
        self.c.execute(text('INSERT INTO activity_streams(activity_id,point_index,time_seconds,distance_meters,latitude,longitude,altitude_meters,velocity_mps,temperature_c,is_moving,created_at) VALUES(1,:i,:t,:d,:lat,-93,100,1,0,1,:created)'),[dict(i=i,t=t,d=d,lat=lat,created=datetime.now()) for i,t,d,lat in rows])

    def views(self):
        files=['sql/views/facts/view_activity.sql','sql/views/dimensions/view_segment.sql','sql/views/dimensions/view_date.sql']
        files += [str(p.relative_to(ROOT)) for p in (ROOT/'sql/views/points').glob('*.sql')]
        for f in files:
            for sql in (ROOT/f).read_text().split(';'):
                if sql.strip(): self.c.exec_driver_sql(sql)

    def test_grain_units_system_trail_timezone_and_repeatability(self):
        self.streams([(0,0,0,41),(1,10,25,41),(2,20,100,41)])
        self.assertEqual(rebuild_points(self.c),3)
        self.views()
        row=self.c.execute(text('SELECT sum(incremental_distance_miles),min(date_key),max(trail_system_key),max(trail_key) FROM view_activity_points')).one()
        self.assertAlmostEqual(row[0],100/1609.344)
        self.assertEqual(tuple(row[1:]),(20260101,1,1))
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM view_activity').scalar(),1)
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM view_date').scalar(),1)
        self.assertAlmostEqual(self.c.exec_driver_sql('SELECT elevation_feet FROM view_activity_points LIMIT 1').scalar(),100/.3048)
        self.assertEqual(rebuild_points(self.c),3)
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM activity_points').scalar(),3)

    def test_missing_coordinates_gaps_and_negative_distance(self):
        self.streams([(0,0,0,41),(1,10,25,None),(2,20,50,41),(3,200,75,41),(4,210,70,41)])
        rebuild_points(self.c);self.views()
        rows=self.c.exec_driver_sql('SELECT point_index,quality_status,incremental_distance_meters FROM activity_points ORDER BY point_index').all()
        self.assertEqual([r[0] for r in rows],[0,2,3,4])
        self.assertEqual([r[1] for r in rows],['first_point','invalid_interval','recording_gap','invalid_interval'])
        self.assertTrue(all(r[2] is None for r in rows))

    def test_overlapping_segments_and_repeated_efforts(self):
        self.streams([(0,0,0,41),(1,10,25,41),(2,20,50,41)])
        self.c.exec_driver_sql("INSERT INTO segments(segment_id,name,created_at,updated_at) VALUES (1,'segment',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),(2,'overlap',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        self.c.exec_driver_sql("INSERT INTO segment_efforts(segment_effort_id,activity_id,segment_id,name,elapsed_time_seconds,moving_time_seconds,start_date,start_index,end_index,created_at,updated_at) VALUES (1,1,1,'first',10,10,'2026-01-02',0,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),(2,1,2,'overlap',10,10,'2026-01-02',1,2,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP),(3,1,1,'repeat',10,10,'2026-01-02',2,2,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        self.c.exec_driver_sql('INSERT INTO stream_index_alignment VALUES (1,1)')
        rebuild_points(self.c);self.views()
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM view_segment').scalar(),2)
        self.assertEqual(self.c.exec_driver_sql("SELECT count(*) FROM view_activity_point_segments WHERE activity_point_key='1:1'").scalar(),2)
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM view_point_segment_effort').scalar(),3)
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM view_activity_points').scalar(),3)

    def test_ambiguous_trail_is_not_arbitrarily_assigned(self):
        self.streams([(0,0,0,41)])
        self.c.exec_driver_sql("INSERT INTO official_trails SELECT 2,trail_system_id,'other','other',total_length_meters,section_count,primary_surface,bicycle_access,mtb_scale,mtb_type,combined_geometry_geojson,created_at,updated_at FROM official_trails WHERE official_trail_id=1")
        rebuild_points(self.c)
        row=self.c.exec_driver_sql('SELECT trail_key,match_method FROM activity_points').one()
        self.assertIsNone(row[0]);self.assertIn('ambiguous_trail',row[1])

    def test_unverified_streams_do_not_link_segments(self):
        self.test_overlapping_segments_and_repeated_efforts()
        self.c.exec_driver_sql('DELETE FROM stream_index_alignment')
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM view_activity_point_segments').scalar(),0)

    def test_parquet_round_trip_preserves_small_distance(self):
        from tempfile import TemporaryDirectory
        import pandas as pd
        from src.tools.export_power_bi import export_view
        self.streams([(0,0,0,41),(1,1,0.1,41)])
        rebuild_points(self.c);self.views()
        with TemporaryDirectory() as folder:
            result=export_view(self.c,'view_activity_points',Path(folder))
            self.assertTrue(result.success,result.error)
            frame=pd.read_parquet(Path(folder)/'view_activity_points.parquet')
            self.assertEqual(len(frame),2)
            self.assertAlmostEqual(frame.incremental_distance_miles.sum(),0.1/1609.344)

    def test_mapper_captures_timezone(self):
        from src.etl.activity_mapper import ActivityMapper
        activity=ActivityMapper.from_api(dict(id=1,athlete={'id':1},name='ride',sport_type='Ride',start_date='2026-01-01T00:00:00Z',timezone='(GMT-06:00) America/Chicago'))
        self.assertEqual(activity.reporting_timezone,'America/Chicago')

    def test_failed_rebuild_rolls_back_derived_rows(self):
        self.streams([(0,0,0,41)])
        rebuild_points(self.c)
        self.c.exec_driver_sql("UPDATE point_reporting_metadata SET timezone_name='Invalid/Zone'")
        with self.assertRaises(Exception):
            with self.c.begin_nested():
                rebuild_points(self.c)
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM activity_points').scalar(),1)
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM activity_streams').scalar(),1)

    def test_outside_boundary_stays_unmatched(self):
        self.streams([(0,0,0,45)])
        rebuild_points(self.c)
        row=self.c.exec_driver_sql('SELECT trail_system_key,trail_key,match_method FROM activity_points').one()
        self.assertEqual(tuple(row),(None,None,'unmatched'))

    def test_populated_audit_outputs(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from src.tools.validate_point_reporting import audit
        self.streams([(0,0,0,41),(1,10,100,41)])
        rebuild_points(self.c);self.views()
        for name in ['view_gear','view_activity_type','view_trail_system']:
            sql=(ROOT/'sql/views/dimensions'/f'{name}.sql').read_text()
            for statement in sql.split(';'):
                if statement.strip(): self.c.exec_driver_sql(statement)
        self.c.commit()
        with TemporaryDirectory() as folder:
            with patch('src.tools.validate_point_reporting.engine',self.engine):
                audit(Path(folder), explain=True)
            summary=json.loads((Path(folder)/'summary.json').read_text())
            self.assertEqual(summary['activity_points'],2)
            self.assertEqual(summary['view_activity'],1)
            self.assertEqual(summary['duplicate_point_keys'],0)
            self.assertTrue(all(v==0 for v in summary['orphan_dimension_keys'].values()))
            self.assertTrue((Path(folder)/'activity_mileage.csv').exists())
            status=json.loads((Path(folder)/'audit_status.json').read_text())
            self.assertEqual(status['status'],'completed')
            self.assertTrue(all(step['status']=='completed' for step in status['steps']))
            plans=json.loads((Path(folder)/'query_plans.json').read_text())
            date_plan=' '.join(str(row[-1]) for row in plans['Check date_key references'])
            self.assertNotIn('CORRELATED',date_plan)
            self.assertNotIn('calendar',date_plan)
            self.assertIn('audit_dim_date_key_key',date_plan)


    def test_audit_counts_orphan_points_after_grouping(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from src.tools.validate_point_reporting import audit
        self.streams([(0,0,0,41),(1,10,100,41)])
        rebuild_points(self.c);self.views()
        for name in ['view_gear','view_activity_type','view_trail_system']:
            for statement in (ROOT/'sql/views/dimensions'/f'{name}.sql').read_text().split(';'):
                if statement.strip(): self.c.exec_driver_sql(statement)
        self.c.exec_driver_sql('UPDATE activity_points SET trail_key=999')
        self.c.commit()
        with TemporaryDirectory() as folder:
            with patch('src.tools.validate_point_reporting.engine',self.engine):
                with self.assertRaises(SystemExit):
                    audit(Path(folder))
            summary=json.loads((Path(folder)/'summary.json').read_text())
            self.assertEqual(summary['orphan_dimension_keys']['trail_key'],2)
            status=json.loads((Path(folder)/'audit_status.json').read_text())
            self.assertEqual(status['status'],'validation_failed')

    def test_audit_records_failed_query(self):
        from tempfile import TemporaryDirectory
        from src.tools.validate_point_reporting import AuditProgress
        with TemporaryDirectory() as folder:
            progress=AuditProgress(Path(folder),self.c)
            with self.assertRaises(Exception):
                progress.run('broken query',lambda: self.c.exec_driver_sql('SELECT * FROM missing_table'))
            status=json.loads((Path(folder)/'audit_status.json').read_text())
            self.assertEqual(status['status'],'failed')
            self.assertEqual(status['steps'][0]['status'],'failed')

    def test_mileage_diagnostic_writes_files_without_changing_data(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from src.tools.diagnose_activity_mileage import run
        self.streams([(0,0,0,41),(1,10,50,41),(2,200,100,41)])
        rebuild_points(self.c)
        self.c.commit()
        before=self.c.exec_driver_sql('SELECT * FROM activity_points ORDER BY point_index').all()
        self.c.commit()
        with TemporaryDirectory() as folder:
            with patch('src.tools.diagnose_activity_mileage.engine',self.engine):
                run([1],Path(folder))
            summary=json.loads((Path(folder)/'summary.json').read_text())[0]
            self.assertEqual(summary['diagnostic_reason_counts']['recording_gap'],1)
            self.assertAlmostEqual(summary['stored_point_miles'],50/1609.344)
            self.assertTrue((Path(folder)/'1_intervals.csv').exists())
        after=self.c.exec_driver_sql('SELECT * FROM activity_points ORDER BY point_index').all()
        self.assertEqual(before,after)

    def test_populated_activity_and_segment_exports_preserve_types(self):
        from tempfile import TemporaryDirectory
        import pyarrow.parquet as pq
        from src.tools.export_power_bi import export_view
        self.streams([(0,0,0,41),(1,10,100,41)])
        self.c.exec_driver_sql("UPDATE activities SET start_date='2026-01-02 13:14:15' WHERE activity_id=1")
        self.c.exec_driver_sql("INSERT INTO segments(segment_id,name,climb_category,created_at,updated_at) VALUES (1,'climb',2,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        rebuild_points(self.c);self.views()
        with TemporaryDirectory() as folder:
            for view in ['view_activity','view_segment']:
                result=export_view(self.c,view,Path(folder))
                self.assertTrue(result.success,result.error)
            activity=pq.read_table(Path(folder)/'view_activity.parquet')
            timestamp=activity['start_date'][0].as_py()
            self.assertEqual((timestamp.hour,timestamp.minute,timestamp.second),(13,14,15))
            self.assertEqual(str(activity.schema.field('start_date').type),'timestamp[us, tz=UTC]')
            self.assertEqual(str(activity.schema.field('activity_date').type),'date32[day]')
            segment=pq.read_table(Path(folder)/'view_segment.parquet')
            self.assertEqual(segment['climb_category'][0].as_py(),2)
            self.assertEqual(str(segment.schema.field('climb_category').type),'int64')

if __name__=='__main__': unittest.main()
