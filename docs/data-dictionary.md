# Exported data dictionary

Scope: the 11 GPS-model exports. Field names/types follow `src/reporting/gps_schema.json`; SQL under `sql/views/` defines exact transformations. Technical types are `string`, `int64`, `double`, and `dateTime`; calendar date fields are physically Parquet date32, timestamps UTC. NULL means unknown/not applicable unless a definition specifies otherwise; it is not automatically zero. Unmatched trail/system keys are NULL. Source telemetry and detail attributes can be missing. IDs/keys are categorical, never summed.

Relationships are single-direction dimension → fact. There is no active point → membership relationship; segment-aware DAX transfers distinct point keys. Association history is filtered by segments/trails/systems, not dates/activities/gear. See [GPS contract](gps-schema.md), [association rules](segment-trail-associations.md) and [metric definitions](measure-library.md).

## activities

Export: `view_activity.parquet`. Grain/key: One GPS-eligible activity; activity_key (same as activity_id).

| Field | Contract type | Meaning / use |
|---|---|---|
| `activity_date` | dateTime | UTC activity-start calendar date. |
| `activity_date_key` | int64 | UTC activity-start date as YYYYMMDD; use dates dimension for local reporting. |
| `activity_id` | int64 | Activity id; source identifier or relationship key, not a measure. |
| `activity_key` | int64 | Activity key; source identifier or relationship key, not a measure. |
| `activity_name` | string | Activity name. |
| `activity_type_key` | string | Activity type key; source identifier or relationship key, not a measure. |
| `average_cadence` | double | Average cadence. |
| `average_heartrate` | double | Average heartrate. |
| `average_speed_mph` | double | Average speed mph. |
| `average_watts` | double | Average watts. |
| `calories` | double | Source activity calories; unknown remains NULL. |
| `description` | string | Description. |
| `device_name` | string | Device name. |
| `distance_miles` | double | Converted source distance in miles at this table grain; gear is source lifetime distance, activities rounded to 2 decimals, efforts may overlap. |
| `elapsed_time_minutes` | double | Elapsed time minutes. |
| `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `is_commute` | int64 | Is commute flag: 1 yes, 0 no; NULL unknown. |
| `is_trainer` | int64 | Is trainer flag: 1 yes, 0 no; NULL unknown. |
| `kilojoules` | double | Kilojoules. |
| `max_heartrate` | double | Max heartrate. |
| `max_speed_mph` | double | Max speed mph. |
| `moving_time_minutes` | double | Moving time minutes. |
| `segment_effort_count` | int64 | Stored segment effort count for activity. |
| `sport_type` | string | Sport type. |
| `start_date` | dateTime | Stored activity start timestamp in UTC. |
| `stream_point_count` | int64 | All stored source stream rows for activity, not just valid GPS samples. |
| `suffer_score` | double | Source Strava suffer score; optional. |
| `total_elevation_gain_feet` | double | Total elevation gain feet. |
| `workout_type` | int64 | Strava workout-type code; meaning depends on sport. |

## activity_point_segments

Export: `view_activity_point_segments.parquet`. Grain/key: One verified point/effort membership; (activity_point_key, segment_effort_key).

| Field | Contract type | Meaning / use |
|---|---|---|
| `activity_point_key` | string | Stable activity/sample composite identifier; do not aggregate. |
| `segment_effort_key` | int64 | Segment effort key; source identifier or relationship key, not a measure. |
| `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |

## activity_points

Export: `view_activity_points.parquet`. Grain/key: One valid GPS sample; activity_point_key, unique (activity_id, point_index).

| Field | Contract type | Meaning / use |
|---|---|---|
| `activity_id` | int64 | Activity id; source identifier or relationship key, not a measure. |
| `activity_key` | int64 | Activity key; source identifier or relationship key, not a measure. |
| `activity_point_key` | string | Stable activity/sample composite identifier; do not aggregate. |
| `activity_type_key` | string | Activity type key; source identifier or relationship key, not a measure. |
| `cadence` | double | Source sample cadence in rpm. |
| `cumulative_distance_miles` | double | Source cumulative stream distance converted to miles; do not sum. |
| `date_basis` | string | activity_timezone or utc_fallback; indicates point calendar basis. |
| `date_key` | int64 | YYYYMMDD point-local calendar key (UTC when timezone metadata is missing). |
| `elapsed_time_seconds` | double | Point table: elapsed seconds from activity start. Effort table: stored whole-effort elapsed seconds. |
| `elevation_feet` | double | Point altitude in feet; not elevation gain. |
| `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `grade_percent` | double | Sample grade in percent. |
| `heartrate` | double | Sample heart rate in bpm. |
| `incremental_distance_miles` | double | Eligible preceding interval distance in miles; first/invalid intervals NULL. |
| `incremental_time_seconds` | double | Eligible preceding interval duration in seconds; first/invalid intervals NULL. |
| `is_moving` | int64 | Source moving flag: 1 moving, 0 stopped; NULL unknown. |
| `latitude` | double | WGS84 latitude in decimal degrees. |
| `longitude` | double | WGS84 longitude in decimal degrees. |
| `match_method` | string | Spatial assignment outcome code; see spatial contract in GPS schema. |
| `moving_time_seconds` | double | Point table: eligible interval seconds when moving, zero when stopped, otherwise NULL. Effort table: stored whole-effort moving seconds. |
| `point_index` | int64 | Original zero-based stream sample index; not a dense GPS-only row number. |
| `quality_status` | string | Interval quality code; see measurement rules in GPS schema and rebuild implementation. |
| `recorded_at_utc` | dateTime | UTC activity start plus stream elapsed seconds. |
| `speed_mph` | double | Speed mph. |
| `temperature_f` | double | Temperature f. |
| `trail_key` | int64 | Trail key; source identifier or relationship key, not a measure. |
| `trail_system_key` | int64 | Trail system key; source identifier or relationship key, not a measure. |
| `watts` | double | Sample power in watts. |

## activity_types

Export: `view_activity_type.parquet`. Grain/key: One GPS-used sport type; activity_type_key.

| Field | Contract type | Meaning / use |
|---|---|---|
| `activity_category` | string | Activity category. |
| `activity_type` | string | Activity type. |
| `activity_type_key` | string | Activity type key; source identifier or relationship key, not a measure. |

## dates

Export: `view_date.parquet`. Grain/key: One calendar date; date_key (YYYYMMDD).

| Field | Contract type | Meaning / use |
|---|---|---|
| `date` | dateTime | Date. |
| `date_key` | int64 | YYYYMMDD point-local calendar key (UTC when timezone metadata is missing). |
| `day_of_week` | int64 | SQLite numbering: Sunday=0 through Saturday=6. |
| `month_number` | int64 | Month number. |
| `quarter_number` | int64 | Quarter number. |
| `week_end_date` | dateTime | Sunday of the containing local calendar week. |
| `week_number` | int64 | SQLite %W: Monday-based week 00–53; use week_start_date across years. |
| `week_start_date` | dateTime | Monday of the containing local calendar week. |
| `year` | int64 | Year. |

## gear

Export: `view_gear.parquet`. Grain/key: One GPS-used equipment item; gear_key (same as gear_id).

| Field | Contract type | Meaning / use |
|---|---|---|
| `athlete_id` | int64 | Athlete id; source identifier or relationship key, not a measure. |
| `brand_name` | string | Brand name. |
| `created_at` | dateTime | Created at. |
| `description` | string | Description. |
| `detail_loaded_at` | dateTime | Detail loaded at. |
| `distance_miles` | double | Converted source distance in miles at this table grain; gear is source lifetime distance, activities rounded to 2 decimals, efforts may overlap. |
| `frame_type` | int64 | Strava frame-type code retained from source; consult source meaning before labeling. |
| `gear_id` | string | Gear id; source identifier or relationship key, not a measure. |
| `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `gear_name` | string | Gear name. |
| `is_primary` | int64 | Is primary flag: 1 yes, 0 no; NULL unknown. |
| `is_retired` | int64 | Is retired flag: 1 yes, 0 no; NULL unknown. |
| `model_name` | string | Model name. |
| `updated_at` | dateTime | Updated at. |

## segment_efforts

Export: `view_point_segment_effort.parquet`. Grain/key: One GPS-activity effort; segment_effort_key.

| Field | Contract type | Meaning / use |
|---|---|---|
| `activity_key` | int64 | Activity key; source identifier or relationship key, not a measure. |
| `distance_miles` | double | Converted source distance in miles at this table grain; gear is source lifetime distance, activities rounded to 2 decimals, efforts may overlap. |
| `elapsed_time_seconds` | double | Point table: elapsed seconds from activity start. Effort table: stored whole-effort elapsed seconds. |
| `end_index` | int64 | Inclusive original stream end index for effort membership. |
| `moving_time_seconds` | double | Point table: eligible interval seconds when moving, zero when stopped, otherwise NULL. Effort table: stored whole-effort moving seconds. |
| `segment_effort_key` | int64 | Segment effort key; source identifier or relationship key, not a measure. |
| `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |
| `start_index` | int64 | Inclusive original stream start index for effort membership. |

## segments

Export: `view_segment.parquet`. Grain/key: One GPS-used Strava segment; segment_key (same as segment_id).

| Field | Contract type | Meaning / use |
|---|---|---|
| `activity_type` | string | Activity type. |
| `average_grade` | double | Average grade. |
| `city` | string | City. |
| `climb_category` | int64 | Strava segment climb-category code. |
| `country` | string | Country. |
| `distance_miles` | double | Converted source distance in miles at this table grain; gear is source lifetime distance, activities rounded to 2 decimals, efforts may overlap. |
| `elevation_high_feet` | double | Elevation high feet. |
| `elevation_low_feet` | double | Elevation low feet. |
| `end_latitude` | double | End latitude. |
| `end_longitude` | double | End longitude. |
| `maximum_grade` | double | Maximum grade. |
| `segment_id` | int64 | Segment id; source identifier or relationship key, not a measure. |
| `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |
| `segment_name` | string | Segment name. |
| `start_latitude` | double | Start latitude. |
| `start_longitude` | double | Start longitude. |
| `state` | string | State. |

## segment_trail_associations

Export: `view_segment_trail_association.parquet`. Grain/key: One observed (segment_key, trail_key, trail_system_key) combination; trail/system can be NULL.

| Field | Contract type | Meaning / use |
|---|---|---|
| `association_basis` | string | verified_point_assignments; inferred observation, not ownership. |
| `evidence_status` | string | distance_supported for positive eligible distance; otherwise point_only. |
| `first_observed_at` | dateTime | Earliest observed membership timestamp in UTC. |
| `last_observed_at` | dateTime | Latest observed membership timestamp in UTC. |
| `observed_distance_miles` | double | Observed eligible effort traversal miles; excludes interval ending at effort start, repeated traversals accumulate. |
| `observed_distance_share` | double | 0–1 fraction of segment eligible observed distance including unmatched denominator; not confidence or geographic coverage. |
| `point_memberships` | int64 | Sample/effort pair count; repeated memberships are not unique physical points. |
| `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |
| `supporting_activities` | int64 | Distinct supporting activities for this association; not additive across associations. |
| `supporting_efforts` | int64 | Distinct supporting efforts for this association; not additive across associations. |
| `trail_key` | int64 | Trail key; source identifier or relationship key, not a measure. |
| `trail_system_key` | int64 | Trail system key; source identifier or relationship key, not a measure. |

## trails

Export: `view_trail.parquet`. Grain/key: One normalized trail; trail_key.

| Field | Contract type | Meaning / use |
|---|---|---|
| `bicycle_access` | string | Bicycle access. |
| `length_miles` | double | Full mapped trail catalog length in miles; not ridden distance. |
| `mtb_scale` | string | Mtb scale. |
| `mtb_type` | string | Mtb type. |
| `normalized_name` | string | Normalized name. |
| `primary_surface` | string | Primary surface. |
| `trail_key` | int64 | Trail key; source identifier or relationship key, not a measure. |
| `trail_name` | string | Trail name. |

## trail_systems

Export: `view_trail_system.parquet`. Grain/key: One catalog system; trail_system_key.

| Field | Contract type | Meaning / use |
|---|---|---|
| `boundary_confirmed` | int64 | 1 confirmed boundary, 0 unconfirmed; only confirmed polygons assign points. |
| `boundary_source` | string | Boundary source. |
| `city` | string | City. |
| `country` | string | Country. |
| `description` | string | Description. |
| `latitude` | double | WGS84 latitude in decimal degrees. |
| `longitude` | double | WGS84 longitude in decimal degrees. |
| `osm_element_id` | int64 | Osm element id; source identifier or relationship key, not a measure. |
| `osm_element_type` | string | Osm element type. |
| `state` | string | State. |
| `trail_system_key` | int64 | Trail system key; source identifier or relationship key, not a measure. |
| `trail_system_name` | string | Trail system name. |
