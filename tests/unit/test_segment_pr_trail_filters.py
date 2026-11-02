"""Check association-based PR filters reach tables and summary measures together."""
import json
from pathlib import Path
import unittest
from src.tools.build_data_dictionary import metadata_rows

ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/'power_bi/report/Activity Analytics.Report/definition/pages/segment_records'


class SegmentPRTrailTests(unittest.TestCase):
    def test_selectors_use_catalog_fields_and_valid_associations(self):
        for name,table,column in [('trail_filter','trails','trail_name'),('trail_system_filter','trail_systems','trail_system_name')]:
            visual=json.loads((PAGE/f'visuals/{name}/visual.json').read_text())
            f=visual['visual']['query']['queryState']['Values']['projections'][0]['field']['Column']
            self.assertEqual(f['Expression']['SourceRef']['Entity'],table)
            self.assertEqual(f['Property'],column)
            self.assertNotIn('syncGroup',visual['visual'])
            filters=visual['filterConfig']['filters']
            self.assertTrue(any(f['field'].get('Measure',{}).get('Property')=='Segments Associated' for f in filters))
    def test_efforts_bests_and_segment_options_share_membership_filter(self):
        for name in ['effort_history','stored_bests','segment_filter']:
            visual=json.loads((PAGE/f'visuals/{name}/visual.json').read_text())
            filters=visual['filterConfig']['filters']
            gate=next(f for f in filters if f['field'].get('Measure',{}).get('Property')=='Segment Matches Trail Selection')
            condition=gate['filter']['Where'][0]['Condition']['Comparison']
            self.assertEqual(condition['ComparisonKind'],0)
            self.assertEqual(condition['Right']['Literal']['Value'],'1L')
    def test_summary_measures_apply_association_keys_without_relationship_changes(self):
        measures={r[2]:r[7] for r in metadata_rows() if r[0]=='Measure'}
        for name in ['Recorded Segment Efforts','Reported PR Firsts','Reported KOM Firsts','Segments With Stored Best']:
            expr=measures[name]
            self.assertIn('ISCROSSFILTERED(trails[trail_key])',expr)
            self.assertIn('ISCROSSFILTERED(trail_systems[trail_system_key])',expr)
            self.assertIn('VALUES(segment_trail_associations[segment_key])',expr)
            self.assertIn('KEEPFILTERS(TREATAS(AssociatedSegments',expr)
        self.assertIn('REMOVEFILTERS()',measures['Segment Effort Rank All Time'])
        self.assertIn('REMOVEFILTERS(segment_personal_bests)',measures['Seconds Behind Segment PR'])
        matcher=measures['Segment Matches Trail Selection']
        self.assertIn('VALUES(segment_effort_achievements[segment_key])',matcher)
        self.assertIn('VALUES(segment_personal_bests[segment_key])',matcher)
        self.assertIn('NOT TrailSelection || MatchingRows > 0',matcher)

    def test_single_row_slicers_and_hidden_key_projections(self):
        positions=[]
        for name in ['date_filter','category_filter','trail_system_filter','trail_filter','segment_filter']:
            d=json.loads((PAGE/f'visuals/{name}/visual.json').read_text())
            positions.append(d['position'])
        self.assertEqual(len({p['y'] for p in positions}),1)
        self.assertEqual(len({p['width'] for p in positions}),1)
        self.assertEqual(positions[0]['x'],24)
        self.assertAlmostEqual(positions[-1]['x']+positions[-1]['width'],1416)
        for left,right in zip(positions,positions[1:]):
            self.assertAlmostEqual(right['x']-left['x']-left['width'],24)
        for path in PAGE.parent.glob('*/visuals/*/visual.json'):
            d=json.loads(path.read_text())
            if d['visual']['visualType'] not in ['tableEx','pivotTable']:continue
            for role in d['visual'].get('query',{}).get('queryState',{}).values():
                for projection in role.get('projections',[]):
                    name=projection.get('field',{}).get('Column',{}).get('Property','')
                    if name.endswith(('_key','_id')):self.assertTrue(projection.get('hidden'),str(path))
