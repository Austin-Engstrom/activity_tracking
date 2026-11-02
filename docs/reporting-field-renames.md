# Reporting field names, durations and local time

This revision changes the active GPS semantic model and updates the tracked Activity Analytics and Quanta Check report bindings. It includes the personal-rank/time/top-10 measures on this branch. Service component columns, hours and mixed schedule units remain unchanged.

## Naming convention

Numeric duration columns use seconds; distance columns use miles. Display measures use MM:SS below an hour and HH:MM:SS at or above an hour. Source UTC instants and operational retrieval timestamps retain explicit `_utc` names; they are audit fields, not local dates. Elevation/speed/temperature units remain explicit.

| Table | Previous model field | New model field |
|---|---|---|
| `activities` | `activity_date` | `date` |
| `activities` | `activity_date_key` | `date_key` |
| `activities` | `start_date` | `started_at` |
| `activities` | `start_date_utc` | `started_at_utc` |
| `activities` | `distance_miles` | `distance` |
| `activities` | `moving_time_seconds` | `moving_time` |
| `activities` | `elapsed_time_seconds` | `elapsed_time` |
| `activities` | `moving_time_minutes` | `moving_time` |
| `activities` | `elapsed_time_minutes` | `elapsed_time` |
| `activity_points` | `elapsed_time_seconds` | `elapsed_time` |
| `activity_points` | `cumulative_distance_miles` | `cumulative_distance` |
| `activity_points` | `incremental_distance_miles` | `incremental_distance` |
| `activity_points` | `incremental_time_seconds` | `incremental_time` |
| `activity_points` | `moving_time_seconds` | `moving_time` |
| `gear` | `distance_miles` | `distance` |
| `gear` | `created_at` | `created_at_utc` |
| `gear` | `updated_at` | `updated_at_utc` |
| `gear` | `detail_loaded_at` | `detail_loaded_at_utc` |
| `segments` | `distance_miles` | `distance` |
| `trails` | `length_miles` | `length` |
| `segment_efforts` | `elapsed_time_seconds` | `time` |
| `segment_efforts` | `moving_time_seconds` | `moving_time` |
| `segment_efforts` | `distance_miles` | `distance` |
| `segment_effort_achievements` | `effort_started_at` | `started_at` |
| `segment_effort_achievements` | `effort_started_at_utc` | `started_at_utc` |
| `segment_effort_achievements` | `effort_local_date` | `date` |
| `segment_effort_achievements` | `elapsed_time_seconds` | `time` |
| `segment_effort_achievements` | `moving_time_seconds` | `moving_time` |
| `segment_effort_achievements` | `distance_miles` | `distance` |
| `segment_effort_achievements` | `ranks_retrieved_at` | `ranks_retrieved_at_utc` |
| `segment_effort_achievements` | `eligible_for_stored_best` | `eligible_for_pr` |
| `segment_personal_bests` | `best_segment_effort_key` | `pr_effort_key` |
| `segment_personal_bests` | `best_activity_key` | `pr_activity_key` |
| `segment_personal_bests` | `best_effort_started_at` | `pr_started_at` |
| `segment_personal_bests` | `best_effort_started_at_utc` | `pr_started_at_utc` |
| `segment_personal_bests` | `best_effort_local_date` | `pr_date` |
| `segment_personal_bests` | `best_elapsed_time_seconds` | `pr_time` |
| `segment_personal_bests` | `best_moving_time_seconds` | `pr_moving_time` |
| `segment_personal_bests` | `best_distance_miles` | `pr_distance` |
| `segment_personal_bests` | `tied_best_effort_count` | `pr_tie_count` |
| `segment_personal_bests` | `best_basis` | `pr_basis` |
| `segment_personal_bests` | `ranks_retrieved_at` | `ranks_retrieved_at_utc` |
| `segment_trail_associations` | `observed_distance_miles` | `distance` |
| `segment_trail_associations` | `first_observed_at` | `first_observed_at_utc` |
| `segment_trail_associations` | `last_observed_at` | `last_observed_at_utc` |

The map in `src/reporting/gps_model_columns.json` records physical-export to semantic-model aliases. Power Query applies those aliases before loading the model. Existing renamed columns retain their lineage IDs. Activity moving/elapsed source durations now export exact seconds rather than rounded minutes; source activity storage and the retained `view_activity_all` legacy view are unchanged.

## Duration display

Raw duration columns are hidden numeric fields for calculations and sorting. Use the display measures for cards and detail tables: Activity Moving Time, Activity Elapsed Time, Point Moving Time, Point Elapsed Time, Segment Effort Time, Segment Effort Moving Time, Segment PR Time and Segment PR Moving Time. Average Activity Moving Time and Total Segment Moving Time support aggregate display.

Examples: 75 → 01:15; 3599 → 59:59; 3600 → 01:00:00; 5025 → 01:23:45. Numeric hour measures remain available for existing analytical axes, service durations remain hours, and Seconds Behind Segment PR remains a numeric difference without a leading plus sign. Text duration labels should not be used as numeric chart axes or sort keys.

## Timezone handling

1. Prefer a valid Strava IANA timezone from point_reporting_metadata.
2. Otherwise find the timezone offline from the first valid GPS coordinate in original stream order.
3. If neither is available, local event timestamps/date keys remain NULL and timezone provenance is unresolved. An existing source-local effort timestamp can still supply its known local effort date.

The first-point timezone applies throughout the activity, matching an activity-local reporting convention even if the route crosses timezone borders. Historical ZoneInfo rules convert UTC instants; stored offset intervals split at daylight-saving changes, including half-hour transitions. `date_basis` and `timezone_name` expose provenance. Original activity/effort UTC timestamps, point UTC timestamps and API retrieval instants remain available as explicit audit fields.

Local activity/point/effort timestamps export as timezone-naive wall-clock timestamps; UTC audit fields export with UTC timezone metadata. Local dates are calendar dates. Point date-key corrections do not change coordinates, mileage, spatial assignments or source timestamps. Missing time or timezone can be checked with Unresolved Local Time Points and the audit summary unresolved_local_points.

## Apply locally

Close Power BI and save/commit manual report edits before checking out this revision. Back up the populated SQLite database using the existing backup workflow. From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.tools.refresh_reporting_model
.\.venv\Scripts\python.exe -m src.tools.validate_point_reporting
.\.venv\Scripts\python.exe -m src.tools.export_power_bi
```

This adds two derived timezone tables and rebuilds reporting views; it does not rebuild GPS/spatial matches or call Strava. `timezonefinder` uses bundled boundary data locally. On migration-managed databases the additive Alembic revision is 20261102_reporting_local_times; do not stamp an unknown database. The normal initializer also creates the tables idempotently. Normal GPS rebuilds and exports keep timezone metadata up to date.

A **full export is required** for the new local fields and activity duration schema. Verify all 16 exports succeed before opening Desktop; do not mix old/new files. Open the GPS PBIP, refresh/recalculate, inspect descriptions, and republish activity_tracking. Then reopen the updated Activity Analytics PBIP. Other reports outside this repository must update their old field bindings before using the renamed published model.

## Validation

Checks cover source-clock preservation, UTC/local Arrow types, exact source seconds, Strava precedence, first-valid-point fallback, invalid/unresolved zones, repeated refreshes, spring-forward, fall-back and a half-hour DST transition. Model/export alias checks, measure references and saved report bindings cover the naming changes. Repository tests cannot execute DAX or render Desktop visuals; verify the formatted durations, local dates and service-hour values in Desktop before merging/publishing.
