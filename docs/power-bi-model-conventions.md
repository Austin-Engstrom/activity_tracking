# Power BI model conventions

Apply these conventions to the active model under `power_bi/gps` when adding or
updating TMDL. The older model under `power_bi/dataset` is retained as legacy.

- Hide foreign keys, including keys used by measures without a physical relationship.
  Keep identifiers non-summing. Dimension primary keys remain visible for diagnostics.
- Expose descriptive attributes on their owning dimension. Hide copies on facts:
  for example, use `gear.gear_name` and component attributes from `gear_components`.
- Format ratio percentages as `0.0%`. Values already on a 0–100 scale, such as
  grades and service percent used, use `0.0\%` so formatting does not multiply them
  by 100. Formatting never changes stored values.
- Show binary flags and category codes with `0`, without decimals or aggregation.
  Show counts with `#,0`, distances and hours with `#,0.00`, seconds with `#,0.0`,
  and heart rate, cadence, watts, calories, and elevation with `#,0`.
- Show coordinates with six decimals and no default aggregation. Indexes and
  calendar attributes also must not default to sums.
- Show dates as `yyyy-mm-dd`, and timestamps as `yyyy-mm-dd hh:mm:ss`.

Keep field names and source columns stable so existing DAX and report bindings
continue to work. Hidden fields remain available to existing visuals and measures.

The user-approved [field naming migration](reporting-field-renames.md) uses concise duration/distance names, numeric seconds underneath formatted duration measures, local event dates, and explicit UTC audit names. Service hours/mixed schedule units remain explicit. Update all tracked DAX/report bindings and the alias contract together when changing a published field.
