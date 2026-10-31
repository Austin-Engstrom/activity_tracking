"""Back up the configured SQLite database and prepare a working copy.

Stop ETL jobs and close database connections before running this command.
Run locally to work with your local data; cloud files are separate.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'database' / 'strava_analytics.db'


def snapshot(source: Path, destination: Path) -> None:
    """Use SQLite backup so committed WAL contents are included."""
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(destination)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError(f'Integrity check failed: {destination}')


def prepare(source: Path, target: Path = TARGET) -> Path:
    source, target = source.resolve(), target.resolve()
    if not source.is_file():
        raise FileNotFoundError(f'Source database does not exist: {source}')
    # Never replace a destination with active/recoverable SQLite sidecars.
    for suffix in ['-wal', '-shm', '-journal']:
        if Path(str(target) + suffix).exists():
            raise RuntimeError('Close database connections and checkpoint the destination before preparing it.')
    target.parent.mkdir(parents=True, exist_ok=True)
    backups = target.parent / 'backups'
    backups.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = backups / f'strava_analytics_before_migration_{stamp}.db'
    snapshot(target if target.exists() else source, backup)
    fd, name = tempfile.mkstemp(prefix='migration_', suffix='.db', dir=target.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        snapshot(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'Backup: {backup}')
    print(f'Working database: {target}')
    with closing(sqlite3.connect(target.as_uri() + '?mode=ro', uri=True)) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ['activities', 'activity_streams']:
            count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] if table in tables else 0
            print(f'{table}: {count} rows')
    return backup


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=TARGET,
                        help='Existing populated SQLite database; defaults to the configured database')
    args = parser.parse_args()
    prepare(args.source)
