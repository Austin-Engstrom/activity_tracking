# Segment PR and KOM data

This adds ETL and shared-model tables for a future segment PR page. It changes no
report pages or visuals.

## Tables and meaning

| Reporting table | Grain | Scope |
|---|---|---|
| segment_effort_achievements | One stored effort | Latest stored reported PR/KOM ranks, retrieval time, availability status, elapsed/moving seconds, local start date and Strava links |
| segment_personal_bests | One segment with an eligible effort | Fastest known stored GPS effort, chosen activity/time/date, tie count and stored/eligible effort counts |

The source `segment_efforts` table already has `pr_rank` and `kom_rank`; those fields
are now exposed with new provenance rather than adding a second copy of effort
facts. `segment_effort_record_metadata` stores the latest response retrieval time
and whether each rank field was returned. `segment_record_refresh` tracks successful
and failed activity refreshes, including completed responses with no efforts.

These are **latest snapshots**, not an append-only change history. Efforts on many
past activities are retained, but re-fetching an activity updates its current stored
ranks rather than preserving every earlier API observation.

`reported_pr_rank` and `reported_kom_rank` mean what Strava returned for that effort
when retrieved. Rank 1 is the reported first position; higher ranks are ranked
achievements, not KOM wins. This is neither a certified historical leaderboard on
the activity date nor current crown ownership. Activity date and retrieval time
are separate. No leaderboard scraping, segment-leaderboard endpoint or subscription
bypass is introduced.

Rank status distinguishes:

- `ranked`: field returned with a positive rank.
- `no_rank`: field explicitly returned with null.
- `not_returned`: API omitted the field; availability is unknown.
- `legacy_unobserved`: existing stored rank with no new retrieval provenance. The
  raw rank is preserved, but no retrieval timestamp is invented from created/updated
  dates. The observed-first flags remain null until the field is observed.

The best-effort view ranks **elapsed seconds**, not moving seconds. It excludes
nonpositive elapsed times and explicitly hidden efforts. Equal times choose the
oldest effort UTC timestamp, then lowest effort ID; `tied_best_effort_count` records
all eligible ties. Segments with no eligible effort have no best row. Hidden/zero-time
entries remain visible in the effort table and stored count. This is an imported
history best, not an official lifetime PR: missing activities, source changes,
hidden efforts and different sport types sharing a segment can affect the result.
Never interpret repeated segment distance as unique physical coverage.

Both views require GPS points on the parent activity. All its stored efforts then
qualify for the effort view, without requiring verified original stream links or
trail assignment. One source effort can overlap another; do not sum effort totals
to get route totals. Effort date keys use Strava's local effort start when available,
otherwise UTC; `date_basis` makes that fallback explicit. This differs from the
point-date convention for activity totals spanning midnight. Rare dates outside the
modeled point calendar appear as blank calendar members; inspect effort_local_date
and date_basis when validating historical coverage.

## Apply locally

Close Desktop and stop concurrent ETL jobs. Back up the populated local SQLite
with the existing backup workflow before adopting ETL changes. The cloud checkout
used for development has no populated source history; Git does not deliver data.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.tools.build_segment_records
.\.venv\Scripts\python.exe -m src.tools.backfill_segment_records --dry-run --limit 25
```

The first command creates only additive metadata/state tables and installs the two
views without a GPS/spatial rebuild. Repeating it is safe. Migration-managed users
can apply Alembic revision `20261101_segment_records` from the existing GPS revision;
do not stamp unknown databases. The normal database initializer also creates the
new tables, so existing local workflows need no manual ALTER of source efforts.

Ranks already stored in historical efforts and fastest-known times are immediately
available, initially with `legacy_unobserved` provenance. To refresh a bounded batch
with local Strava credentials:

```powershell
.\.venv\Scripts\python.exe -m src.tools.backfill_segment_records --limit 25
```

Rerun to resume. Each selected activity makes one detail request with
`include_all_efforts=true`; normal OAuth authentication is additional. The client
respects read capacity/429 stops. Previously completed activities are skipped;
untouched activities are prioritized ahead of failures. A failed or malformed
response rolls back that activity without erasing its prior effort data. Missing
or null effort arrays are rejected; an explicitly returned empty array is a valid
replacement. The command exits nonzero for failed activities, prints counts, and
records successful progress per activity. A rate-limit stop reports deferred work
and is safe to resume. Do not run concurrent backfills or imports on this database.

To revisit old snapshots, or force specific known GPS activities with stored efforts:

```powershell
.\.venv\Scripts\python.exe -m src.tools.backfill_segment_records --limit 25 --refresh-before 2026-11-01
.\.venv\Scripts\python.exe -m src.tools.backfill_segment_records --limit 1 --activity-ids 20796076161
```

`--refresh-before` accepts a naive UTC ISO date/time. The ID command refreshes only
eligible locally stored activities; it does not import a missing activity. The
backfill targets stored efforts. The regular `src.main` detail enrichment captures
provenance on new activities, including returned empty effort arrays, and rebuilds
these views/exports normally. No resetting of `detail_loaded_at`, no extra stream
reads and no point rebuild are needed for a historical rank refresh.

After backfill, generate the new exports:

```powershell
.\.venv\Scripts\python.exe -m src.tools.export_power_bi --views view_segment_effort_achievement view_segment_personal_best
```

The default full export also includes both (16 current model views). Empty and
all-null fields use explicit Parquet types. Open the GPS dataset PBIP, refresh and
verify the new tables, then republish the shared semantic model before authoring a
PR page in the connected report. The native descriptions are included in the
regenerated embedded data dictionary. The two new Parquet files must exist before
refreshing this model revision.

## Model filter behavior

The effort table has single-direction dimension filters from segments, activities,
gear, activity_types and dates. It uses **effort-start dates** and whole effort
values. Trail/system filters do not filter this table, and no new bidirectional
relationships or point-to-effort paths are added.

The best table relates only to segments: it represents all imported GPS history.
Date, activity, gear and sport filters do **not** recompute the fastest-effort row.
Keep its lifetime scope visible on a future PR page. A fastest-in-selected-period
measure would be a separate calculation over the effort table. The best table's
activity key is a reference, not an active relationship.

## Validation

A bounded live check of activity 20796076161 returned nine efforts; all nine included
PR and KOM rank fields, two had positive PR ranks, and none had positive KOM ranks.
Only aggregate field availability was inspected; no live payloads or credentials
are committed. This verifies availability for that activity, not full-history
completeness or crown ownership.

Offline tests cover normal detail ingestion, missing-vs-null ranks, legacy rows,
atomic rejection, duplicate/mismatched IDs, reruns/stale metadata, empty responses,
rate limits, retry priority, refresh cutoffs, GPS scope, hidden/invalid times,
deterministic ties and populated typed exports. Review at least one known PR/KOM
effort against Strava locally, and verify field/relationship behavior in Desktop.

The 23 targeted ETL/export/dictionary/migration checks pass. The full suite also
reports four existing failures reproduced on unmodified main at b1c4d1b: three
report assertions about Desktop-normalized filter/start properties and one
field-parameter metadata-format assertion. This branch leaves those report files
and unrelated metadata unchanged.
