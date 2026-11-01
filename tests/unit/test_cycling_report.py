"""Validate the editable draft's binding, analytical scope and layout structure."""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'power_bi/report'
REPORT=BASE/'draft.Report'
MODEL=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition/tables'


class CyclingReportTests(unittest.TestCase):
    def test_project_uses_shared_model_and_has_five_pages(self):
        project=json.loads((BASE/'draft.pbip').read_text())
        self.assertEqual(project['artifacts'][0]['report']['path'],'draft.Report')
        binding=json.loads((REPORT/'definition.pbir').read_text())
        self.assertNotIn('byPath',binding['datasetReference'])
        connection=binding['datasetReference']['byConnection']['connectionString']
        self.assertIn('semanticmodelid=',connection.lower())
        self.assertIn('integrated security=ClaimsToken',connection)
        pages=json.loads((REPORT/'definition/pages/pages.json').read_text())
        self.assertEqual(pages['pageOrder'],['cycling_overview','consistency','trails_systems','gear_maintenance','data_definitions'])
        self.assertEqual(pages['activePageName'],'cycling_overview')

    def test_all_visual_fields_resolve_and_visuals_fit(self):
        columns={p.stem:set(re.findall(r"\n\tcolumn (?:'([^']+)'|([^\s]+))",p.read_text())) for p in MODEL.glob('*.tmdl')}
        columns={t:{a or b for a,b in names} for t,names in columns.items()}
        measures=set(re.findall(r"\n\tmeasure (?:'([^']+)'|([^\s]+))",(MODEL/'measures_.tmdl').read_text()))
        measures={a or b for a,b in measures}
        def verify(obj):
            if isinstance(obj,dict):
                for kind in ['Column','Measure']:
                    if kind in obj:
                        field=obj[kind]; table=field['Expression']['SourceRef']['Entity']
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
        filters=json.loads((REPORT/'definition/report.json').read_text())['filterConfig']['filters']
        self.assertEqual(len(filters),1)
        f=filters[0];self.assertFalse(f['isLockedInViewMode']);self.assertFalse(f['isHiddenInViewMode'])
        values=f['filter']['Where'][0]['Condition']['In']['Values']
        sports={v[0]['Literal']['Value'] for v in values}
        self.assertTrue({"'Ride'","'MountainBikeRide'","'GravelRide'"} <= sports)
        self.assertNotIn("'Run'",sports)

    def test_analysis_slicers_sync_and_dictionary_is_independent(self):
        for page in ['cycling_overview','consistency','trails_systems','gear_maintenance']:
            for name in ['date_filter','gear_filter']:
                v=json.loads((REPORT/f'definition/pages/{page}/visuals/{name}/visual.json').read_text())
                self.assertTrue(v['visual']['syncGroup']['filterChanges'])
        for path in (REPORT/'definition/pages/data_definitions').glob('visuals/*/visual.json'):
            self.assertNotIn('syncGroup',json.loads(path.read_text())['visual'])
