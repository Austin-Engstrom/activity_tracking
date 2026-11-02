# Dataset measure library

All measures are defined in `power_bi/gps/activity_tracking.SemanticModel/definition/tables/measures_.tmdl`.
Each has a display folder and new measures include descriptions. The older
`strava_analytics_dataset` model was the inventory source, not a formula template.
No SQL, export schema, relationships or report visuals change in this update.

## Reused concepts and adaptations

| Older measure/concept | Current dataset measure | Scope |
|---|---|---|
| Activity Count | Activities Ridden (existing) | Distinct point-selected activities |
| Total Distance | Miles Ridden / Whole Activity Miles (existing) | Selected point distance / full activity distance |
| Total Moving Time | Point Moving Hours / Activity Moving Hours (existing) | Eligible point intervals / Strava summaries |
| Total Elapsed Time | Activity Elapsed Hours | Whole activity summaries |
| Total Elevation Gain | Activity Elevation Gain Feet | Whole activity summaries |
| Total Calories | Activity Calories | Whole activity summaries; unknown remains blank |
| Average Distance | Average Activity Miles | Full activity miles / selected activity count |
| Average Moving Time | Average Activity Moving Hours | Full activity moving hours / selected activity count |
| Average Elevation Gain | Average Activity Elevation Gain Feet | Full activity elevation / selected activity count |
| Average Speed | Activity Average Speed mph | Whole activity miles / whole activity moving hours |
| Elevation per Mile | Activity Elevation Feet per Mile | Whole activity feet / whole activity miles |
| Ride Days | Activity Days | Distinct selected local point dates, all GPS sport types |
| Miles per Activity | Point Miles per Activity | Point miles / selected activity count |
| Segment Effort Count | Segment Effort Count | All efforts in point-selected activities |
| Segment Miles Ridden | Segment Effort Miles | Sum of effort distances; overlapping efforts are additive |
| Segment Moving Time | Segment Effort Moving Hours | Sum of effort durations; overlaps can repeat time |
| Segment participation | Segments Ridden | Distinct segments in the selected activities' efforts |
| Verified segment participation | Linked Segment Effort Count | Verified efforts touching selected points |
| Trail Ride Count | Matched Trail Activities | Distinct activities with a selected matched trail point |
| Trail Miles Ridden | Matched Trail Miles | Point miles confidently assigned to trails |
| Trails Ridden | Trails Visited | Distinct nonblank point trail keys, all GPS sport types |
| Official trail lengths | Visited Trail Length Miles | Full mapped length of each distinct touched trail, once |
| System usage | Matched System Miles / Trail Systems Visited | Assigned point distance / distinct nonblank systems |
| Assignment coverage | Trail Match % / System Match % | Assigned point mileage / selected point mileage |
| Activity Miles by Trail Context | Whole Activity Miles (existing) | Whole summaries for activities touching selected points |

## Filter and aggregation rules

Dimensions filter points in one direction. Whole-activity measures explicitly
transfer selected point activity keys back to `activities`; partial trail/date
filters include the entire summaries of the activities they touch. Elevation,
calories and activity averages are therefore not allocated to individual trails.
Average speed is duration-weighted by dividing aggregated distance by aggregated
moving time. It is not an arithmetic average of activity speeds. DIVIDE returns
blank when the denominator is zero; missing calories are not replaced with zero.

Segment Effort Count, Segment Effort Miles, Segment Effort Moving Hours, and
Segments Ridden explicitly apply selected activity keys to the effort table and
also retain segment filters. These work for efforts whose historical point links
are not verified. On a partial trail/date selection, they describe whole efforts
in the touched activities, not only that selected route portion. Effort miles/time
are additive per effort and may overlap. In contrast, existing Miles in Selected
Segments and new Linked Segment Effort Count use verified point membership and
respect the selected route portions. Verification coverage is still partial.

All ordinary activity/trail/system measures retain the existing segment-filter
behavior: a segment selection alone does not filter points. Use segment-aware
measures for segment analysis. No bidirectional relationships or hidden filter
paths are introduced. Measures using selected point keys can be more expensive
on a full-history canvas; begin validation on a known activity.

Trails Visited, Trail Systems Visited and Activity Days exclude blank keys. An
activity spanning local midnight can contribute two activity days. Visited Trail
Length Miles counts each touched trail's full mapped length, regardless of how
much was traversed. Repeated rides do not multiply that catalog length.
Trail/System Match % describe assignment coverage only, not trail completion.
A 100% match within a named-trail filter does not imply the whole trail was ridden.

## Deliberately omitted

Maintenance/component measures remain deferred. Unique Trail Miles Ridden,
Remaining Trail Miles and Trail Completion % require unique spatial coverage
that the new model does not currently store. Repeated point mileage cannot safely
substitute for that coverage. Average Distance and Miles per Activity were
redundant at activity-summary grain, so the adapted measures name their grain
explicitly instead of adding synonymous aliases.

## Validate in Power BI

Close Desktop, pull the branch, reopen `activity_tracking.pbip`, and refresh the
model metadata. No new Parquet export or database rebuild is required.

1. Filter to activity `20784488267`: Activity Moving Hours should remain about
   1.33 and Activity Average Speed mph should be about 7.6. Compare activity
   elevation/calories with Strava when available.
2. Filter to a single named trail in that ride: point mileage should decrease;
   activity-summary totals should remain the full ride totals.
3. Add segment names with Segment Effort Count/Miles and Miles in Selected
   Segments. Confirm repeated/overlapping efforts are additive in the effort
   measures while the linked-point mileage total remains a union.
4. Review Trails Visited/Trail Systems Visited against known selections; blank
   assignment rows should not add a visited trail/system.
5. Check zero/empty selections: ratios should remain blank rather than divide by
   zero. New measures do not claim missing data or unverified links are complete.

Automated checks validate names, field/dependency references, cycles, display
folders and existing exports/report bindings. DAX parsing, rendering and filter
semantics still require these Desktop checks; Python tests are not a DAX engine.

## Activity links to Strava

`Activity URL` (Activities folder) returns
`https://www.strava.com/activities/<activity_id>` when the current selected GPS
points represent exactly one activity. For activity `20796076161`, the expected
result is `https://www.strava.com/activities/20796076161`. FORMAT with `0` keeps
identifiers free of grouping separators, decimals or scientific notation.

The measure is categorized as Web URL. Add it to an activity-detail table beside
`activities[activity_id]` and the activity name; enable URL icons in the table's
format settings if desired. Alternatively use it as the Web URL conditional
formatting field for the activity-name column. Duplicate names require the ID in
the row context. Totals/multi-activity contexts and empty selections return blank;
a total filtered to exactly one activity intentionally retains its link.

The ID comes from selected points so local-date, sport, gear and route filters
follow the reporting model. A segment slicer alone does not restrict ordinary point
context. The URL opens the source page using the viewer's Strava permissions; it
does not grant access to private activities or restore deleted activities.

Reopen and refresh the GPS model, then republish the shared semantic model to expose
the measure to connected reports. No ETL or Parquet re-export is required. The
embedded dictionary includes its definition. In Desktop verify an individual
activity link, a multi-activity total, an empty selection and duplicate-name rows;
click a known link and confirm the activity ID matches. Repository tests do not
execute DAX or verify browser navigation.

## Segment record summaries

The Segments / Records folder adds Recorded Segment Efforts, Rank Observed Efforts,
Rank Observation Coverage %, Unobserved Rank Efforts, Reported PR Firsts, Reported
KOM Firsts and Segments With Stored Best. Effort summaries follow effort-start
dates and the effort table's dimension filters. Coverage requires both API rank
fields to be returned, including explicit nulls; legacy/omitted fields remain
unobserved. Segments With Stored Best is an all-history, segment-only summary.
See [report and location-map notes](cycling-report.md#activity-frequency-maps-and-segment-prs)
for the PR page and interpretation limits.

## Seconds behind the segment PR

`Seconds Behind Segment PR` compares one selected eligible effort's elapsed seconds
with the fastest eligible stored effort for its segment across all imported GPS
history. It is blank for ambiguous/no effort, hidden or nonpositive-time efforts,
or a missing baseline. Date/category/equipment selections do not change the PR
baseline. The lookup transfers the current effort's segment key explicitly; an
effort row does not rely on a bidirectional segment relationship.

A 75-second effort with a 60-second best shows **+15**. The 60-second best and ties
show **0**. A negative result means the effort beats the loaded best snapshot;
check that both tables were exported/refreshed together. This is not an official
Strava lifetime-PR guarantee and works before rank backfill is complete.

The measure is included in the Segment PRs effort-history table, measure selector
and dictionary. Reopen/refresh and republish the GPS model before using this report
revision. No Parquet re-export is needed if both tables are already current.
In Desktop verify a best effort, a slower effort, a tie, date-filter changes,
a hidden/invalid effort and a multi-effort total. Repository tests do not execute DAX.

## Segment length

`Segment Length Miles` returns a single segment's catalog distance, formatted to
two decimals. Use the segment dimension to select a segment or place it on a
segment-effort detail row. Multiple segments or unknown source distance return
blank. A date selection does not shorten a segment's catalog length.

Both PR tables show Segment length (mi): the effort table uses this measure, while
the all-history best table uses the existing `segments[distance_miles]` attribute.
This is distinct from `Segment Miles`, which accumulates effort distances and can
count repeated or overlapping traversals. Refresh and republish the GPS model for
the new measure; no Parquet re-export is needed.
