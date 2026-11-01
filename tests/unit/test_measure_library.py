"""Validate DAX dependency and column references against the actual shared model.

Desktop remains responsible for parsing/evaluating DAX and interactive checks.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
MODEL=ROOT/'power_bi/gps/activity_tracking.SemanticModel/definition/tables'


class MeasureLibraryTests(unittest.TestCase):
    def setUp(self):
        self.columns={p.stem:set(re.findall(r'\n\tcolumn (\w+)',p.read_text())) for p in MODEL.glob('*.tmdl')}
        source=(MODEL/'measures_.tmdl').read_text()
        self.measures={quoted or plain: body for quoted,plain,body in re.findall(r"\n\tmeasure (?:'([^']+)'|([A-Za-z_]\w*)) =(.*?)(?=\n\tmeasure |\n\tcolumn |\Z)",source,re.S)}

    def test_all_measure_and_column_dependencies_exist(self):
        for name,body in self.measures.items():
            # Ignore display metadata and description comments when scanning DAX.
            expression=body.split('\n\t\tformatString:')[0]
            for table,column in re.findall(r'\b(\w+)\[([^\]]+)\]',expression):
                self.assertIn(table,self.columns,(name,table))
                self.assertIn(column,self.columns[table],(name,table,column))
            for measure in re.findall(r'(?<![\w])\[([^\]]+)\]',expression):
                self.assertIn(measure,self.measures,(name,measure))

    def test_measure_dependencies_have_no_cycles(self):
        dependencies={name:set(re.findall(r'(?<![\w])\[([^\]]+)\]',body.split('\n\t\tformatString:')[0])) for name,body in self.measures.items()}
        done=set()
        def visit(name,path):
            self.assertNotIn(name,path,' -> '.join([*path,name]))
            if name in done:return
            for child in dependencies[name]:visit(child,[*path,name])
            done.add(name)
        for name in dependencies:visit(name,[])
