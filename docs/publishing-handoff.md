# Dataset publishing handoff

## Review of existing coverage

| Handoff item | Repository coverage |
|---|---|
| Field definitions and types | [Data dictionary](data-dictionary.md); machine contract in `src/reporting/gps_schema.json` |
| Metric definitions | [Measure library](measure-library.md), [native descriptions](measure-descriptions.md), [daily/weekly consistency](activity-consistency.md) |
| Grain, keys and filters | [GPS schema](gps-schema.md), [association bridge](segment-trail-associations.md), dictionary below |
| Validation | [Quanta Check](quanta-check.md), offline audit and release record below |
| Refresh and ownership | Manual runbook below; operator records the actual owner/workspace |
| Report scope | [Report outline](report-outline.md); proposed starting scope |

This review documents repository behavior. It does not certify a current populated
snapshot or Power BI Desktop/Service execution. Historical example totals in Quanta
Check are not release targets.

## Ownership and operating policy

Refreshes are manual while the current local Parquet workflow is in use. The
repository maintainer operates ETL/export and the semantic-model publisher operates
Desktop refresh/publish; one person can fill both roles. Record the actual operator,
workspace, model and time for each release below. No refresh SLA or unattended
schedule is assumed. Replacing Parquet alone will not establish automation: source
access, credentials, scheduling and failure handling also need configuration.

Flow: Strava API → Python ETL → SQLite → 11 Parquet files → imported Power BI model
→ connected reports. Database files and exports are ignored by Git; a branch pull
does not deliver refreshed data. `ExportFolder` currently uses a local Windows path.

## Manual refresh (from repository root)

Close Desktop before switching branches/pulling model changes. Do not run imports,
rebuilds, verification or exports concurrently. Preserve a known-good database and
complete export folder before a release; use SQLite's backup API for a live database
([migration preparation](gps-schema.md#prepare-a-local-working-database-before-migration)
provides a backup helper when preparing a migration).

For new Strava data, with the local environment/credentials configured:

```powershell
.\.venv\Scripts\python.exe -m src.main
```

The pipeline already rebuilds point reporting and exports Parquet. Inspect its
retrieved/failed/deferred/rate-limit counts as well as the final export result;
a successful export does not prove all remote history was enriched.

If SQLite is already current and only exports are needed:

```powershell
.\.venv\Scripts\python.exe -m src.tools.export_power_bi
```

For intentional point/spatial rule changes, use the separate rebuild instructions
in [GPS schema](gps-schema.md), then export. For view-only association installation,
use [association setup](segment-trail-associations.md#apply-locally). A routine
refresh does not require repeating historical timezone/stream backfills.

After database work is finished, run the offline audit against that same snapshot:

```powershell
.\.venv\Scripts\python.exe -m src.tools.validate_point_reporting
```

Confirm all **11** default view exports succeeded. Export files replace individually,
not as an atomic set: a failed/interrupted export can leave mixed generations.
Keep Desktop closed until all succeed; resolve failures and rerun the full export.
Do not refresh/publish a partial set. Preserve the previous complete set for recovery.

Open `power_bi/gps/activity_tracking.pbip`, set `ExportFolder` to the complete local
export directory with a trailing slash, and refresh in Desktop. Review Quanta Check
unfiltered, then known activities, local dates, trails and repeated segment efforts.
Changing SQLite or Parquet alone does not update the imported model.

## Validation and publication gate

- Require this run's `exports/validation/audit_status.json` to say `completed`,
  and inspect its timestamps; previous summary files can survive failed runs.
- Require `duplicate_point_keys` and every `orphan_dimension_keys` value in
  `summary.json` to be zero. These are the offline audit's structural failure checks.
- Record GPS activity/point counts, local date coverage, UTC fallback count,
  interval-quality and matching distributions. Review NULLs/blank members and
  changes from the previous release; optional telemetry and unmatched trails are
  not automatically errors. Zero UTC fallback is the goal; explain exceptions.
- Reconcile `activity_mileage.csv`, `trail_mileage.csv` and
  `trail_system_mileage.csv` to Quanta Check on the same unfiltered snapshot.
  Review large source/point differences without forcing equality. Activity CSV
  source totals are unrounded conversions; activity-view totals round each activity.
- Validate DAX, slicers, local midnight, week/year boundaries, trail partial filters,
  segment unions and whole-activity behavior in Desktop. Python tests do not execute DAX.
- Record remaining alignment coverage and spatial limitations. Use the optional
  offline [segment coverage audit](segment-trail-associations.md#diagnose-low-association-coverage-before-changing-tolerances)
  when segment reports are planned. Do not represent matching coverage as accuracy
  or trail completion.

Publish the GPS shared semantic model with Quanta Check to the intended workspace
through Power BI Desktop after the checks pass. Record its workspace/model identity.
Build subsequent thin reports against that published model; the repository's
`byPath` connection is for local development. Verify the deployed report's totals
and access using the intended viewer account before sharing broadly.

For now, refreshing in Desktop and republishing is the manual update route. A
Service-side manual refresh also needs a configured reachable source/gateway and
credentials for these local files; clicking Refresh in Service cannot reach a
personal `C:\...` path by itself. Parquet can support other arrangements, but this
repo does not configure one. Record any such deployment configuration separately.
If validation fails, retain the previous published model and restore the complete
known-good local export set if needed. Avoid overwriting a good deployed model.

## Release validation record (copy for each publication)

Store the completed record and private audit artifacts with the release/operator's
records. Do not commit GPS rows, activity-name CSVs or credentials to Git.
Unfilled entries mean pending validation, not a pass.

| Evidence | Value / result |
|---|---|
| Git commit / branch | Pending |
| ETL/export operator and publication owner | Pending |
| Refresh/export timestamp with timezone | Pending |
| All 11 exports successful; audit status and timestamp | Pending |
| Source activities / GPS activities / GPS points | Pending |
| Earliest/latest local modeled date | Pending |
| Duplicate point keys / orphan counts by key | Pending |
| UTC fallback count and accepted exceptions | Pending |
| Point miles / rounded whole-activity miles / difference | Pending |
| Missing telemetry, interval quality, unmatched trail/system review | Pending |
| Segment verification/association coverage and limitations | Pending |
| Desktop refresh, DAX and interaction checks | Pending |
| Known-route/source reconciliation and accepted differences | Pending |
| Target workspace / semantic model / connected reports | Pending |
| Deployed totals and viewer-access check | Pending |
| Known-good backup/export location and release decision | Pending |
