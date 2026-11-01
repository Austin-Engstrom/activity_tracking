"""Protect maintenance DAX from TMDL properties indented into its expression."""
import unittest
from src.tools.build_data_dictionary import metadata_rows


class MaintenanceMeasureMetadataTests(unittest.TestCase):
    def test_next_service_expression_excludes_model_properties(self):
        row=next(row for row in metadata_rows() if row[:3]==['Measure','measures_','Next Service Remaining'])
        self.assertEqual(row[4],'Maintenance')
        self.assertIn('RETURN IF(',row[7])
        self.assertNotIn('displayFolder:',row[7])
        self.assertNotIn('lineageTag:',row[7])
