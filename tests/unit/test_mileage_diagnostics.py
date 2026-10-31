import unittest
from src.tools.diagnose_activity_mileage import analyze


def sample(index, seconds, distance, stored=None, latitude=41):
    return dict(point_index=index,time_seconds=seconds,distance_meters=distance,
        latitude=latitude,longitude=-93,stored_increment_meters=stored,
        reporting_index=index if latitude is not None else None,
        quality_status='valid' if stored is not None else None,is_moving=True)


class MileageDiagnosticsTests(unittest.TestCase):
    def analyze(self, rows, distance=200):
        return analyze(dict(activity_id=1,name='test',distance_meters=distance,
                            elapsed_time_seconds=200), rows)

    def test_excluded_gap_explains_missing_distance(self):
        summary, rows=self.analyze([sample(0,0,0),sample(1,10,50,50),sample(2,130,200)])
        self.assertEqual(rows[2]['diagnostic_reason'],'recording_gap')
        self.assertAlmostEqual(summary['excluded_signed_delta_sum_miles'],150/1609.344)
        self.assertAlmostEqual(summary['hypothetical_point_miles_by_gap_seconds']['120'],200/1609.344)
        self.assertAlmostEqual(summary['stored_point_miles'],50/1609.344)
        self.assertEqual(summary['source_minus_last_stream_miles'],0)

    def test_missing_coordinates_do_not_bridge_across_samples(self):
        summary,rows=self.analyze([sample(0,0,0),sample(1,10,100,latitude=None),sample(2,20,200)])
        self.assertEqual(rows[2]['diagnostic_reason'],'missing_or_invalid_coordinates')
        self.assertIsNone(summary['hypothetical_point_miles_by_gap_seconds']['no_time_gap_limit'])
        self.assertEqual(summary['diagnostic_reason_counts']['missing_or_invalid_coordinates'],2)

    def test_first_offset_and_source_tail_are_visible(self):
        summary,_=self.analyze([sample(0,5,20),sample(1,10,100,80)])
        self.assertAlmostEqual(summary['first_stream_distance_miles'],20/1609.344)
        self.assertAlmostEqual(summary['source_minus_last_stream_miles'],100/1609.344)
        self.assertAlmostEqual(summary['source_minus_stored_point_miles'],120/1609.344)

    def test_single_point_has_no_invented_zero_mileage(self):
        summary,_=self.analyze([sample(0,0,0)])
        self.assertEqual(summary['valid_gps_rows'],1)
        self.assertIsNone(summary['stored_point_miles'])
        self.assertEqual(summary['included_intervals'],0)

    def test_distance_reset_is_reported(self):
        summary,rows=self.analyze([sample(0,0,0),sample(1,10,100,100),sample(2,20,50),sample(3,30,150,100)])
        self.assertEqual(summary['negative_distance_intervals'],1)
        self.assertEqual(rows[2]['diagnostic_reason'],'negative_distance_increment')
        self.assertAlmostEqual(summary['excluded_signed_delta_sum_miles'],-50/1609.344)

    def test_missing_distances_and_no_streams(self):
        summary,_=self.analyze([sample(0,0,None),sample(1,10,100)])
        self.assertEqual(summary['intervals_without_known_distance_delta'],1)
        empty,_=self.analyze([])
        self.assertEqual(empty['stream_rows'],0)
        self.assertIsNone(empty['last_stream_distance_miles'])
