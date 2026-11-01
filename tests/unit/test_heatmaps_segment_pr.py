"""Check weighted GPS heatmap bindings and partial-coverage PR reporting contracts."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition'
PAGES=ROOT/'power_bi/report/Activity Analytics.Report/definition/pages'


class HeatmapAndPRTests(unittest.TestCase):
    def test_maps_group_cells_and_weight_by_point_count(self):
        maps=[]
        for p in PAGES.glob('*/visuals/*/visual.json'):
            d=json.loads(p.read_text());v=d['visual']
            self.assertNotEqual(v['visualType'],'shapeMap')
            if v['visualType']!='azureMap':continue
            maps.append(p)
            q=v['query']['queryState']
            self.assertEqual(q['Y']['projections'][0]['field']['Column']['Property'],'map_latitude')
            self.assertEqual(q['X']['projections'][0]['field']['Column']['Property'],'map_longitude')
            self.assertEqual(q['Size']['projections'][0]['field']['Measure']['Property'],'GPS Points')
            self.assertNotIn('Category',q)  # No point-ID grouping that explodes map cardinality.
            self.assertNotIn('Series',q)
            heat=v['objects']['heatMapLayer'][0]['properties']
            self.assertEqual(heat['show']['expr']['Literal']['Value'],'true')
            self.assertEqual(heat['heatMapUseSize']['expr']['Literal']['Value'],'true')
            self.assertEqual(v['objects']['bubbleLayer'][0]['properties']['show']['expr']['Literal']['Value'],'false')
        self.assertEqual(len(maps),4)
        content=(MODEL/'tables/activity_points.tmdl').read_text()
        for coordinate in ['latitude','longitude']:
            block=content.split(f'column map_{coordinate} =',1)[1].split('\n\t',1)[0]
            self.assertIn('ROUND(activity_points['+coordinate+'], 3)',block)
            self.assertIn('BLANK()',block)

    def test_partial_observation_and_lifetime_scopes_are_explicit(self):
        content=(MODEL/'tables/measures_.tmdl').read_text()
        self.assertIn('pr_rank_status] IN {"ranked", "no_rank"}',content)
        self.assertIn('kom_rank_status] IN {"ranked", "no_rank"}',content)
        self.assertIn('DIVIDE([Rank Observed Efforts], [Recorded Segment Efforts])',content)
        self.assertIn('[Recorded Segment Efforts] - [Rank Observed Efforts]',content)
        page=json.loads((PAGES/'segment_records/page.json').read_text())
        self.assertEqual(page['displayName'],'Segment PRs')
        self.assertFalse(page.get('filterConfig',{}).get('filters',[]))
        self.assertEqual({i['source'] for i in page['visualInteractions'] if i['target']=='stored_bests' and i['type']=='NoFilter'}, {'effort_history','achievement_trend'})
        relationships=(MODEL/'relationships.tmdl').read_text()
        self.assertEqual(relationships.count('fromColumn: segment_personal_bests.'),1)
        self.assertIn('fromColumn: segment_personal_bests.segment_key',relationships)
        for name in ['effort_history','stored_bests']:
            d=json.loads((PAGES/f'segment_records/visuals/{name}/visual.json').read_text())
            q=d['visual']['query'];self.assertEqual(q['sortDefinition']['sort'][0]['direction'],'Descending')
            fields=[p['field']['Column']['Property'] for p in q['queryState']['Values']['projections']]
            if name=='effort_history':
                self.assertIn('segment_effort_key',fields)
                self.assertIn('pr_rank_status',fields)
                self.assertIn('kom_rank_status',fields)
                self.assertIn('ranks_retrieved_at',fields)
            else:self.assertIn('tied_best_effort_count',fields)
