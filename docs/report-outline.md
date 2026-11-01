# Report-building outline

Proposed first release for the personal activity-history audience. Confirm page
priority while building; all pages use the published GPS semantic model. Keep
Quanta Check with the model as the validation report.

| Page | Questions | Starting measures / visuals | Filters |
|---|---|---|---|
| Activity overview | How much activity, distance and time occurred? How is it changing? | Activities Ridden, Miles Ridden, Whole Activity Miles, Point Moving Hours, Activity Moving Hours; monthly trend and activity detail | Local date, activity type, gear |
| Consistency | How regularly am I active? Where are the gaps? | Active Days/Weeks, Active Day/Week %, longest streaks; date/week matrix including inactive periods | Local date, activity type, gear |
| Trails and systems | Where do I ride and how much distance is assigned? | Matched Trail Miles, Matched System Miles, Trails Visited, match percentages; trail/system matrix | Local date, activity type, gear, trail/system |
| Segments | Which verified segments overlap the selected riding? What trail associations are observed? | Miles in Selected Segments, Linked Segment Effort Count; separate history-wide association matrix | Segment plus date/activity for route measures; label association matrix as all verified history |
| Gear usage | How is GPS-recorded usage distributed by equipment? | Miles Ridden, Activities Ridden, Activity Moving Hours by gear and month | Local date, activity type, gear |

## Visual and measure rules

Use explicit measures from `measures_`, dimensions for slicers and identifiers with
Don't summarize. Use `dates[date]` for local reporting; activity start-date fields
are UTC source attributes. Use week-start dates for weekly axes. Apply a cycling
sport filter when a page says rides: eligibility itself includes all GPS sports.

Label point distance/time and whole-activity distance/time separately. Whole
activity values include the entire activity even under a partial trail/date filter.
Avoid adding whole-activity values across trail rows. Ordinary mileage and
consistency measures do not respond to a segment slicer; use the segment-aware
measures on segment visuals. Overlapping segment mileage totals count a point union,
not the sum of rows. Association catalog measures ignore date/activity/gear filters;
keep their historical scope visible and separate from route-filtered totals.

Gear source lifetime distance is not GPS-filtered usage. Match percentages measure
assignment coverage; visited trail length is catalog length, not unique ridden
length or completion. Maintenance, non-GPS activity reporting, unique trail coverage
and completion remain deferred.

## Acceptance before sharing

Start with one known activity and a bounded date range, then check full history.
Reconcile top-level totals with the same refreshed Quanta Check model. Test empty
selections, missing telemetry, unmatched trails, midnight crossings, inactive days
and weeks, year boundaries, repeated efforts and overlapping segments. Check that
all-date streak measures retain non-date filters. Verify sensible response time on
full history and deployed viewer access. Follow the publication record in
[publishing handoff](publishing-handoff.md) before sharing each report.
