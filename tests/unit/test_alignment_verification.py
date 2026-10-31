import unittest
from src.tools.validate_point_reporting import verify_alignment

class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(point_index=i,time_seconds=i*10,latitude=41+i/100,longitude=-93) for i in range(2)]
        self.payload={key:dict(original_size=2,series_type='distance',data=data) for key,data in [('time',[0,10]),('latlng',[[41,-93],[41.01,-93]])]}

    def test_original_arrays_match(self):
        self.assertTrue(verify_alignment(self.rows,self.payload)[0])

    def test_resampled_arrays_rejected(self):
        self.payload['time']['original_size']=4
        self.assertEqual(verify_alignment(self.rows,self.payload),(False,'resampled_stream'))

    def test_same_length_but_different_points_rejected(self):
        self.payload['latlng']['data'][1][0]=42
        self.assertEqual(verify_alignment(self.rows,self.payload),(False,'coordinates_changed'))

    def test_shifted_indexes_rejected(self):
        self.rows[0]['point_index']=1
        self.assertEqual(verify_alignment(self.rows,self.payload),(False,'time_index_changed'))

    def test_missing_sample_rejected(self):
        self.assertEqual(verify_alignment(self.rows[:1],self.payload),(False,'sample_count_changed'))
