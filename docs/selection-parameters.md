# Dynamic measure and dimension selection

`select_measures` and `select_dimensions` are **Power BI field parameters**, not
calculation groups. They choose existing fields for a visual instead of rewriting
measure calculations. The committed older reference model did not contain these
selectors, so the implementation uses standard field-parameter metadata adapted
to the current dataset. Existing renamed measures and descriptions are preserved.

- `select_measures[selection]` offers all 59 current explicit measures, in their
  existing model order. Each retains its own calculation and numeric format.
- `select_dimensions[selection]` offers Year, Quarter Number, Month Number,
  Week Starting, Date, Activity Type, Activity Category, Gear, Trail System, Trail,
  Segment, Activity, and Activity ID.

Both tables are disconnected calculated tables in the semantic model. Their
hidden `fields` and `sort_order` columns provide field identity and ordering.
There are no SQL views, exports, source tables or new relationships for selectors.
The existing star and association bridge filter behavior are unchanged.

## Use in Desktop

Close Power BI, pull/check out this branch and reopen `activity_tracking.pbip`.
Refresh model metadata if needed. No database rebuild or Parquet export is required.

1. Add `select_measures[selection]` to a slicer and to the target visual's Values
   (or numeric axis).
2. Add `select_dimensions[selection]` to another slicer and to that visual's Rows
   (or category axis).
3. Configure both slicers as single-select for a simple chart. Start with Miles
   grouped by Gear. Switch to Activities, Moving Time, and Active Week % to check
   that the displayed field, title and number format follow the selection.
4. For matrices, multiple parameter choices can be useful. Multiple selected
   dimensions create grouping levels; multiple measures become separate values.

Power BI treats a cleared field-parameter selection as all choices, not none.
Single-select is recommended to avoid unintentionally requesting all 59 measures,
including full-history streak calculations, on every visual interaction.
Existing Quanta Check visuals are unchanged: add the parameters to a visual to
opt it into dynamic selection. A selector does not replace fields already on it.

## Scope cautions

Field parameters do not make incompatible calculation grains equivalent. Miles
uses selected GPS intervals; Whole Activity Miles uses full summaries for touched
activities. Segment grouping should use segment-aware measures such as Miles in
Selected Segments or Segment Efforts. Ordinary Miles does not acquire segment
filtering just because Segment is the chosen axis. Association measures still
use all verified history and ignore activity/date filters.

Month Number and Quarter Number combine the same number across years if selected
alone; use Year as an additional grouping level or constrain the date slicer to one
year. Week Starting uses an actual Monday date, avoiding that ambiguity. Activity
names may repeat; choose Activity ID when a unique grouping is required.

The visible label column is grouped with the hidden field-reference column as
required by field-parameter metadata. Keep that metadata when editing the tables.
When adding/renaming dataset fields, update parameter entries; static tests verify
all targets resolve. The standard NAMEOF references let Desktop track model field
renames when made through its model editor.

Static tests cover all bindings, ordinals, metadata, hidden columns and disconnected
relationships. Desktop still needs to validate actual field substitution, formats,
slicer behavior and connected-report support before merging.

## Refresh and field-parameter recognition

The hidden `fields` column on each selector has a JSON extended property named
`ParameterMetadata`, with value `{"version":3,"kind":2}` and explicit `type: json`.
That belongs on the field-reference column, not on the table or visible label.
The visible label already groups by `fields` and sorts by `sort_order`.

After importing new calculated selector tables, Desktop can show `#ERROR` rows
with a banner saying calculated tables must be manually refreshed. Reopen the
updated project and use Home > Refresh to process the calculated tables before
checking parameter behavior. Updating a property in an external editor alone does
not populate those tables. No SQL refresh or Parquet export is required.
If errors remain after a successful refresh, capture the refresh error details;
unprocessed tables and parameter recognition are separate issues.
