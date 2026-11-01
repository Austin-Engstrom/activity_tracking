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
| On Foot & Leg-Powered | Editable non-cycling leg-powered filter; mileage, moving hours, active days, type mix, weekly active-day trend and activity links |
| Consistency | All GPS activity types by default; active days/weeks, weekly participation and streaks; weekly/daily trends and detail |
| Trails & Systems | All GPS activity types by default; matched point mileage, assignment coverage, system/trail breakdowns and route detail |
| Gear & Maintenance | All GPS activity types for riding usage; separate latest exported component-service snapshot |
| Data Definitions | Independent, searchable measure and column reference |

There is **no report-wide sport filter**. The cycling filter moved to the Cycling
Overview page, where it selects Ride, MountainBikeRide, GravelRide, EBikeRide,
EMountainBikeRide, VirtualRide, Handcycle and Velomobile. The On Foot & Leg-Powered
page selects Run, TrailRun, VirtualRun, Walk, Hike, Snowshoe, NordicSki,
BackcountrySki, IceSkate, InlineSkate, RollerSki, StairStepper and Elliptical.
Both filters are visible and unlocked in Filters on this page. Only GPS-eligible
activities present in the semantic model participate, including indoor sports only
when they actually have GPS points. Downhill skiing/snowboarding, cycling and
paddling are excluded from the leg-powered page by default. Adjust the whitelist
to match the intended interpretation.

Only **date slicers sync** between analysis pages. Sport and equipment slicers are
page-specific so a bike/sport selection does not silently restrict all-activity
Consistency or the leg-powered page. A manual selection on Consistency still
intentionally changes its results; clear local slicers for all GPS activities.
The shared date selection starts January 1, 2026 with no fixed upper bound. This
saved start does not automatically change next January. Slider bars are hidden;
the date inputs remain visible.

## Layout and interpretation

All seven pages use a dark theme, 1440 × 1280 canvas, middle alignment and Fit to
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
sign in with access to the published model. Verify all seven pages render, the
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
