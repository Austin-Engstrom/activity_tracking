"""Check the dataset report's bindings and one-page layout against the shared model."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'power_bi/gps'


class QuantaReportTests(unittest.TestCase):
    def test_shared_dataset_and_single_page(self):
        project=json.loads((BASE/'activity_tracking.pbip').read_text())
        report=BASE/project['artifacts'][0]['report']['path']
        binding=json.loads((report/'definition.pbir').read_text())
        dataset=(report/binding['datasetReference']['byPath']['path']).resolve()
        self.assertEqual(dataset,ROOT/'power_bi/gps/activity_tracking.SemanticModel')
        pages=json.loads((report/'definition/pages/pages.json').read_text())
        self.assertEqual(pages['pageOrder'],['quanta_check'])
        self.assertEqual(pages['activePageName'],'quanta_check')

    def test_visual_bindings_and_bounds(self):
        model=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition/tables'
        columns={p.stem:set(re.findall(r'\n\tcolumn (\w+)',p.read_text())) for p in model.glob('*.tmdl')}
        measures=set(re.findall(r"\n\tmeasure '([^']+)'",(model/'measures_.tmdl').read_text()))
        page=BASE/'activity_tracking.Report/definition/pages/quanta_check'
        size=json.loads((page/'page.json').read_text())
        visuals=[json.loads(p.read_text()) for p in (page/'visuals').glob('*/visual.json')]
        self.assertGreaterEqual(len(visuals),10)
        self.assertEqual(len({v['name'] for v in visuals}),len(visuals))
        for visual in visuals:
            position=visual['position']
            self.assertLessEqual(position['x']+position['width'],size['width'])
            self.assertLessEqual(position['y']+position['height'],size['height'])
            self.assertGreaterEqual(position['x'],0)
            self.assertGreaterEqual(position['y'],0)
            for role in visual['visual'].get('query',{}).get('queryState',{}).values():
                for projection in role['projections']:
                    kind,field=next(iter(projection['field'].items()))
                    entity=field['Expression']['SourceRef']['Entity']
                    self.assertIn(entity,columns)
                    if kind=='Measure':
                        self.assertEqual(entity,'measures_')
                        self.assertIn(field['Property'],measures)
                    else:
                        self.assertIn(field['Property'],columns[entity])

    def test_report_json_valid_and_no_duplicate_project(self):
        self.assertFalse((ROOT/'power_bi/validation/quanta_check.pbip').exists())
        for path in BASE.rglob('*.json'):
            json.loads(path.read_text())
        gps_binding=json.loads((ROOT/'power_bi/gps/activity_tracking.Report/definition.pbir').read_text())
        self.assertEqual(gps_binding['datasetReference']['byPath']['path'],'../activity_tracking.SemanticModel')
