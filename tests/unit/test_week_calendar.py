"""Verify real calendar boundaries and incremental calendar-only exports."""
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import pyarrow.parquet as pq
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.tools.export_power_bi import run

ROOT=Path(__file__).resolve().parents[2]


class WeekCalendarTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://')
        with self.engine.begin() as conn:
            conn.exec_driver_sql('CREATE TABLE activity_points(date_key INTEGER)')
            sql=(ROOT/'sql/views/dimensions/view_date.sql').read_text()
            for statement in sql.split(';'):
                if statement.strip():conn.exec_driver_sql(statement)

    def tearDown(self):
        self.engine.dispose()

    def test_monday_weeks_cross_year_without_reset(self):
        with self.engine.begin() as conn:
            conn.exec_driver_sql('INSERT INTO activity_points VALUES (20201227),(20210111)')
            rows={r[0]:(r[1],r[2]) for r in conn.exec_driver_sql('SELECT date,week_start_date,week_end_date FROM view_date')}
            self.assertEqual(rows['2020-12-27'],('2020-12-21','2020-12-27'))
            self.assertEqual(rows['2020-12-31'],('2020-12-28','2021-01-03'))
            self.assertEqual(rows['2021-01-01'],rows['2020-12-31'])
            self.assertEqual(rows['2021-01-04'],('2021-01-04','2021-01-10'))
            self.assertEqual(rows['2021-01-11'],('2021-01-11','2021-01-17'))
            for stamp,(start,end) in rows.items():
                self.assertEqual(date.fromisoformat(start).weekday(),0)
                self.assertEqual(date.fromisoformat(end)-date.fromisoformat(start),timedelta(days=6))
                self.assertTrue(start<=stamp<=end)

    def test_calendar_only_export_keeps_other_files_and_date_types(self):
        with self.engine.begin() as conn:
            conn.exec_driver_sql('INSERT INTO activity_points VALUES (20200229)')
        with TemporaryDirectory() as folder:
            out=Path(folder)
            sentinel=out/'view_activity_points.parquet';sentinel.write_bytes(b'unchanged')
            with patch('src.tools.export_power_bi.EXPORT_DIRECTORY',out), patch('src.tools.export_power_bi.SessionLocal',lambda:Session(self.engine)):
                result=run(views=['view_date'])
            self.assertEqual([r.view_name for r in result],['view_date'])
            self.assertTrue(result[0].success)
            self.assertEqual(sentinel.read_bytes(),b'unchanged')
            table=pq.read_table(out/'view_date.parquet')
            self.assertEqual(str(table.schema.field('week_start_date').type),'date32[day]')
            self.assertEqual(table['week_start_date'][0].as_py(),date(2020,2,24))
            self.assertEqual(table['week_end_date'][0].as_py(),date(2020,3,1))

    def test_empty_calendar_and_invalid_export_selection(self):
        with self.engine.connect() as conn:
            self.assertEqual(conn.exec_driver_sql('SELECT count(*) FROM view_date').scalar(),0)
        with TemporaryDirectory() as folder,patch('src.tools.export_power_bi.EXPORT_DIRECTORY',Path(folder)):
            with self.assertRaises(ValueError):run(views=['unknown_view'])
