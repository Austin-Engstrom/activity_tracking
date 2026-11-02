"""Check renamed fields, lineage continuity and unit/format separation."""
from pathlib import Path
import json,re
import unittest
from src.tools.build_data_dictionary import metadata_rows

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition'


class FieldAliasTests(unittest.TestCase):
    def test_aliases_are_unique_and_have_declared_numeric_units(self):
        aliases=json.loads((ROOT/'src/reporting/gps_model_columns.json').read_text())
        rows=metadata_rows();columns={(r[1],r[2]):r for r in rows if r[0]=='Column'}
        for table,names in aliases.items():
            self.assertEqual(len(names.values()),len(set(names.values())))
            for old,new in names.items():self.assertIn((table,new),columns)
        for name in ['pr_time','pr_moving_time']:
            self.assertEqual(columns['segment_personal_bests',name][5],'int64')
        self.assertIn(('segment_personal_bests','pr_date'),columns)
        self.assertEqual(columns['component_service_status','hours_since_service'][5],'double')
        self.assertIn(('component_service_status','service_interval_type'),columns)
        self.assertIn(('activity_points','recorded_at_utc'),columns)
        self.assertIn(('activity_points','recorded_at'),columns)
    def test_duration_displays_keep_numeric_columns_for_calculation(self):
        rows=metadata_rows();measures={row[2]:row for row in rows if row[0]=='Measure'}
        for name in ['Segment Effort Time','Segment PR Time','Activity Moving Time','Activity Elapsed Time','Point Moving Time']:
            expression=measures[name][7]
            self.assertIn('QUOTIENT(RoundedSeconds, 3600)',expression)
            self.assertIn('IF(HoursPart > 0',expression)
        self.assertIn('SUM(activities[moving_time]),3600',measures['Moving Time'][7])
        self.assertIn('segment_effort_achievements[time]',measures['Seconds Behind Segment PR'][7])
        self.assertIn('segment_personal_bests[pr_time]',measures['Seconds Behind Segment PR'][7])

    def test_dax_and_relationship_references_resolve_after_renames(self):
        columns={p.stem:{a or b for a,b in re.findall(r"\n\tcolumn (?:'([^']+)'|([^\s=]+))",p.read_text())} for p in (MODEL/'tables').glob('*.tmdl')}
        measures={row[2] for row in metadata_rows() if row[0]=='Measure'}
        for path in (MODEL/'tables').glob('*.tmdl'):
            content=path.read_text().split('\n\tpartition ',1)[0]
            for table,name in re.findall(r"'?([A-Za-z_]\w*)'?\[([^\]]+)\]",content):
                if table not in columns:continue
                self.assertIn(name,measures if table=='measures_' else columns[table],(path.name,table,name))
        for table,name in re.findall(r'(?:fromColumn|toColumn): (\w+)\.(\w+)',(MODEL/'relationships.tmdl').read_text()):
            self.assertIn(name,columns[table])
