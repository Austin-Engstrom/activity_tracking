# Quanta Check

Open `power_bi/gps/activity_tracking.pbip` in Power BI Desktop. Its sole report
page is Quanta Check. This keeps the validation canvas with the dataset project;
other reports can connect to the shared `activity_tracking.SemanticModel`.
No extra dataset, SQL views or Parquet files are introduced. Close Desktop before
switching branches or pulling model edits. Existing generated Parquet files can
be reused; refresh the shared model normally.

The uploaded `strava_analytics_dataset.pbip` identifies the older companion report,
whose repository layout provided the reference: summary cards across the top,
date/type/gear matrices beneath, segment/trail matrices, and a bottom system grid.
The new page follows that arrangement, with an activity detail grid and quality
summary in place of deferred component and trail-completion reporting.

## Use

- Begin with no filters: compare activity/point counts, point miles, activity miles,
  mileage difference and UTC fallback count against the CLI audit.
- Select an activity in the bottom-right matrix to inspect a known ride. The
  dimension grids and cards use Power BI's normal cross-filter interactions.
- Inspect dates, activity types and gear, then named trails and systems. Blank
  trail/system rows represent unmatched points, not missing dimension records.
- Compare Point Moving Hours with Activity Moving Hours. Their difference is
  point-derived time minus whole-activity time, not an automatic error flag.
- Segment rows use Miles in Selected Segments. Overlapping segment rows are not
  additive; the total counts the union of linked points. Historical verification
  is partial until the separate Strava alignment backfill is complete.

All measures live in the shared model's `measures_.tmdl`. Added diagnostic measures
use the Validation display folder. Activity totals count each point-selected
activity once; filtering to one trail still includes the whole activity's summary
when showing activity-level measures. Unmatched Trail Miles includes both
system-matched/unmatched-trail points and points outside mapped systems. Recording
gaps are excluded from interval mileage under the current policy.

For the validated local snapshot, unfiltered checks are approximately 1,179
activities, 3,006,741 points, 8,201.38 point miles, 8,250.55 rounded activity miles,
and zero UTC fallback points. These are documentation examples, never hardcoded
report targets. New data and filters change them.

Static tests validate project paths, visual bindings and page bounds. Desktop
opening, visual rendering, interaction and DAX evaluation need Windows validation.
The older `strava_analytics_dataset` reference project remains separate.
For future deployed thin reports, publish the shared semantic model and bind
reports to that published model through Power BI; this project's byPath binding
is the local development arrangement.
