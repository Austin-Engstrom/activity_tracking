"""Validate reportable model metadata coverage and catalog isolation."""
from pathlib import Path
import re
import unittest

MODEL = Path(__file__).resolve().parents[2] / 'power_bi/gps/activity_tracking.SemanticModel/definition'
HELPERS = {'measures_', 'select_measures', 'select_dimensions', 'data_dictionary'}


class DataDictionaryTests(unittest.TestCase):
    def test_catalog_has_matching_union_projections(self):
        content = (MODEL / 'tables/data_dictionary.tmdl').read_text()
        self.assertIn('INFO.VIEW.MEASURES ()', content)
        self.assertIn('INFO.VIEW.COLUMNS ()', content)
        expected = {
            'Object Type': None, 'Table Name': 'Table', 'Object Name': 'Name',
            'Description': 'Description', 'Display Folder': 'DisplayFolder',
            'Data Type': 'DataType', 'Format String': 'FormatString',
            'DAX Expression': 'Expression', 'Is Hidden': 'IsHidden',
        }
        columns = re.findall(r"\n\tcolumn '([^']+)'\n(.*?)(?=\n\t(?:column|partition)|\Z)", content, re.S)
        self.assertEqual({name for name, _ in columns}, set(expected))
        for name, block in columns:
            if expected[name]:
                self.assertEqual(content.count(f'"{name}", [{expected[name]}]'), 2)
            self.assertIn(f'sourceColumn: [{name}]', block)
            self.assertIn('summarizeBy: none', block)
            self.assertNotIn('isHidden', block)
        self.assertIn('"Object Type", "Measure"', content)
        self.assertIn('"Object Type", "Column"', content)
        self.assertIn('partition data_dictionary = calculated', content)

    def test_column_scope_covers_analytical_tables_and_descriptions(self):
        content = (MODEL / 'tables/data_dictionary.tmdl').read_text()
        scope = set(re.findall(r'"(\w+)"', re.search(r'\[Table\] IN \{(.*?)\}', content)[1]))
        analytical = {p.stem for p in (MODEL / 'tables').glob('*.tmdl')} - HELPERS
        self.assertEqual(scope, analytical)
        for table in analytical:
            text = (MODEL / 'tables' / f'{table}.tmdl').read_text()
            names = re.findall(r'\n\tcolumn (\w+)', text)
            documented = re.findall(r'\n\t/// [^\n]+\n\tcolumn (\w+)', text)
            self.assertTrue(names, table)
            self.assertEqual(names, documented, table)

    def test_catalog_is_registered_without_analytical_relationships(self):
        self.assertIn('ref table data_dictionary', (MODEL / 'model.tmdl').read_text())
        self.assertNotIn('data_dictionary.', (MODEL / 'relationships.tmdl').read_text())
