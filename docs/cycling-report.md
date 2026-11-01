# Cycling report draft

Open `power_bi/report/cycling_analytics.pbip`. This is a separate five-page report using the
published activity_tracking shared model; the existing GPS PBIP and Quanta Check report are unchanged.
All visuals are native Power BI visuals and can be edited in Desktop.

| Page | Draft layout |
|---|---|
| Cycling Overview | Activity miles/hours, activity and active-day cards; weekly point-mile trend; sport and gear breakdowns; activity detail with Strava URL |
| Consistency | Active-day/week cards and weekly streak; weekly active days, daily counts, weekly detail |
| Trails & Systems | Assigned trail mileage and coverage cards; system/trail rankings; point-mile detail |
| Gear & Maintenance | Date-selected riding usage and gear comparison; separate current component service table |
| Data Definitions | Searchable object/table/name slicers and wrapped model descriptions |

The canvas is 1440 × 1000 with shared spacing, a light theme, navy text, teal and
orange accents, four top-row KPI cards, charts and bottom detail tables. Use the
normal page tabs to navigate. This is an editable draft, not a claim of rendered
Desktop validation.

## Cycling and other filters

The unlocked, visible **Cycling sports (editable)** report filter selects Ride,
MountainBikeRide, GravelRide, EBikeRide, EMountainBikeRide, VirtualRide, Handcycle and
Velomobile. Only sports present in the GPS model appear in visuals. Expand, replace
or clear this filter in the report Filters pane to change scope across pages.
Non-GPS indoor activities remain outside the source model regardless of this filter.

Date and equipment slicers are synchronized across the four analysis pages. Sport
slicers are synchronized on Overview, Consistency and Trails. Definitions has its
own independent searchable metadata slicers. Use Desktop's slicer Search option
if the search box is not displayed initially.

Maintenance status comes from the latest exported snapshot, uses all source usage
on its equipment, and does not respond to the riding date/sport filters. Gear
selection does filter its components. The page labels this explicitly. It shows
per-component remaining intervals with units, avoiding an aggregate of hours/miles.

Overview cards show whole-activity totals; its weekly trend uses point miles.
Trail visuals use point mileage and assignment coverage, not unique trail completion.
Activities crossing local dates can contribute whole summaries to multiple contexts;
whole-activity rows across periods/partial routes are not always additive. Activity
start dates in the detail table are UTC; the report date slicer uses local point dates.
Strava URLs are measure values categorized as Web URL; enable URL icons or conditional
URL formatting in Desktop if needed. Activity IDs remain in the detail for unique rows.

## Published-model connection

The report preserves the `byConnection` definition from the merged blank
`power_bi/report/cycling_analytics.pbip`. It connects directly to the published `activity_tracking`
semantic model. The project, connection string and base theme remain unchanged;
this branch adds report pages, visuals, filters and a custom theme only. There is
no copied semantic model, local Parquet source or dataset recalculation required.

Sign in to Power BI Desktop with an account that can author against the published
model. The deployed model must include `Activity URL` and `data_dictionary` from the
merged dataset changes. If those fields are missing in Service, refresh and republish
the semantic model first. Publishing this report is a separate step from committing
these files.

## Desktop review

1. Close Desktop before checking out the branch; open `power_bi/report/cycling_analytics.pbip` and sign in for the published model.
2. Check every page renders, headers and tables fit, and the cycling filter is
   editable. Confirm date/equipment slicer selections carry between analysis pages.
3. Check a known activity, its link, local dates, inactive weeks, unmatched trails,
   and component service values. Confirm Definitions is unaffected by riding filters.
4. Refine chart density, table column widths, sort, URL icons, tooltips and fonts.
   Large history may need a bounded date selection before adding more detail.
5. Verify totals against the published Quanta Check and intended viewer access
   before publishing/sharing the report.

Static checks validate JSON schemas, model field bindings, page bounds, cycling
filter configuration and slicer groups. They do not execute report queries, verify
DAX or render visuals. The daily calendar heatmap, custom navigation, due-count
cards, drillthrough and a dedicated segment page are deferred from this draft.

## Branch validation

All four report-specific tests pass, and all 69 report/project JSON files validate
against Microsoft schemas. The full suite has 66 passes and two existing failures,
reproduced on unmodified `main` at `73107bc`: the field-parameter metadata-format
assertion and embedded dictionary freshness assertion. No semantic-model files are
changed in this report branch. Desktop rendering and live Service queries remain
manual checks.
