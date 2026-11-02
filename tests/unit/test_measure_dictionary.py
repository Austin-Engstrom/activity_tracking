"""Validate the embedded catalog matches native metadata without runtime INFO calls."""
from pathlib import Path
import re
import tempfile
import unittest

from src.tools.build_data_dictionary import FIELDS, HELPERS, MODEL, metadata_rows, m_literal, render


class DataDictionaryTests(unittest.TestCase):
    def test_embedded_catalog_matches_source_and_has_no_metadata_queries(self):
        content = (MODEL / 'tables/data_dictionary.tmdl').read_text()
        self.assertEqual(content, render())
        self.assertNotIn('INFO.VIEW.', content)
        self.assertIn('partition data_dictionary = m', content)
        self.assertNotIn('File.Contents', content)
        self.assertIn('ref table data_dictionary', (MODEL / 'model.tmdl').read_text())
        self.assertNotIn('data_dictionary.', (MODEL / 'relationships.tmdl').read_text())
        for field in FIELDS:
            self.assertRegex(content, r"\n\tcolumn (?:'" + re.escape(field) + r"'|" + re.escape(field) + r")\n")
            self.assertIn(f'sourceColumn: {field}', content)

    def test_catalog_covers_all_native_objects_and_descriptions(self):
        rows = metadata_rows()
        expected = set()
        for path in (MODEL / 'tables').glob('*.tmdl'):
            if path.stem == 'data_dictionary':
                continue
            for kind, name in re.findall(r"^\t(measure|column) ('[^']+'|[^\s=]+)", path.read_text(), re.M):
                if kind == 'column' and path.stem in HELPERS:
                    continue
                expected.add((kind.title(), path.stem, name.strip("'")))
        self.assertEqual({tuple(row[:3]) for row in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertTrue(all(row[3] for row in rows))
        objects = {row[2]: row for row in rows if row[0] == 'Measure'}
        self.assertIn('RETURN', objects['Next Service Remaining'][7])
        self.assertIn('MAXX(', objects['Longest Active Day Streak'][7])
        self.assertEqual(objects['Miles'][7], 'SUM(activity_points[incremental_distance])')

    def test_m_literal_preserves_special_characters(self):
        self.assertEqual(m_literal('a"b\n#(lf)\t'), '"a""b#(lf)#(#)(lf)#(tab)"')
        self.assertEqual(m_literal(None), 'null')
        self.assertEqual(m_literal(False), 'false')

    def test_native_metadata_changes_are_reflected_by_generator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tables').mkdir()
            path = root / 'tables/example.tmdl'
            path.write_text('table example\n\t/// Original\n\tcolumn label\n\t\tdataType: string\n\t\tisHidden\n')
            self.assertEqual(metadata_rows(root)[0][3], 'Original')
            path.write_text(path.read_text().replace('Original', 'Updated'))
            row = metadata_rows(root)[0]
            self.assertEqual(row[3], 'Updated')
            self.assertTrue(row[-1])
