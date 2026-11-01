# Measure descriptions in Power BI

All 59 current dataset measures have native Description metadata in
`power_bi/gps/activity_tracking.SemanticModel/definition/tables/measures_.tmdl`.
TMDL represents that metadata with the `///` lines immediately above each measure.
These are native descriptions, rather than custom annotations that users would
need another tool to read.

Descriptions explain:

1. What is calculated and the units used.
2. Which filters apply, including whether partial routes select full activities.
3. Important interpretation limits: overlapping efforts, partial verification,
   catalog-wide associations, missing data, or date/streak behavior.

Close Power BI before pulling this branch, then reopen the project. Inspect a
measure's tooltip in the Data pane, or select it in Model view and read its
Description property. Descriptions are part of the semantic model and travel with
the published dataset; connected authoring clients can expose this metadata.
Exact tooltip presentation depends on the client/version.

No database rebuild, Parquet export or recalculation change is required. Measure
names, DAX expressions, display folders, format strings and lineage IDs are unchanged.
The older reference model is outside this change.

When adding or changing a measure, update its native description alongside its
calculation. Describe point totals, full-activity totals, whole-effort totals, and
historical association catalogs distinctly. Avoid describing every difference as
an error or treating match percentages as accuracy/completion scores.

For definitions inside report table visuals, use the [data dictionary](data-dictionary-pbi.md), which reads this native metadata on model refresh.
