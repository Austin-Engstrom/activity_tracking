# Activity Analytics report

Open `power_bi/report/Activity Analytics.pbip` on the report branch. The project
retains the original published `activity_tracking` semantic-model connection and
logical report identity; there is no copied model or Parquet dependency. The
existing GPS project and Quanta Check are unchanged.

## Pages and scope

| Page | Scope and layout |
|---|---|
| Activity Overview | All GPS activities; activity miles/hours, activity and active-day cards; weekly point-mile trend; activity-type and equipment breakdowns; detail with Strava links |
| Cycling Overview | Editable cycling page filter; same riding summary and detail |
| Running, Walking & Hiking | Editable Walking / Hiking and Running activity-category filter; mileage, moving hours, active days, type mix, weekly active-day trend and activity links |
| Consistency | All GPS activity types by default; active days/weeks, weekly participation and streaks; weekly/daily trends and detail |
| Trails & Systems | All GPS activity types by default; matched point mileage, assignment coverage, system/trail breakdowns and route detail |
| Gear & Maintenance | All GPS activity types for riding usage; separate latest exported component-service snapshot |
| Data Definitions | Independent, searchable measure and column reference |

There is **no report-wide sport filter**. The cycling filter moved to the Cycling
Overview page, where it selects Ride, MountainBikeRide, GravelRide, EBikeRide,
EMountainBikeRide, VirtualRide, Handcycle and Velomobile. The Running, Walking & Hiking
page filters `activity_types[activity_category]` to exactly `Walking / Hiking` and
`Running`, so sports enter the page through their category mapping rather than a
hardcoded sport whitelist.
Both filters are visible and unlocked in Filters on this page. Only GPS-eligible
activities present in the semantic model participate, including indoor sports only
when they actually have GPS points.

Only **date slicers sync** between analysis pages. Sport and equipment slicers are
page-specific so a bike/sport selection does not silently restrict all-activity
Consistency or the leg-powered page. A manual selection on Consistency still
intentionally changes its results; clear local slicers for all GPS activities.
The shared date selection starts January 1, 2026 with no fixed upper bound. This
saved start does not automatically change next January. Slider bars are hidden;
the date inputs remain visible.

## Layout and interpretation

All eight pages use a dark theme, 1440 × 1280 canvas, middle alignment and Fit to
width. A twelve-column grid gives 24px outer margins and gutters: equal cards span
three columns, slicers span four, and chart rows use 8/4 or 6/6 splits. Titles replace
duplicate card category labels. Date visuals sort newest first; mileage visuals
without dates sort highest first. Normal page tabs provide navigation.

Overview cards show whole-activity totals while weekly trends use point mileage.
Whole summaries for activities crossing dates can contribute to multiple contexts;
partial-route/period whole totals are not always additive. Activity-detail dates
are UTC source dates; date slicers use local point dates. IDs distinguish duplicate
activity names; Activity URL opens the corresponding Strava page with viewer access.
Trail matching coverage is not matching accuracy or unique completion.

Maintenance is a current export-time snapshot using all source usage on each
component's equipment; it does not recalculate with riding date/sport filters.
The local equipment slicer does filter service rows. Display remaining service
intervals per component with their hours/miles units; do not sum mixed units.

## Desktop review

Close Desktop before switching branches, then open `Activity Analytics.pbip` and
sign in with access to the published model. Verify all eight pages render, the
model includes the published Activity URL/dictionary/maintenance fixes, and renamed
report paths load. No dataset refresh or republication is needed for these
report-only scope/layout changes.

Compare Consistency with all GPS totals in Quanta Check under the same date range;
check that running/walking now contribute active dates and streaks. Move between
Cycling and On Foot pages to confirm local sport/equipment filters do not transfer,
while date selections do. Check known activities, Strava links, inactive weeks,
unmatched trail rows, component service values and dictionary search. Refine text
sizes, chart density, widths and tooltips in Desktop as needed. Before publishing,
verify intended viewer access and choose whether to replace the existing report
or publish a renamed item.

Static tests check the preserved live binding, seven-page layout, field references,
page bounds/grid, page-specific sports, isolated sport/gear slicers and shared date
selection. They do not render visuals or execute live queries. One existing
field-parameter metadata-format test on main remains unrelated to this report.

The Activity Overview category breakdown uses `activity_types[activity_category]`.
Every date-axis chart has a report-level drill sequence of year, month_name, week_start_date and date using existing calendar columns. It opens expanded to Month within Year with
newest-first sorting; use the chart drill/expand controls for finer time detail.
The calculated `dates[month_name]` column is sorted by month_number. Refresh and republish the GPS semantic model before opening this report revision. No Parquet re-export is required.
Date slicers explicitly persist their displayed start as January 1, 2026 in addition
to the lower-bound selection; no end value is stored. Desktop rendering remains
the verification for the displayed date inputs.

Visual subtitles are disabled throughout the report.

The drill order is Year → Month name → Week (Monday start) → Day (full date).
Year and Month are initially active to keep years distinct when displaying months.
Weeks crossing month boundaries appear under both months with only that month's
selected dates; the weekly start date can fall in the prior month.

Month-name chart axes display January through December, using the model month_number sort; years remain newest first. This overrides descending date order at the month level.

## GPS density maps and Segment PRs

Four map placeholders on Overview, Cycling, Running/Walking/Hiking and Trails &
Systems now use Azure Maps heat layers. The previous empty shape-map placeholder
is converted to Azure Maps. The existing manual positions and other visuals are
preserved. Heatmap locations group the calculated `activity_points[map_latitude]`
and `[map_longitude]` fields, rounded to 0.001 degrees. Each plotted cell is weighted
by the existing `GPS Points` measure, with a dark basemap and teal/orange density
ramp; tooltip measures include GPS points, activities and point miles.

This is **recorded sample density**, not independent visit counts or a mileage/time
heatmap. Repeated samples raise the weight, and different sampling rates/slow or
stationary recording can affect hotspots. Cell size is approximately 111 metres
north/south and varies east/west by latitude. Azure Maps can reduce large datasets
(roughly 30,000 plotted locations): inspect data-reduction notices and use a bounded
date range when reviewing broad history. Rounded grouping reduces cardinality but
does not guarantee every selection fits that limit. Radius/intensity are visual
smoothing controls rather than physical distance measurements.

The new **Segment PRs** page contains:

- Synced effort-start date selection, plus page-local category and segment slicers.
- Reported PR firsts, reported KOM firsts, observation coverage and unobserved counts.
- A year/month/week/day trend of observed firsts.
- Effort history with rank statuses, retrieval timestamps, elapsed seconds and
  source activity links, sorted newest first.
- A separate fastest-known stored effort table across all imported GPS history,
  filtered by segment only. Date/category selections do not recompute these bests;
  chart/effort selections do not cross-filter that table.

Coverage requires **both** rank fields to be returned; explicit null fields count
as observed while omitted fields/legacy data do not. Zero reported firsts under
partial coverage is not evidence that none occurred. KOM firsts are retrieval-time
API observations, not current crowns or certified historical leaderboard positions.
Stored bests are based on imported eligible effort history, not official lifetime
records. All new measures are in `measures_` under Segments / Records and are
included in the embedded dictionary and measure-selection field parameter.

### Apply this revision

Open the GPS dataset project, refresh/recalculate and republish `activity_tracking`
first: this revision adds the two calculated map-coordinate columns and seven
summary measures. Existing Parquet files suffice; no ETL or additional export is
required for these changes. Then reopen `power_bi/report/Activity Analytics.pbip`.
Check that Azure Maps is enabled for your signed-in Power BI environment and that
all four heat layers render under the intended date/category filters.

On a known route, compare point totals for a few cells and check repeat rides
increase density. On Segment PRs, check coverage against the current exported rank
statuses, verify a known effort/link, and confirm the bottom best table is stable
under date/category changes while the upper history changes. Map rendering,
DAX execution, smoothing and deployed performance require Desktop/Service review;
repository schema and binding checks cannot establish those results.

Validation for this revision: 18 targeted report/model/export/dictionary checks
pass. The full suite has 88 passes and one existing field-parameter metadata-format
failure. New page and changed maps pass public PBIR structure validation; ten
Desktop-authored 2.14 containers were checked against the common public 2.12
structure because the public repository does not yet publish that newer version.
Azure-specific layer properties still need Desktop render verification.
