"""Validate the editable draft's binding, analytical scope and layout structure."""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'power_bi/report'
REPORT=BASE/'Activity Analytics.Report'
MODEL=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition/tables'


class CyclingReportTests(unittest.TestCase):
    def test_project_uses_shared_model_and_has_seven_pages(self):
        project=json.loads((BASE/'Activity Analytics.pbip').read_text())
        self.assertEqual(project['artifacts'][0]['report']['path'],'Activity Analytics.Report')
        binding=json.loads((REPORT/'definition.pbir').read_text())
        self.assertNotIn('byPath',binding['datasetReference'])
        connection=binding['datasetReference']['byConnection']['connectionString']
        self.assertIn('semanticmodelid=',connection.lower())
        self.assertIn('integrated security=ClaimsToken',connection)
        pages=json.loads((REPORT/'definition/pages/pages.json').read_text())
        self.assertEqual(pages['pageOrder'],['activity_overview','cycling_overview','leg_powered','consistency','trails_systems','gear_maintenance','data_definitions'])
        self.assertEqual(pages['activePageName'],'activity_overview')

    def test_all_visual_fields_resolve_and_visuals_fit(self):
        columns={p.stem:set(re.findall(r"\n\tcolumn (?:'([^']+)'|([^\s]+))",p.read_text())) for p in MODEL.glob('*.tmdl')}
        columns={t:{a or b for a,b in names} for t,names in columns.items()}
        measures=set(re.findall(r"\n\tmeasure (?:'([^']+)'|([^\s]+))",(MODEL/'measures_.tmdl').read_text()))
        measures={a or b for a,b in measures}
        def verify(obj):
            if isinstance(obj,dict):
                for kind in ['Column','Measure']:
                    if kind in obj:
                        field=obj[kind]; table=field['Expression']['SourceRef'].get('Entity','dates')
                        self.assertIn(field['Property'],measures if kind=='Measure' else columns[table])
                for v in obj.values():verify(v)
            elif isinstance(obj,list):
                for v in obj:verify(v)
        for page in (REPORT/'definition/pages').glob('*/page.json'):
            size=json.loads(page.read_text());names=set()
            for path in page.parent.glob('visuals/*/visual.json'):
                visual=json.loads(path.read_text());verify(visual);pos=visual['position']
                self.assertNotIn(visual['name'],names);names.add(visual['name'])
                self.assertEqual(visual['name'],path.parent.name)
                self.assertGreater(pos['width'],0);self.assertGreater(pos['height'],0)
                self.assertGreaterEqual(pos['x'],0);self.assertGreaterEqual(pos['y'],0)
                self.assertLessEqual(pos['x']+pos['width'],size['width'])
                self.assertLessEqual(pos['y']+pos['height'],size['height'])

    def test_cycling_filter_is_visible_and_editable(self):
        report=json.loads((REPORT/'definition/report.json').read_text())
        self.assertFalse(report.get('filterConfig',{}).get('filters',[]))
        filters=json.loads((REPORT/'definition/pages/cycling_overview/page.json').read_text())['filterConfig']['filters']
        self.assertEqual(len(filters),1)
        f=next(f for f in filters if f['name']=='cycling_sport_filter');self.assertFalse(f['isLockedInViewMode']);self.assertFalse(f['isHiddenInViewMode'])
        values=f['filter']['Where'][0]['Condition']['In']['Values']
        sports={v[0]['Literal']['Value'] for v in values}
        self.assertTrue({"'Ride'","'MountainBikeRide'","'GravelRide'"} <= sports)
        self.assertNotIn("'Run'",sports)

    def test_only_dates_sync_between_activity_scopes(self):
        for page in ['activity_overview','cycling_overview','leg_powered','consistency','trails_systems','gear_maintenance']:
            v=json.loads((REPORT/f'definition/pages/{page}/visuals/date_filter/visual.json').read_text())
            self.assertTrue(v['visual']['syncGroup']['filterChanges'])
            for name in ['gear_filter','sport_filter']:
                path=REPORT/f'definition/pages/{page}/visuals/{name}/visual.json'
                if path.exists():
                    self.assertNotIn('syncGroup',json.loads(path.read_text())['visual'])
        for page in ['activity_overview','consistency','trails_systems','gear_maintenance','data_definitions']:
            config=json.loads((REPORT/f'definition/pages/{page}/page.json').read_text())
            self.assertFalse(config.get('filterConfig',{}).get('filters',[]))
        config=json.loads((REPORT/'definition/pages/leg_powered/page.json').read_text())
        f=config['filterConfig']['filters'][0]
        self.assertFalse(f['isLockedInViewMode'])
        sports={v[0]['Literal']['Value'] for v in f['filter']['Where'][0]['Condition']['In']['Values']}
        self.assertTrue({"'Run'","'TrailRun'","'Walk'","'Hike'"} <= sports)
        self.assertNotIn("'Ride'",sports)

    def test_visuals_share_uniform_grid_and_outer_edges(self):
        for page in (REPORT/'definition/pages').glob('*/page.json'):
            cards=[]
            for path in page.parent.glob('visuals/*/visual.json'):
                d=json.loads(path.read_text());p=d['position']
                self.assertAlmostEqual((p['x']-24)%118,0,msg=str(path))
                self.assertAlmostEqual((p['width']+24)%118,0,msg=str(path))
                self.assertLessEqual(p['x']+p['width'],1416)
                if d['visual']['visualType']=='card':cards.append(p)
            if cards:
                cards.sort(key=lambda p:p['x'])
                self.assertEqual(len({p['width'] for p in cards}),1)
                self.assertEqual(cards[0]['x'],24)
                self.assertEqual(cards[-1]['x']+cards[-1]['width'],1416)
                for left,right in zip(cards,cards[1:]):
                    self.assertEqual(right['x']-left['x']-left['width'],24)

    def test_current_year_selection_lives_on_synced_date_slicers(self):
        report=json.loads((REPORT/'definition/report.json').read_text())
        self.assertFalse(any(f['name']=='reporting_year_filter' for f in report.get('filterConfig',{}).get('filters',[])))
        for path in (REPORT/'definition/pages').glob('*/visuals/date_filter/visual.json'):
            visual=json.loads(path.read_text())
            self.assertNotIn('filterConfig',visual)
            selection=visual['visual']['objects']['general'][0]['properties']['filter']['filter']
            condition=selection['Where'][0]['Condition']
            self.assertEqual(set(condition),{'Comparison'})
            self.assertEqual(condition['Comparison']['ComparisonKind'],2)
            self.assertEqual(condition['Comparison']['Right']['Literal']['Value'],"datetime'2026-01-01T00:00:00'")
            self.assertTrue(visual['visual']['syncGroup']['filterChanges'])
