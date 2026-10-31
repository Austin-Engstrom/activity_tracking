import sqlite3
from contextlib import closing
from unittest.mock import patch
import tempfile
import unittest
from pathlib import Path
from src.tools.prepare_migration_database import prepare, snapshot


class MigrationCopyTests(unittest.TestCase):
    def test_preserves_original_and_copies_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = [Path(folder) / name for name in ['source.db', 'working.db']]
            for path, value in [(source, 2), (target, 1)]:
                with closing(sqlite3.connect(path)) as conn, conn:
                    conn.execute('CREATE TABLE activities(id INTEGER)')
                    conn.execute('INSERT INTO activities VALUES (?)', (value,))
            backup = prepare(source, target)
            for path, expected in [(source, 2), (target, 2), (backup, 1)]:
                with closing(sqlite3.connect(path)) as conn, conn:
                    self.assertEqual(conn.execute('SELECT id FROM activities').fetchone()[0], expected)

    def test_same_source_and_target(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'working.db'
            with closing(sqlite3.connect(target)) as conn, conn:
                conn.execute('CREATE TABLE activities(id INTEGER)')
                conn.execute('INSERT INTO activities VALUES (7)')
            backup = prepare(target, target)
            for path in [target, backup]:
                with closing(sqlite3.connect(path)) as conn, conn:
                    self.assertEqual(conn.execute('SELECT id FROM activities').fetchone()[0], 7)

    def test_snapshot_explicitly_closes_connections_on_success_and_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.db'
            with closing(sqlite3.connect(source)) as conn:
                conn.execute('CREATE TABLE example(id INTEGER)')
            real_connect = sqlite3.connect
            connections = []

            def track(*args, **kwargs):
                conn = real_connect(*args, **kwargs)
                connections.append(conn)
                return conn

            with patch('src.tools.prepare_migration_database.sqlite3.connect', side_effect=track):
                snapshot(source, Path(folder) / 'copy.db')
            self.assertEqual(len(connections), 2)
            for conn in connections:
                with self.assertRaises(sqlite3.ProgrammingError):
                    conn.execute('SELECT 1')

            connections.clear()
            with patch('src.tools.prepare_migration_database.sqlite3.connect', side_effect=track):
                with self.assertRaises(sqlite3.OperationalError):
                    snapshot(source, Path(folder) / 'missing' / 'copy.db')
            self.assertEqual(len(connections), 1)
            with self.assertRaises(sqlite3.ProgrammingError):
                connections[0].execute('SELECT 1')
