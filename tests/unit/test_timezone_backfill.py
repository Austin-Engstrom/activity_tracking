import unittest
from src.tools.backfill_activity_timezones import parse_zone, local_date_key


class TimezoneTests(unittest.TestCase):
    def test_strava_zone_and_invalid_zone(self):
        self.assertEqual(parse_zone('(GMT-06:00) America/Chicago'),'America/Chicago')
        self.assertIsNone(parse_zone('Invalid/Zone'))
        self.assertIsNone(parse_zone(None))

    def test_local_dates_use_daylight_saving_rules(self):
        self.assertEqual(local_date_key('2026-01-02T05:30:00+00:00','America/Chicago'),20260101)
        self.assertEqual(local_date_key('2026-07-02T05:30:00+00:00','America/Chicago'),20260702)
        self.assertIsNone(local_date_key(None,'America/Chicago'))
