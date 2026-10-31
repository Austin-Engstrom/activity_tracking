"""Power BI must receive real Parquet types even for empty/all-null columns."""
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine
from src.tools.export_power_bi import export_view

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((ROOT/'src/reporting/gps_schema.json').read_text())


class ReportingTypeTests(unittest.TestCase):
    def test_empty_and_null_only_exports_have_explicit_types(self):
        engine=create_engine('sqlite://')
        try:
            with engine.connect() as conn, TemporaryDirectory() as folder:
                for view, columns in CONTRACT.items():
                    for empty in [True, False]:
                        with self.subTest(view=view,empty=empty):
                            conn.exec_driver_sql(f'DROP VIEW IF EXISTS {view}')
                            select=', '.join(f'NULL AS "{name}"' for name in columns)
                            conn.exec_driver_sql(f'CREATE VIEW {view} AS SELECT '+select+(' WHERE 0' if empty else ''))
                            result=export_view(conn,view,Path(folder))
                            self.assertTrue(result.success,result.error)
                            schema=pq.read_schema(Path(folder)/(view+'.parquet'))
                            self.assertFalse(any(pa.types.is_null(field.type) for field in schema))
                            self.assertEqual(result.row_count,0 if empty else 1)
        finally:
            engine.dispose()

    def test_model_types_and_power_query_match_contract(self):
        model=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition/tables'
        seen=set()
        for path in model.glob('*.tmdl'):
            content=path.read_text()
            view=re.search(r'ExportFolder & "(view_\w+).parquet"',content)[1]
            seen.add(view)
            types=dict(re.findall(r'\n\tcolumn (\w+)\n\t\tdataType: (\w+)',content))
            self.assertEqual(types,CONTRACT[view])
            self.assertIn('Table.TransformColumnTypes',content)
            for column in types:
                self.assertIn('{"'+column+'", ',content)
        self.assertEqual(seen,set(CONTRACT))
