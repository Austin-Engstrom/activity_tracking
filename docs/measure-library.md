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
