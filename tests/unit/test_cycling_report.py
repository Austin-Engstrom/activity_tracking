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
    def test_project_uses_shared_model_and_has_eight_pages(self):
        project=json.loads((BASE/'Activity Analytics.pbip').read_text())
        self.assertEqual(project['artifacts'][0]['report']['path'],'Activity Analytics.Report')
        binding=json.loads((REPORT/'definition.pbir').read_text())
        self.assertNotIn('byPath',binding['datasetReference'])
        connection=binding['datasetReference']['byConnection']['connectionString']
        self.assertIn('semanticmodelid=',connection.lower())
        self.assertIn('integrated security=ClaimsToken',connection)
        pages=json.loads((REPORT/'definition/pages/pages.json').read_text())
        self.assertEqual(pages['pageOrder'],['activity_overview','cycling_overview','leg_powered','consistency','trails_systems','gear_maintenance','segment_records','data_definitions'])
        self.assertEqual(pages['activePageName'],'activity_overview')

    def test_all_visual_fields_resolve_and_visuals_fit(self):
        columns={p.stem:set(re.findall(r"\n\tcolumn (?:'([^']+)'|([^\s]+))",p.read_text())) for p in MODEL.glob('*.tmdl')}
        columns={t:{a or b for a,b in names} for t,names in columns.items()}
        measures=set(re.findall(r"\n\tmeasure (?:'([^']+)'|([^\s]+))",(MODEL/'measures_.tmdl').read_text()))
        measures={a or b for a,b in measures}
        def verify(obj,aliases=None):
            aliases=dict(aliases or {})
            if isinstance(obj,dict):
                for source in obj.get('From',[]):
                    if 'Name' in source and 'Entity' in source:aliases[source['Name']]=source['Entity']
                for kind in ['Column','Measure']:
                    if kind in obj:
                        field=obj[kind]; source=field['Expression']['SourceRef']; table=source.get('Entity') or aliases.get(source.get('Source'))
                        self.assertIn(field['Property'],measures if kind=='Measure' else columns[table])
                for v in obj.values():verify(v,aliases)
            elif isinstance(obj,list):
                for v in obj:verify(v,aliases)
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
        f=next(f for f in filters if f['name']=='cycling_sport_filter');self.assertFalse(f.get('isLockedInViewMode',False));self.assertFalse(f.get('isHiddenInViewMode',False))
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
        for page in ['activity_overview','consistency','trails_systems','gear_maintenance','segment_records','data_definitions']:
            config=json.loads((REPORT/f'definition/pages/{page}/page.json').read_text())
            self.assertFalse(config.get('filterConfig',{}).get('filters',[]))
        config=json.loads((REPORT/'definition/pages/leg_powered/page.json').read_text())
        f=config['filterConfig']['filters'][0]
        self.assertFalse(f.get('isLockedInViewMode',False))
        self.assertEqual(f['field']['Column']['Property'],'activity_category')
        condition=f['filter']['Where'][0]['Condition']['In']
        self.assertEqual(condition['Expressions'][0]['Column']['Property'],'activity_category')
        categories={v[0]['Literal']['Value'] for v in condition['Values']}
        self.assertEqual(categories,{"'Walking / Hiking'","'Running'"})

    def test_generated_pr_visuals_share_uniform_grid_and_outer_edges(self):
        for page in (REPORT/'definition/pages').glob('*/page.json'):
            if page.parent.name!='segment_records':
                continue  # Existing page layouts are maintained manually in Desktop.
            cards=[]
            for path in page.parent.glob('visuals/*/visual.json'):
                d=json.loads(path.read_text());p=d['position']
                if d['visual']['visualType']=='slicer':continue  # Compact five-column selector row.
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

    def test_overview_category_and_date_axis_drill_fields(self):
        path=REPORT/'definition/pages/activity_overview/visuals/sport_mix/visual.json'
        d=json.loads(path.read_text())
        self.assertEqual(d['visual']['query']['queryState']['Category']['projections'][0]['field']['Column']['Property'],'activity_category')
        date_chart_count=0
        for path in (REPORT/'definition/pages').glob('*/visuals/*/visual.json'):
            d=json.loads(path.read_text());v=d['visual'];q=v.get('query',{})
            category=q.get('queryState',{}).get('Category',{}).get('projections',[])
            if category and category[0]['field'].get('Column',{}).get('Expression',{}).get('SourceRef',{}).get('Entity')=='dates':
                date_chart_count+=1
                self.assertEqual([p['field']['Column']['Property'] for p in category],['year','month_name','week_start_date','date'])
                self.assertEqual([p['active'] for p in category],[True,True,False,False])
                # Desktop may omit explicit sorts on manually edited charts.
                # Generated PR charts must retain the configured hierarchy order.
                if path.parents[2].name=='segment_records':
                    self.assertEqual(q['sortDefinition']['sort'][0]['direction'],'Descending')
                    self.assertEqual(q['sortDefinition']['sort'][1]['field']['Column']['Property'],'month_name')
                    self.assertEqual(q['sortDefinition']['sort'][1]['direction'],'Ascending')
            if d['name']=='date_filter':
                props=v['objects']['data'][0]['properties']
                if 'start' in props:  # Desktop can retain the selection in general.filter instead.
                    self.assertEqual(props['start']['expr']['Literal']['Value'],"datetime'2026-01-01T00:00:00'")
                self.assertNotIn('end',props)
        self.assertGreater(date_chart_count,0)

    def test_month_names_are_calculated_and_chronologically_sorted(self):
        content=(MODEL/'dates.tmdl').read_text()
        self.assertIn('column month_name = FORMAT(dates[date], "MMMM", "en-US")',content)
        block=content.split('column month_name =',1)[1].split('partition dates',1)[0]
        self.assertIn('sortByColumn: month_number',block)
