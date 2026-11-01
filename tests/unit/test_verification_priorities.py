import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from sqlalchemy import create_engine
from src.tools.validate_point_reporting import select_verification_activities


class VerificationPriorityTests(unittest.TestCase):
    def test_csv_order_skips_verified_and_resumes_after_failed_attempts(self):
        engine=create_engine('sqlite://')
        try:
            with engine.connect() as conn, TemporaryDirectory() as folder:
                for sql in ['CREATE TABLE activities(activity_id INTEGER PRIMARY KEY)',
                            'CREATE TABLE activity_points(activity_id INTEGER)',
                            'CREATE TABLE segment_efforts(activity_id INTEGER)',
                            'CREATE TABLE stream_index_alignment(activity_id INTEGER PRIMARY KEY,verified INTEGER)',
                            'CREATE TABLE stream_alignment_checks(activity_id INTEGER PRIMARY KEY,checked_at TEXT,reason TEXT)']:
                    conn.exec_driver_sql(sql)
                for table in ['activities','activity_points','segment_efforts']:
                    conn.exec_driver_sql(f'INSERT INTO {table} VALUES (1),(2),(3),(4)')
                conn.exec_driver_sql('INSERT INTO stream_index_alignment VALUES (1,1)')
                conn.exec_driver_sql("INSERT INTO stream_alignment_checks VALUES (3,'2026-10-31','coordinates_changed')")
                path=Path(folder)/'candidates.csv'
                path.write_text('activity_id\n3\n1\n2\n2\n999\n4\n')
                self.assertEqual(select_verification_activities(conn,2,path),[2,4])
                conn.exec_driver_sql('INSERT INTO stream_index_alignment VALUES (2,1),(4,1)')
                self.assertEqual(select_verification_activities(conn,2,path),[3])
                self.assertEqual(select_verification_activities(conn,2),[3])
        finally:
            engine.dispose()

    def test_bad_csv_has_clear_error(self):
        engine=create_engine('sqlite://')
        try:
            with engine.connect() as conn, TemporaryDirectory() as folder:
                for sql in ['CREATE TABLE activities(activity_id INTEGER)',
                            'CREATE TABLE activity_points(activity_id INTEGER)',
                            'CREATE TABLE segment_efforts(activity_id INTEGER)',
                            'CREATE TABLE stream_index_alignment(activity_id INTEGER,verified INTEGER)',
                            'CREATE TABLE stream_alignment_checks(activity_id INTEGER,checked_at TEXT)']:
                    conn.exec_driver_sql(sql)
                path=Path(folder)/'bad.csv';path.write_text('other\n1\n')
                with self.assertRaisesRegex(ValueError,'activity_id'):
                    select_verification_activities(conn,5,path)
        finally:
            engine.dispose()
