"""Exercise rank observation, resumable refresh and stored-best semantics offline."""
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sqlalchemy import create_engine, event, text, select
from sqlalchemy.orm import sessionmaker

from src.api.client import StravaRateLimitError
from src.etl.segment_mapper import SegmentMappingError
from src.models import Base, Activity, SegmentEffort
from src.models.segment_record_metadata import SegmentEffortRecordMetadata, SegmentRecordRefresh
from src.services.segment_record_service import load_activity_segments
from src.services.point_reporting_service import DDL
from src.tools.backfill_segment_records import run_batch, select_candidates
from src.tools.export_power_bi import export_view

ROOT=Path(__file__).resolve().parents[2]


def effort(key=101, seconds=60, segment=10, **kwargs):
    data=dict(id=key,name='segment',segment={'id':segment,'name':'segment'},
              elapsed_time=seconds,moving_time=seconds,start_date='2026-01-02T12:00:00Z',
              start_date_local='2026-01-02T06:00:00Z',distance=500,
              start_index=0,end_index=2,pr_rank=None,kom_rank=None)
    data.update(kwargs)
    return data


class FakeClient:
    def __init__(self, responses, capacity=True):
        self.responses=responses;self.capacity=capacity;self.calls=[]
    def has_read_capacity(self):return self.capacity
    def get_activity(self, activity_id, include_all_efforts=False):
        self.calls.append((activity_id,include_all_efforts))
        payload=self.responses[activity_id]
        if isinstance(payload,Exception):raise payload
        return payload


class SegmentRecordTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://')
        @event.listens_for(self.engine,'connect')
        def enforce_foreign_keys(connection,record):connection.execute('PRAGMA foreign_keys=ON')
        Base.metadata.create_all(self.engine)
        self.sessions=sessionmaker(self.engine,autoflush=False,expire_on_commit=False)
        with self.engine.begin() as conn:
            for sql in DDL.split(';'):
                if sql.strip():conn.exec_driver_sql(sql)
            for key in [1,2,3]:
                conn.execute(text("""INSERT INTO activities(activity_id,athlete_id,name,sport_type,start_date,
                    distance_meters,moving_time_seconds,elapsed_time_seconds,total_elevation_gain_meters,
                    trainer,commute,created_at,updated_at) VALUES (:id,1,'activity','Ride','2026-01-02',
                    500,60,60,0,0,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"""),{'id':key})
            for key in [1,2]:
                conn.execute(text("INSERT INTO activity_points(activity_point_key,activity_id,point_index,date_key,quality_status,match_method) VALUES (:key,:id,0,20260102,'first_point','unmatched')"),{'key':str(key)+':0','id':key})
            for view in ['view_segment_effort_achievement','view_segment_personal_best']:
                for statement in (ROOT/'sql/views/facts'/f'{view}.sql').read_text().split(';'):
                    if statement.strip():conn.exec_driver_sql(statement)
    def tearDown(self):self.engine.dispose()
    def load(self,activity_id,efforts,stamp=datetime(2026,11,1)):
        with self.sessions() as session:
            result=load_activity_segments(session,session.get(Activity,activity_id),{'id':activity_id,'segment_efforts':efforts},stamp)
            session.commit();return result
    def rows(self,view):
        with self.engine.connect() as conn:return conn.exec_driver_sql('SELECT * FROM '+view+' ORDER BY segment_key').mappings().all()

    def test_rank_values_and_retrieval_provenance(self):
        self.load(1,[effort(pr_rank=1,kom_rank=2)])
        row=self.rows('view_segment_effort_achievement')[0]
        self.assertEqual((row['reported_pr_rank'],row['reported_kom_rank']),(1,2))
        self.assertEqual((row['reported_pr_first'],row['reported_kom_first']),(1,0))
        self.assertEqual(row['pr_rank_status'],'ranked')
        self.assertTrue(row['ranks_retrieved_at'].startswith('2026-11-01'))
        self.assertEqual(row['date_key'],20260102)
        self.assertEqual(row['activity_url'],'https://www.strava.com/activities/1')

    def test_omitted_fields_differ_from_explicit_nulls(self):
        raw=effort();raw.pop('kom_rank')
        self.load(1,[raw]);row=self.rows('view_segment_effort_achievement')[0]
        self.assertEqual(row['pr_rank_status'],'no_rank');self.assertEqual(row['reported_pr_first'],0)
        self.assertEqual(row['kom_rank_status'],'not_returned');self.assertIsNone(row['reported_kom_first'])

    def test_reimport_updates_snapshot_and_removes_only_stale_metadata(self):
        self.load(1,[effort(101,pr_rank=1),effort(102)])
        self.load(1,[effort(101,pr_rank=2)],datetime(2026,11,2))
        rows=self.rows('view_segment_effort_achievement');self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['reported_pr_rank'],2)
        self.assertTrue(rows[0]['ranks_retrieved_at'].startswith('2026-11-02'))
        with self.sessions() as session:
            self.assertIsNone(session.get(SegmentEffortRecordMetadata,102))

    def test_missing_or_invalid_payload_preserves_prior_efforts(self):
        self.load(1,[effort()])
        for payload in [{'id':1},{'id':1,'segment_efforts':None},{'id':2,'segment_efforts':[]},
                        {'id':1,'segment_efforts':[effort(kom_rank=-1)]},
                        {'id':1,'segment_efforts':[effort(),effort()]}]:
            with self.subTest(payload=payload),self.sessions() as session:
                with self.assertRaises(SegmentMappingError):load_activity_segments(session,session.get(Activity,1),payload)
                session.rollback()
            self.assertEqual(len(self.rows('view_segment_effort_achievement')),1)

    def test_explicit_empty_array_is_completed_and_clears_removed_efforts(self):
        self.load(1,[effort()]);self.load(1,[])
        self.assertEqual(self.rows('view_segment_effort_achievement'),[])
        with self.sessions() as session:self.assertEqual(session.get(SegmentRecordRefresh,1).status,'completed')

    def test_best_elapsed_ties_hidden_nonpositive_and_non_gps(self):
        self.load(1,[effort(102,60),effort(101,60),effort(103,0),effort(104,10,hidden=True)])
        self.load(2,[effort(201,90)])
        self.load(3,[effort(301,1)])  # no GPS points: excluded from both reporting views
        row=self.rows('view_segment_personal_best')[0]
        self.assertEqual(row['best_segment_effort_key'],101)
        self.assertEqual(row['best_elapsed_time_seconds'],60)
        self.assertEqual(row['stored_effort_count'],5)
        self.assertEqual(row['eligible_effort_count'],3)
        self.assertEqual(row['tied_best_effort_count'],2)
        self.assertEqual(row['best_activity_key'],1)

    def test_best_without_eligible_time_has_no_summary_row(self):
        self.load(1,[effort(101,0),effort(102,5,hidden=True)])
        self.assertEqual(self.rows('view_segment_personal_best'),[])

    def test_legacy_ranks_not_backdated(self):
        self.load(1,[effort(pr_rank=1)])
        with self.engine.begin() as conn:conn.exec_driver_sql('DELETE FROM segment_effort_record_metadata')
        row=self.rows('view_segment_effort_achievement')[0]
        self.assertEqual(row['reported_pr_rank'],1)
        self.assertEqual(row['pr_rank_status'],'legacy_unobserved')
        self.assertIsNone(row['ranks_retrieved_at']);self.assertIsNone(row['reported_pr_first'])

    def test_backfill_resumes_and_respects_rate_limit(self):
        self.load(1,[effort(101)]);self.load(2,[effort(201)])
        with self.engine.begin() as conn:conn.exec_driver_sql('DELETE FROM segment_record_refresh')
        client=FakeClient({2:{'id':2,'segment_efforts':[effort(201,pr_rank=1)]},1:StravaRateLimitError('limit')})
        result=run_batch(self.sessions,client,2)
        self.assertEqual((result.refreshed,result.deferred,result.rate_limit_reached),(1,1,True))
        self.assertTrue(all(all_efforts for _,all_efforts in client.calls))
        with self.sessions() as session:self.assertEqual(select_candidates(session,25),[1])

    def test_failed_batch_preserves_data_and_does_not_starve_untouched(self):
        self.load(1,[effort(101)]);self.load(2,[effort(201)])
        with self.engine.begin() as conn:conn.exec_driver_sql('DELETE FROM segment_record_refresh')
        client=FakeClient({2:{'id':2}})
        result=run_batch(self.sessions,client,1);self.assertEqual(result.failed,1)
        self.assertEqual(len(self.rows('view_segment_effort_achievement')),2)
        with self.sessions() as session:self.assertEqual(select_candidates(session,1),[1])

    def test_cutoff_and_explicit_activity_refresh(self):
        self.load(1,[effort()])
        with self.sessions() as session:
            self.assertEqual(select_candidates(session,25),[])
            self.assertEqual(select_candidates(session,25,datetime(2026,11,2)),[1])
            self.assertEqual(select_candidates(session,25,activity_ids=[1]),[1])
        result=run_batch(self.sessions,FakeClient({},capacity=False),25,activity_ids=[1])
        self.assertTrue(result.rate_limit_reached);self.assertEqual(result.deferred,1)

    def test_populated_views_export_with_explicit_contract(self):
        self.load(1,[effort(pr_rank=1)])
        with self.engine.connect() as conn, TemporaryDirectory() as directory:
            for view in ['view_segment_effort_achievement','view_segment_personal_best']:
                result=export_view(conn,view,Path(directory))
                self.assertTrue(result.success,result.error);self.assertEqual(result.row_count,1)

    def test_normal_detail_etl_records_provenance(self):
        from src.repositories.activity_repository import ActivityRepository
        from src.repositories.segment_repository import SegmentRepository
        from src.services.activity_detail_service import ActivityDetailService
        with self.engine.begin() as conn:
            conn.exec_driver_sql("UPDATE activities SET detail_loaded_at=CURRENT_TIMESTAMP, segments_loaded_at=CURRENT_TIMESTAMP")
            conn.exec_driver_sql("UPDATE activities SET segments_loaded_at=NULL WHERE activity_id=1")
        with self.sessions() as session:
            client=FakeClient({1:{'id':1,'segment_efforts':[effort(pr_rank=1,kom_rank=1)]}})
            result=ActivityDetailService(client,ActivityRepository(session),SegmentRepository(session)).run_batch(1)
            self.assertEqual(result.segment_activities_loaded,1)
            self.assertEqual(result.failed,0)
            self.assertEqual(client.calls,[(1,True)])
        row=self.rows('view_segment_effort_achievement')[0]
        self.assertEqual(row['reported_kom_first'],1)
        self.assertIsNotNone(row['ranks_retrieved_at'])

    def test_additive_migration_is_idempotent_and_preserves_source(self):
        import importlib
        from unittest.mock import patch
        from alembic.migration import MigrationContext
        from alembic.operations import Operations
        from sqlalchemy import inspect
        migration=importlib.import_module('migrations.versions.20261101_segment_records')
        self.load(1,[effort(pr_rank=1)])
        with self.engine.begin() as conn:
            conn.exec_driver_sql('DROP TABLE segment_effort_record_metadata')
            conn.exec_driver_sql('DROP TABLE segment_record_refresh')
            with patch.object(migration,'op',Operations(MigrationContext.configure(conn))):
                migration.upgrade()
                migration.upgrade()
            self.assertTrue(inspect(conn).has_table('segment_effort_record_metadata'))
            self.assertEqual(conn.exec_driver_sql('SELECT pr_rank FROM segment_efforts WHERE segment_effort_id=101').scalar(),1)
            self.assertEqual(conn.exec_driver_sql('SELECT count(*) FROM segment_effort_record_metadata').scalar(),0)
