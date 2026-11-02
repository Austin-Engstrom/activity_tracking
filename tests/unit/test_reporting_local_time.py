"""Validate geographic fallback, DST intervals, local exports and source preservation."""
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import pyarrow.parquet as pq
from sqlalchemy import create_engine,text
from src.models import Base
from src.services.point_reporting_service import DDL
from src.services.reporting_local_time import refresh_local_times,intervals,gps_timezone
from src.tools.export_power_bi import export_view

ROOT=Path(__file__).resolve().parents[2]


class ReportingLocalTimeTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://');Base.metadata.create_all(self.engine)
        self.c=self.engine.connect()
        for statement in DDL.split(';'):
            if statement.strip():self.c.exec_driver_sql(statement)
        self.c.exec_driver_sql('''INSERT INTO activities(activity_id,athlete_id,name,sport_type,start_date,
            distance_meters,moving_time_seconds,elapsed_time_seconds,total_elevation_gain_meters,trainer,commute,created_at,updated_at)
            VALUES (1,1,'ride','Ride','2026-11-01 05:00:00',100,75,14400,0,0,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)''')
        self.c.exec_driver_sql("INSERT INTO point_reporting_metadata VALUES (1,'America/Chicago')")
        self.c.exec_driver_sql("INSERT INTO segments(segment_id,name,created_at,updated_at) VALUES (10,'s',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        self.c.exec_driver_sql("INSERT INTO segment_efforts(segment_effort_id,activity_id,segment_id,name,elapsed_time_seconds,moving_time_seconds,start_date,created_at,updated_at) VALUES (101,1,10,'s',75,70,'2026-11-01 07:30:00',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
        for i,stamp in enumerate(['2026-11-01 06:30:00','2026-11-01 07:30:00']):
            self.c.execute(text("INSERT INTO activity_streams(activity_id,point_index,time_seconds,distance_meters,latitude,longitude,created_at) VALUES (1,:i,:seconds,0,41,-93,CURRENT_TIMESTAMP)"),{'i':i,'seconds':5400+i*3600})
            self.c.execute(text("INSERT INTO activity_points(activity_point_key,activity_id,point_index,recorded_at_utc,date_key,quality_status,match_method) VALUES (:key,1,:i,:stamp,20261101,'valid','unmatched')"),{'key':'1:'+str(i),'i':i,'stamp':stamp})
        self.c.exec_driver_sql('CREATE TABLE activity_type_categories(activity_type TEXT PRIMARY KEY,activity_category TEXT)')
        for file in ['sql/views/facts/view_activity.sql','sql/views/points/view_activity_points.sql','sql/views/facts/view_segment_effort_achievement.sql','sql/views/facts/view_segment_personal_best.sql']:
            for statement in (ROOT/file).read_text().split(';'):
                if statement.strip():self.c.exec_driver_sql(statement)
    def tearDown(self):self.c.close();self.engine.dispose()
    def test_strava_precedence_and_fall_back_hour(self):
        def forbidden(*args):raise AssertionError('GPS lookup should not run for a valid Strava timezone')
        before=self.c.exec_driver_sql('SELECT * FROM activity_streams').all()
        summary=refresh_local_times(self.c,lookup=forbidden)
        self.assertEqual(summary,{'strava':1})
        rows=self.c.exec_driver_sql('SELECT recorded_at,recorded_at_utc FROM view_activity_points ORDER BY point_index').all()
        self.assertEqual(rows[0][0],rows[1][0])
        self.assertTrue(rows[0][0].endswith('01:30:00'))
        self.assertNotEqual(rows[0][1],rows[1][1])
        self.assertEqual(self.c.exec_driver_sql('SELECT count(*) FROM reporting_timezone_offsets').scalar(),2)
        self.assertEqual(before,self.c.exec_driver_sql('SELECT * FROM activity_streams').all())
        effort=self.c.exec_driver_sql('SELECT effort_started_at,effort_started_at_utc,effort_local_date FROM view_segment_effort_achievement').one()
        self.assertEqual(effort[0],'2026-11-01 01:30:00')
        self.assertEqual(effort[1],'2026-11-01 07:30:00')
        self.assertEqual(effort[2],'2026-11-01')
    def test_first_valid_coordinate_fallback_and_source_promotion(self):
        self.c.exec_driver_sql("UPDATE point_reporting_metadata SET timezone_name='Invalid/Zone'")
        self.c.exec_driver_sql('UPDATE activity_streams SET latitude=NULL WHERE point_index=0')
        seen=[]
        def lookup(lat,lon):seen.append((lat,lon));return 'America/Los_Angeles'
        refresh_local_times(self.c,lookup=lookup)
        self.assertEqual(seen,[(41.0,-93.0)])
        row=self.c.exec_driver_sql('SELECT timezone_name,timezone_source FROM reporting_activity_timezones').one()
        self.assertEqual(tuple(row),('America/Los_Angeles','first_gps'))
        self.assertEqual(self.c.exec_driver_sql('SELECT min(date_key) FROM activity_points').scalar(),20261031)
        self.c.exec_driver_sql("UPDATE point_reporting_metadata SET timezone_name='America/Chicago'")
        refresh_local_times(self.c,lookup=lambda *_:self.fail('must prefer source'))
        self.assertEqual(self.c.exec_driver_sql('SELECT timezone_source FROM reporting_activity_timezones').scalar(),'strava')
        self.assertEqual(self.c.exec_driver_sql('SELECT min(date_key) FROM activity_points').scalar(),20261101)
    def test_unresolved_local_fields_are_null_not_utc(self):
        self.c.exec_driver_sql('DELETE FROM point_reporting_metadata')
        refresh_local_times(self.c,lookup=lambda *_:None)
        self.assertEqual(self.c.exec_driver_sql('SELECT timezone_source FROM reporting_activity_timezones').scalar(),'unresolved')
        self.assertIsNone(self.c.exec_driver_sql('SELECT recorded_at FROM view_activity_points LIMIT 1').scalar())
        self.assertIsNone(self.c.exec_driver_sql('SELECT date_key FROM activity_points LIMIT 1').scalar())
        self.assertIsNone(self.c.exec_driver_sql('SELECT activity_date FROM view_activity').scalar())
        self.assertIsNone(self.c.exec_driver_sql('SELECT effort_local_date FROM view_segment_effort_achievement').scalar())
        self.assertIsNotNone(self.c.exec_driver_sql('SELECT start_date_utc FROM view_activity').scalar())
    def test_spring_forward_and_half_hour_transition(self):
        rows=intervals(datetime(2026,3,8,7,tzinfo=timezone.utc),datetime(2026,3,8,10,tzinfo=timezone.utc),'America/Chicago')
        self.assertEqual([r[2] for r in rows],[-21600,-18000])
        self.assertEqual(rows[0][1],datetime(2026,3,8,8,tzinfo=timezone.utc))
        rows=intervals(datetime(2026,4,4,14,tzinfo=timezone.utc),datetime(2026,4,4,17,tzinfo=timezone.utc),'Australia/Lord_Howe')
        self.assertEqual([r[2] for r in rows],[39600,37800])
    def test_local_export_is_naive_and_durations_stay_exact_seconds(self):
        refresh_local_times(self.c)
        with TemporaryDirectory() as directory:
            result=export_view(self.c,'view_activity',Path(directory));self.assertTrue(result.success,result.error)
            data=pq.read_table(Path(directory)/'view_activity.parquet')
            self.assertEqual(data['moving_time_seconds'][0].as_py(),75)
            self.assertEqual(str(data.schema.field('start_date').type),'timestamp[us]')
            self.assertEqual(str(data.schema.field('start_date_utc').type),'timestamp[us, tz=UTC]')
            self.assertEqual(data['activity_date'][0].as_py().isoformat(),'2026-11-01')
    def test_offline_known_coordinate(self):
        self.assertEqual(gps_timezone(41,-93),'America/Chicago')
