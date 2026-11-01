"""Maintenance baselines, unit selection, and CSV date handling."""
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import create_engine
from src.tools.import_maintenance import create_tables, import_gear_components, import_component_services, normalize_date
from src.tools.export_power_bi import export_view

ROOT = Path(__file__).resolve().parents[2]

class MaintenanceTests(unittest.TestCase):
    def test_csv_import_and_service_reset(self):
        with TemporaryDirectory() as folder:
            db = Path(folder)/'test.db'
            with sqlite3.connect(db) as conn:
                conn.row_factory = sqlite3.Row
                conn.executescript('''create table gear(gear_id text primary key, name text);
                insert into gear values ('b17417153','Bike 1'),('b18838408','Bike 2');
                create table activities(gear_id text,start_date text,moving_time_seconds real,distance_meters real);
                insert into activities values
                ('b17417153','2026-02-01',360000,1609344),
                ('b17417153','2026-08-01',36000,160934.4),
                ('b17417153','2026-08-21',90000,321868.8),
                ('b18838408','2026-10-18',216000,1931212.8);''')
                create_tables(conn)
                for _ in range(2):
                    result=import_gear_components(conn,ROOT/'data/maintenance/gear_components.csv')
                    self.assertEqual(result.skipped,0)
                    import_component_services(conn,ROOT/'data/maintenance/component_services.csv')
                self.assertEqual(conn.execute('select count(*) from gear_components').fetchone()[0],6)
                self.assertEqual(conn.execute('select count(*) from component_services').fetchone()[0],3)
                conn.executescript((ROOT/'sql/views/facts/view_component_service_status.sql').read_text())
                rows={row['component_id']:row for row in conn.execute('select * from view_component_service_status')}
                self.assertEqual(rows[1]['hours_since_service'],25)
                self.assertEqual(rows[1]['lifetime_component_hours'],35)
                self.assertEqual(rows[1]['service_interval_remaining_percent'],.5)
                self.assertEqual(rows[1]['service_interval_remaining'],25)
                self.assertEqual(rows[2]['service_interval_remaining'],700)
                self.assertEqual(rows[4]['service_interval_remaining_percent'],0)
                self.assertEqual(rows[4]['usage_overdue'],10)
                self.assertEqual(rows[5]['service_status'],'Due')
                conn.execute("update gear_components set removed_at='2026-08-20' where component_id=1")
                row=conn.execute('select * from view_component_service_status where component_id=1').fetchone()
                self.assertEqual(row['hours_since_service'],0)
                self.assertEqual(row['service_status'],'Inactive')
                conn.commit()
            engine=create_engine(f'sqlite:///{db}')
            try:
                with engine.connect() as conn:
                    result=export_view(conn,'view_component_service_status',Path(folder))
                    self.assertTrue(result.success,result.error)
                    self.assertEqual(result.row_count,6)
            finally:
                engine.dispose()

    def test_dates(self):
        self.assertEqual(normalize_date('2/9/2026'),'2026-02-09')
        self.assertEqual(normalize_date('2026-02-09'),'2026-02-09')
        self.assertIsNone(normalize_date(''))
        with self.assertRaises(ValueError):
            normalize_date('2/30/2026')
