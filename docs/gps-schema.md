# GPS reporting schema

The reporting fact is one valid GPS sample, unique by `(activity_id, point_index)`.
Source activities, streams, gear, segments and geometry are retained; `activity_points`
is an atomically replaceable derived table. Source IDs are stable dimension keys;
we do not create redundant copies of source entities just to rename them dimensions.
Components and non-GPS reporting are outside this model.

```mermaid
erDiagram
 activities ||--o{ activity_points : activity_key
 gear ||--o{ activity_points : gear_key
 activity_types ||--o{ activity_points : activity_type_key
 dates ||--o{ activity_points : date_key
 trails ||--o{ activity_points : trail_key
 trail_systems ||--o{ activity_points : trail_system_key
 segments ||--o{ segment_efforts : segment_key
 segment_efforts ||--o{ activity_point_segments : segment_effort_key
 activity_points ||--o{ activity_point_segments : point_membership
```

The last relationship is logical, not an active bidirectional Power BI relationship.
The segment-aware mileage measure uses TREATAS to filter distinct point keys,
preventing overlapping segments and repeated efforts from duplicating point mileage.
Segment effort durations remain effort-level measures.

| SQL view | Power BI table | Grain |
|---|---|---|
| view_activity_points | activity_points | GPS sample |
| view_activity | activities | GPS activity |
| view_gear | gear | equipment |
| view_activity_type | activity_types | sport type |
| view_date | dates | point calendar date |
| view_trail | trails | normalized trail |
| view_trail_system | trail_systems | confirmed or candidate system |
| view_segment | segments | Strava segment |
| view_point_segment_effort | segment_efforts | Strava effort |
| view_activity_point_segments | activity_point_segments | point/effort membership |

## Measurement contract

Source storage retains Strava metric units. Reporting exposes miles, feet, mph,
Fahrenheit, seconds, bpm, rpm, watts and percent. Point increments are not rounded.
Activity totals remain Strava totals on `activities`; do not sum them through a
point join. `Whole Activity Miles` sums each selected activity once. Normal miles
sum point increments and can differ from Strava totals due to excluded/invalid
intervals, GPS filtering, or Strava's processing. Do not allocate the difference
silently. The first point has no preceding interval and its increments are NULL.

Increments are calculated against the original preceding stream sample, before
GPS filtering. Missing coordinates, nonpositive elapsed increments, negative
cumulative distance increments, and gaps over 60 seconds produce NULL increments
and a quality flag. Valid zero-distance intervals retain their elapsed time.
Moving seconds use Strava's moving flag at the interval endpoint.

Point timestamps are UTC start time plus stream elapsed seconds. New activity
imports capture Strava's IANA timezone in `point_reporting_metadata`. Historical
activities without it explicitly use UTC (`date_basis=utc_fallback`); reimport or
populate verified IANA metadata before relying on local-day comparisons.
Dates span the minimum through maximum point date. Empty datasets have no dates.

## Spatial contract

Only confirmed polygons assign systems. Boundary points are included (`covers`).
Overlaps choose the lowest system ID and expose `boundary_overlap_lowest_id`.
Unmatched keys are NULL (Power BI blank member), never fabricated matches.
Geometry must be valid WGS84 longitude/latitude; invalid geometry fails the rebuild.

Trail matching uses an activity-local azimuthal equidistant projection, nearest
trail within 40 feet in the assigned system. If two candidates are within 10 feet
of one another in distance, leave the trail unmatched and flag ambiguity. This is
an initial proximity model, not directional map matching; parallel trails require
real-route review. Distance is attributed to the interval's ending point; intervals
crossing boundaries are not split. Tolerances are configurable rebuild parameters.

Segment membership uses inclusive original start/end stream indexes. Only streams
whose time and GPS metadata prove original size and time-series alignment are
linked. Historical arrays lack this evidence and remain unlinked until refreshed.
Efforts and segment attributes remain visible even without point membership.

## Build and cutover

From the repository root:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m src.tools.rebuild_point_reporting
.venv/bin/python -m src.tools.export_power_bi
.venv/bin/python -m unittest discover -s tests/unit -v
```

The normal `src.main` pipeline also rebuilds points after stream loading.
`initialize_database` creates the additive tables on existing/fresh databases;
Alembic revision `20261031_gps_points` provides the same additive schema for
already migration-managed databases. Do not stamp an unknown historical database.
The pre-existing baseline migration cannot bootstrap source tables from scratch.

Back up a populated SQLite database with SQLite's backup API before cutover.
No source tables are dropped. `view_activity_all` preserves the old activity scope.
Canonical activity/date/segment/trail-system views now follow the new model, so existing report
relationships and date columns require migration. The original Power BI project
is retained as a reference; use the new model under `power_bi/gps` for cutover.
Set its `ExportFolder` M parameter to the local Parquet directory (trailing slash).
Open `power_bi/gps/activity_tracking.pbip` in Power BI Desktop. The starter report
has a blank canvas; the model and initial measures are ready for new visuals.
Desktop rendering and refresh must be verified on a supported Windows machine.

The new model uses single-direction dimension-to-point relationships. It avoids
competing paths through activity, trail and system dimensions. Filtering segments
requires the explicit segment-aware mileage measure; ordinary mileage intentionally
does not respond to disconnected point-membership filters. Component tracking and
legacy progress measures are not included.

Before retiring the old report, reconcile several known routes, all point-key and
dimension-key cardinalities, boundary crossings, trail ambiguity, repeated segment
efforts and import reruns. Benchmark a full history: current rebuilding is per
activity and tests all system polygons/candidate trails; very large trail catalogs
will need spatial indexing and incremental invalidation. No accuracy or full-history
performance claim is made from synthetic tests alone.

The default export contains the ten GPS-model views. Use `--include-legacy`
to also export the six retained legacy views; legacy maintenance exports require
the existing maintenance-table initializer. Geometry and source data are not
removed by the cutover. Rebuild thresholds are exposed as `--max-gap-seconds`,
`--tolerance-feet`, and `--ambiguity-feet`.

### Prepare a local working database before migration

Close ETL jobs and database connections. In your local Fork checkout, run:

```powershell
.\.venv\Scripts\python.exe -m src.tools.prepare_migration_database
```

This backs up the current database under `database/backups/` and replaces
`database/strava_analytics.db` with a verified SQLite working copy. To use a
populated database stored elsewhere, add `--source "C:\path\existing.db"`.
The previous destination is backed up before replacement, and the source remains
unchanged. Both databases and backups are Git-ignored; pulling the branch brings
the helper, not cloud data. Then run the reporting rebuild and export commands.

### Validate populated data and verify historical segment indexes

After rebuilding, run locally:

```powershell
.\.venv\Scripts\python.exe -m src.tools.validate_point_reporting
.\.venv\Scripts\python.exe -m src.tools.validate_point_reporting --verify-streams --limit 5
```

The first command is offline and writes `exports/validation/summary.json` plus
activity-mileage, trail-mileage, and trail-system-mileage CSVs. It checks duplicate
point keys and non-null dimension references, and reports interval quality,
matching outcomes, and timezone fallbacks. Mileage differences are reported for
review, not declared failures: filtering uncertain intervals can legitimately
reduce point mileage. CSVs contain activity names; review before sharing them.

The second command requires local Strava credentials. It fetches original time and
GPS arrays for a bounded batch and compares every stored sample's index, time, and
coordinates. It requires original-size metadata, compatible series types, and valid
effort index bounds. It changes only alignment/check metadata, never source streams
or efforts. Mismatched or resampled streams remain unlinked for investigation.
Verification attempts are recorded locally so untouched activities are prioritized
on subsequent runs. Verified activities are skipped; API rate limits stop the batch
without discarding completed checks. Each activity needs one stream API read, plus
OAuth authentication. Increase the batch size only within your Strava limits.

The bridge view reflects successful verification immediately; no spatial rebuild
is necessary. Re-export Parquet after verifying links. Then review several known
routes in Power BI, including rides spanning systems and repeated segments, before
merging. Static audits do not establish spatial matching accuracy or validate DAX
execution in Power BI Desktop.

### Audit progress and query timings

Use `--explain` to capture SQLite query plans:

```powershell
.\.venv\Scripts\python.exe -m src.tools.validate_point_reporting --explain
```

Each step prints START and COMPLETED messages immediately, with elapsed seconds.
While a long SQLite query executes, a progress-handler heartbeat prints roughly
once every five seconds. Heartbeats indicate SQLite work, not a percentage or ETA;
waiting on a database lock may not emit them. `audit_status.json` is updated during
the run and records step timings and completed/failed/interrupted state.
`query_plans.json` contains plans when `--explain` is used. CSV files are published
after each finishes. Check this run's status/timestamps when older results exist.
Do not run concurrent audits into the same output folder; use `--output` to separate
runs. Ctrl+C is safe for the offline audit; incomplete TEMP tables are discarded
when the connection closes and source database records are unchanged.

The audit materializes each dimension's distinct keys once into indexed TEMP
tables and checks grouped point counts against them. This avoids the original
correlated date-reference query, whose plan could regenerate the recursive calendar
and scan point date bounds for each point. Point mileage/key groups are calculated
once and reused across the reference checks and CSV summaries. The grouping retains
point counts so an orphan shared by many points is counted correctly.

### Investigate activity mileage differences

Run the read-only diagnostic for the five migration outliers:

```powershell
.\.venv\Scripts\python.exe -m src.tools.diagnose_activity_mileage
```

Or choose activities with `--activity-ids 3783144977 3014709305`. No network access
or GPS rebuild is needed. Output goes to
`exports/validation/mileage_diagnostics/summary.json` and one interval CSV per
activity. It reports original stream indexes, elapsed-time and cumulative-distance
changes, observed stored increments, missing coordinate endpoints, gap durations,
distance resets, first/last GPS coverage, and activity-total versus stream-end
differences. The CSVs omit coordinates but contain activity identifiers; the summary
also includes activity names.

Excluded distance is signed: distance resets can make it negative. Missing distance
values remain unknown, not zero. A single GPS point has no measurable interval and
keeps its point mileage NULL. The first sample's cumulative distance and the source
minus stream-end difference are exposed separately, rather than attributed to a
trail without evidence. Hypothetical 60/120/300-second and unlimited-gap totals show
sensitivity to gap rules while still requiring valid endpoint coordinates, positive
time, and nonnegative distance. These are diagnostic comparisons, not recommended
reporting totals. `--gap-seconds` changes reason labels only; stored mileage and
schema are never changed by this command.

### Power BI null-type refresh errors

GPS exports use the explicit contract in `src/reporting/gps_schema.json` so empty
or entirely null columns retain a concrete Arrow/Parquet type. Power Query also
applies explicit column types matching the semantic model. Keep this contract,
SQL views and TMDL columns synchronized; tests check their model correspondence.
Legacy/ad-hoc exports still use inference.

If Desktop reports `'dataType' argument cannot be null`, cancel the failed apply,
close the project without saving failed local model edits, pull the latest branch,
and regenerate Parquet using `python -m src.tools.export_power_bi`. Reopen the GPS
PBIP, set the `ExportFolder` text parameter, and apply/refresh again. No database
rebuild is needed. If the error persists, collect Desktop's Copy details text;
Parquet typing is validated offline, but Desktop refresh itself requires Windows
validation and this message can have other causes.
