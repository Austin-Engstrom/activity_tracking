# Segment PRs by trail and trail system

This is a separate report/model change following the field-name/local-time update.
The branch is based on the merged naming/local-time update on `main`. It introduces no ETL, Parquet fields or relationships.

The Segment PRs page adds searchable **Trail system** and **Trail** dropdowns.
The five compact slicers share one row: date, category, system, trail and segment. Choose a system, then optionally a named trail. The segment dropdown, effort history,
all-history best table, PR/KOM first counts, observed-rank coverage and trend follow
the matching segment set. Clearing both geographic selectors restores all segments,
including segments that have no association evidence.

The existing `segment_trail_associations` bridge supplies the matching IDs across
verified imported history. Systems can include system-only observations whose trail
is unknown; the named-trail dropdown excludes blank trail names. A system selection
limits the trail choices to associated trails through the catalog association count.
The filter does not rely on segment-name matching and does not add bidirectional
relationships or an ambiguous path through GPS points.

This is **historical segment association**, not proof that each effort was matched
to the selected trail. A segment spanning multiple trails can appear under each.
Unverified index history, missing geometry or ambiguous assignments can leave valid
segments unassociated. Empty filtered results are not proof that no activity/PR
exists there. Use the existing segment-coverage audit if expected associations are
missing; the new filter does not widen spatial tolerances or infer matches.

Date and category filters still apply to upper effort history and achievement
summaries. Personal rank and the current PR baseline stay all-history comparisons
within each selected segment. The bottom best table stays across all dates and
categories, but now shows only segments associated with the geographic selections.
Association catalogs themselves are all-history and do not shrink with date/category
filters. Explicit source-rank coverage is separate from association completeness.

`Recorded Segment Efforts`, `Reported PR Firsts`, `Reported KOM Firsts` and
`Segments With Stored Best` use the selected association IDs with KEEPFILTERS/TREATAS.
Coverage, pending counts and KOM Top 10 inherit this through the base effort count.
The `Segment Matches Trail Selection` measure gates rows on both tables and segment
slicer; preserve that visual filter when editing/copying these visuals. Effort and segment keys stay as hidden query projections to distinguish duplicate names and preserve row grain; key columns are not displayed.

Refresh/recalculate and republish the GPS model for the updated/helper measures,
then reopen Activity Analytics. No additional export is needed after the prerequisite
naming/local-time migration has been applied. The dark styling, page dimensions,
shared date selection and native descriptions/dictionary are retained.

In Desktop, verify a known system/trail, a system-only observation, a segment spanning
multiple trails, clearing the selectors, and the expected partial-data/empty cases.
Confirm cards and detail rows agree, and verify changing dates does not recompute the
selected segment's all-history personal rank or PR time. Static checks cover bindings,
selector fields, membership gates, DAX reference targets and layout; they do not
execute DAX or validate the quality/completeness of spatial associations.

Validation: 30 targeted checks pass. The full suite has 100 passes and the existing field-parameter metadata-format failure. Desktop interaction and DAX evaluation remain manual validation.

## Segment path and table layout

A map beside the trend chart replaces the note panel. Select a single segment in
the segment slicer or a segment table row to display exact GPS coordinates linked
through the verified activity_point_segments membership bridge. It shows small
fixed markers following the sampled route, preserving gaps instead of drawing
invented connecting lines. Date/category/equipment/trail point filters still apply.
No verified memberships or no unique identifiable segment means a blank map; a
Strava rank observation by itself does not establish verified point alignment.
Large point sets remain subject to Azure Maps reduction; narrow dates if needed.

The upper full-width table shows segment name, distance, date, formatted effort
time, seconds behind PR, all-history personal rank and activity link. The lower
full-width table shows segment name, distance, PR date, formatted PR time,
Recorded Segment Efforts, stored_effort_count and activity link. The recorded
count here uses Segment Efforts All Time, so it agrees with the all-history stored
count and does not manufacture zero-valued blank rows under a date filter. Internal
key projections remain hidden for row identity. Refresh/recalculate and republish
the model for the two new measures; no additional Parquet export is needed.
