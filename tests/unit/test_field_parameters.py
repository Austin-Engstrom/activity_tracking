"""Validate field parameter bindings, metadata and isolation from the star."""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition'


class FieldParameterTests(unittest.TestCase):
    def test_every_parameter_target_resolves_and_ordinals_are_unique(self):
        measures={a or b for a,b in re.findall(r"\n\tmeasure (?:'([^']+)'|([A-Za-z_]\w*)) =",(MODEL/'tables/measures_.tmdl').read_text())}
        columns={p.stem:set(re.findall(r'\n\tcolumn (\w+)',p.read_text())) for p in (MODEL/'tables').glob('*.tmdl')}
        model=(MODEL/'model.tmdl').read_text()
        relationships=(MODEL/'relationships.tmdl').read_text()
        for name in ['select_measures','select_dimensions']:
            content=(MODEL/'tables'/f'{name}.tmdl').read_text()
            entries=re.findall(r'\("([^"]+)", NAMEOF\(\'([^\']+)\'\[([^\]]+)\]\), (\d+)\)',content)
            self.assertTrue(entries)
            self.assertEqual(len({label for label,_,_,_ in entries}),len(entries))
            self.assertEqual([int(order) for _,_,_,order in entries],list(range(len(entries))))
            self.assertIn(f'ref table {name}',model)
            self.assertNotIn(name+'.',relationships)
            for _,table,field,_ in entries:
                if name=='select_measures':
                    self.assertEqual(table,'measures_')
                    self.assertIn(field,measures)
                else:
                    self.assertNotIn(table,['activity_points','segment_trail_associations'])
                    self.assertIn(field,columns[table])
            if name=='select_measures':
                self.assertEqual({field for _,_,field,_ in entries},measures)

    def test_parameter_metadata_and_hidden_sort_columns(self):
        for name in ['select_measures','select_dimensions']:
            content=(MODEL/'tables'/f'{name}.tmdl').read_text()
            self.assertIn('relatedColumnDetails\n\t\t\tgroupByColumn: fields',content)
            self.assertIn('sortByColumn: sort_order',content)
            metadata=re.search(r'extendedProperty ParameterMetadata =\s*(\{.*?\})',content,re.S)
            self.assertEqual(json.loads(metadata[1]),{'version':3,'kind':2})
            self.assertRegex(content,r'extendedProperty ParameterMetadata =[^\n]+\n\t\t\ttype: json')
            self.assertIn(f'partition {name} = calculated',content)
            for field in ['fields','sort_order']:
                block=re.search(r'\n\tcolumn '+field+r'\n(.*?)(?=\n\t(?:column|partition)|\Z)',content,re.S)[1]
                self.assertIn('isHidden',block)
                self.assertIn('summarizeBy: none',block)
