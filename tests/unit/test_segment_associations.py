"""Exercise observed associations with multiple trails, repeats and unknown points."""
from pathlib import Path
import json
import unittest
from sqlalchemy import create_engine, text

ROOT=Path(__file__).resolve().parents[2]


class SegmentAssociationTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://')
        self.c=self.engine.connect()
        self.c.exec_driver_sql('''CREATE TABLE activity_points (
            activity_point_key TEXT PRIMARY KEY,activity_id INTEGER,point_index INTEGER,
            trail_key INTEGER,trail_system_key INTEGER,recorded_at_utc TEXT,
            incremental_distance_meters REAL)''')
        self.c.exec_driver_sql('''CREATE TABLE segment_efforts (
            segment_effort_id INTEGER PRIMARY KEY, activity_id INTEGER,segment_id INTEGER,
            start_index INTEGER,end_index INTEGER)''')
        self.c.exec_driver_sql('CREATE TABLE stream_index_alignment(activity_id INTEGER PRIMARY KEY, verified INTEGER)')
        for file in ['view_activity_point_segments','view_segment_trail_association']:
            for sql in (ROOT/'sql/views/points'/f'{file}.sql').read_text().split(';'):
                if sql.strip():self.c.exec_driver_sql(sql)
        self.c.exec_driver_sql('INSERT INTO stream_index_alignment VALUES (1,1)')
        self.c.exec_driver_sql('INSERT INTO segment_efforts VALUES (1,1,100,0,4)')
        points=[(0,10,1,100),(1,10,1,50),(2,11,1,75),(3,None,1,25),(4,None,None,50)]
        for idx,trail,system,distance in points:
            self.c.execute(text('INSERT INTO activity_points VALUES (:key,1,:idx,:trail,:system,:stamp,:distance)'),
                dict(key=f'1:{idx}',idx=idx,trail=trail,system=system,stamp=f'2026-01-01T00:00:{idx:02d}+00:00',distance=distance))

    def tearDown(self):
        self.c.close();self.engine.dispose()

    def rows(self):
        return self.c.exec_driver_sql('SELECT * FROM view_segment_trail_association ORDER BY segment_key,trail_key').mappings().all()

    def test_multiple_trails_and_system_only_match(self):
        rows=self.rows()
        self.assertEqual(len(rows),3)
        by_trail={r['trail_key']:r for r in rows}
        self.assertAlmostEqual(by_trail[10]['observed_distance_miles'],50/1609.344)
        self.assertAlmostEqual(by_trail[11]['observed_distance_miles'],75/1609.344)
        self.assertAlmostEqual(by_trail[None]['observed_distance_miles'],25/1609.344)
        self.assertAlmostEqual(sum(r['observed_distance_share'] for r in rows),.75)
        self.assertEqual(by_trail[10]['point_memberships'],2)
        self.assertEqual(by_trail[10]['supporting_efforts'],1)

    def test_repeated_efforts_keep_counts_and_add_traversal_distance(self):
        self.c.exec_driver_sql('INSERT INTO segment_efforts VALUES (2,1,100,0,4)')
        row=next(r for r in self.rows() if r['trail_key']==10)
        self.assertEqual(row['supporting_efforts'],2)
        self.assertEqual(row['supporting_activities'],1)
        self.assertAlmostEqual(row['observed_distance_miles'],100/1609.344)
        self.assertAlmostEqual(row['observed_distance_share'],.25)

    def test_supporting_activities_are_distinct_across_repeated_rides(self):
        self.c.exec_driver_sql('INSERT INTO stream_index_alignment VALUES (2,1)')
        self.c.exec_driver_sql('INSERT INTO segment_efforts VALUES (2,2,100,0,1)')
        self.c.exec_driver_sql("INSERT INTO activity_points VALUES ('2:0',2,0,10,1,'2026-01-02T00:00:00+00:00',0),('2:1',2,1,10,1,'2026-01-02T00:00:10+00:00',25)")
        row=next(r for r in self.rows() if r['trail_key']==10)
        self.assertEqual(row['supporting_efforts'],2)
        self.assertEqual(row['supporting_activities'],2)
        self.assertAlmostEqual(row['observed_distance_miles'],75/1609.344)
        self.assertEqual(row['last_observed_at'],'2026-01-02T00:00:10+00:00')

    def test_unverified_history_contributes_no_associations(self):
        self.c.exec_driver_sql('UPDATE stream_index_alignment SET verified=0')
        self.assertEqual(self.rows(),[])

    def test_overlapping_segment_starts_do_not_inherit_pre_segment_distance(self):
        self.c.exec_driver_sql('INSERT INTO segment_efforts VALUES (2,1,200,1,2)')
        rows=[r for r in self.rows() if r['segment_key']==200]
        point_only=next(r for r in rows if r['trail_key']==10)
        self.assertIsNone(point_only['observed_distance_miles'])
        self.assertEqual(point_only['evidence_status'],'point_only')
        distance=next(r for r in rows if r['trail_key']==11)
        self.assertAlmostEqual(distance['observed_distance_miles'],75/1609.344)
        self.assertEqual(distance['observed_distance_share'],1)

    def test_no_invented_distance_for_gap_or_single_sample(self):
        self.c.exec_driver_sql('UPDATE activity_points SET incremental_distance_meters=NULL')
        for row in self.rows():
            self.assertIsNone(row['observed_distance_miles'])
            self.assertIsNone(row['observed_distance_share'])
            self.assertEqual(row['evidence_status'],'point_only')

    def test_association_view_is_live_and_install_is_repeatable(self):
        self.c.exec_driver_sql('UPDATE activity_points SET trail_key=11 WHERE trail_key=10')
        rows=self.rows()
        self.assertEqual(len(rows),2)
        sql=(ROOT/'sql/views/points/view_segment_trail_association.sql').read_text()
        for statement in sql.split(';'):
            if statement.strip():self.c.exec_driver_sql(statement)
        self.assertEqual(len(self.rows()),2)

    def test_only_single_direction_dimensions_connect_to_association_bridge(self):
        model=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition'
        import re
        blocks=re.split(r'\n(?=relationship )',(model/'relationships.tmdl').read_text())
        associations=[b for b in blocks if 'segment_trail_associations.' in b]
        self.assertEqual(len(associations),3)
        self.assertTrue(all('crossFilteringBehavior: oneDirection' in b for b in associations))
        self.assertFalse(any('activity_points.' in b for b in associations))
        for table in ['segments','trails','trail_systems']:
            self.assertTrue(any('toColumn: '+table+'.' in b for b in associations))
