# Export and model data dictionary

This lists physical Parquet fields, their active semantic-model aliases, types and definitions. The source contract is `src/reporting/gps_schema.json`; aliases are `src/reporting/gps_model_columns.json`. Numeric durations are seconds except explicit service-hour/mixed-unit fields; distances are miles. Local event timestamps and explicit UTC audit timestamps are distinct. See [migration and formatting notes](reporting-field-renames.md).

## activities

Export: `view_activity.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `activity_date` | `date` | dateTime | Local activity-start calendar date, derived using the activity timezone and historical daylight-saving rules. NULL when unresolved. |
| `activity_date_key` | `date_key` | int64 | YYYYMMDD local activity-start date key. NULL when unresolved. |
| `activity_id` | `activity_id` | int64 | Activity id; source identifier or relationship key, not a measure. |
| `activity_key` | `activity_key` | int64 | Activity key; source identifier or relationship key, not a measure. |
| `activity_name` | `activity_name` | string | Source Strava activity title. Names need not be unique; use activity_key for identity. |
| `activity_type_key` | `activity_type_key` | string | Activity type key; source identifier or relationship key, not a measure. |
| `average_cadence` | `average_cadence` | double | Source activity average cadence in rpm; optional, not an average of selected GPS samples. |
| `average_heartrate` | `average_heartrate` | double | Source activity average heart rate in bpm; optional, not recomputed for selected route portions. |
| `average_speed_mph` | `average_speed_mph` | double | Source activity average speed converted to mph and rounded to 2 decimals; not route-selected speed. |
| `average_watts` | `average_watts` | double | Source activity average power in watts; optional, not recomputed for selected route portions. |
| `calories` | `calories` | double | Source activity calories; unknown remains NULL. |
| `description` | `description` | string | Source free-text description for the row entity; may be missing. |
| `device_name` | `device_name` | string | Source activity recording device name; may be missing. |
| `distance_miles` | `distance` | double | Converted source distance in miles at this table grain; gear is source lifetime distance, activities rounded to 2 decimals, efforts may overlap. |
| `elapsed_time_seconds` | `elapsed_time` | int64 | Whole source activity elapsed duration in numeric seconds, including stops. Use Activity Elapsed Time for formatted display. |
| `gear_key` | `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `is_commute` | `is_commute` | int64 | Is commute flag: 1 yes, 0 no; NULL unknown. |
| `is_trainer` | `is_trainer` | int64 | Is trainer flag: 1 yes, 0 no; NULL unknown. |
| `kilojoules` | `kilojoules` | double | Source activity energy in kilojoules; optional whole-activity total. |
| `max_heartrate` | `max_heartrate` | double | Source activity maximum heart rate in bpm; optional. |
| `max_speed_mph` | `max_speed_mph` | double | Source activity maximum speed converted to mph and rounded to 2 decimals. |
| `moving_time_seconds` | `moving_time` | int64 | Whole source activity moving duration in numeric seconds. Use Activity Moving Time for MM:SS or HH:MM:SS display. |
| `segment_effort_count` | `segment_effort_count` | int64 | Stored segment effort count for activity. |
| `sport_type` | `sport_type` | string | Source Strava sport type for the activity; GPS eligibility does not restrict sports to cycling. |
| `start_date` | `started_at` | dateTime | Activity start in its resolved local timezone. NULL when unresolved; started_at_utc retains the original instant. |
| `stream_point_count` | `stream_point_count` | int64 | All stored source stream rows for activity, not just valid GPS samples. |
| `suffer_score` | `suffer_score` | double | Source Strava suffer score; optional. |
| `total_elevation_gain_feet` | `total_elevation_gain_feet` | double | Whole source activity elevation gain converted to feet and rounded to 2 decimals; not allocated to trails. |
| `workout_type` | `workout_type` | int64 | Strava workout-type code; meaning depends on sport. |
| `start_date_utc` | `started_at_utc` | dateTime | Original source activity start instant in UTC; retained for auditing and timezone reconstruction. |
| `timezone_name` | `timezone_name` | string | IANA timezone used for local event reporting. |
| `date_basis` | `date_basis` | string | Timezone provenance: strava, first_gps, source_local or unresolved. No UTC instant is silently presented as local. |

## activity_point_segments

Export: `view_activity_point_segments.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `activity_point_key` | `activity_point_key` | string | Stable activity/sample composite identifier; do not aggregate. |
| `segment_effort_key` | `segment_effort_key` | int64 | Segment effort key; source identifier or relationship key, not a measure. |
| `segment_key` | `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |

## activity_points

Export: `view_activity_points.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `activity_id` | `activity_id` | int64 | Activity id; source identifier or relationship key, not a measure. |
| `activity_key` | `activity_key` | int64 | Activity key; source identifier or relationship key, not a measure. |
| `activity_point_key` | `activity_point_key` | string | Stable activity/sample composite identifier; do not aggregate. |
| `activity_type_key` | `activity_type_key` | string | Activity type key; source identifier or relationship key, not a measure. |
| `cadence` | `cadence` | double | Source sample cadence in rpm. |
| `cumulative_distance_miles` | `cumulative_distance` | double | Source cumulative stream distance converted to miles; do not sum. |
| `date_basis` | `date_basis` | string | Timezone provenance: strava, first_gps, source_local or unresolved. No UTC instant is silently presented as local. |
| `date_key` | `date_key` | int64 | YYYYMMDD local point-date key; NULL when timezone or source time is unresolved. |
| `elapsed_time_seconds` | `elapsed_time` | double | Point table: elapsed seconds from activity start. Effort table: stored whole-effort elapsed seconds. |
| `elevation_feet` | `elevation_feet` | double | Point altitude in feet; not elevation gain. |
| `gear_key` | `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `grade_percent` | `grade_percent` | double | Sample grade in percent. |
| `heartrate` | `heartrate` | double | Sample heart rate in bpm. |
| `incremental_distance_miles` | `incremental_distance` | double | Eligible preceding interval distance in miles; first/invalid intervals NULL. |
| `incremental_time_seconds` | `incremental_time` | double | Eligible preceding interval duration in seconds; first/invalid intervals NULL. |
| `is_moving` | `is_moving` | int64 | Source moving flag: 1 moving, 0 stopped; NULL unknown. |
| `latitude` | `latitude` | double | WGS84 latitude in decimal degrees. |
| `longitude` | `longitude` | double | WGS84 longitude in decimal degrees. |
| `match_method` | `match_method` | string | Spatial outcome: boundary, boundary_overlap_lowest_id or unmatched, optionally suffixed :nearest_trail or :ambiguous_trail. Unknown system/trail assignments retain NULL keys. |
| `moving_time_seconds` | `moving_time` | double | Point table: eligible interval seconds when moving, zero when stopped, otherwise NULL. Effort table: stored whole-effort moving seconds. |
| `point_index` | `point_index` | int64 | Original zero-based stream sample index; not a dense GPS-only row number. |
| `quality_status` | `quality_status` | string | Interval quality: valid, first_point, invalid_interval or recording_gap. Only valid intervals have eligible increments; NULL increments are not zero. |
| `recorded_at_utc` | `recorded_at_utc` | dateTime | UTC activity start plus stream elapsed seconds. |
| `speed_mph` | `speed_mph` | double | Source instantaneous stream speed converted to mph; NULL when not recorded. |
| `temperature_f` | `temperature_f` | double | Source sample temperature converted from Celsius to Fahrenheit; NULL when absent. |
| `trail_key` | `trail_key` | int64 | Trail key; source identifier or relationship key, not a measure. |
| `trail_system_key` | `trail_system_key` | int64 | Trail system key; source identifier or relationship key, not a measure. |
| `watts` | `watts` | double | Sample power in watts. |
| `recorded_at` | `recorded_at` | dateTime | GPS sample timestamp in the activity local timezone, including historical offset changes. NULL when unresolved; recorded_at_utc retains the instant. |
| `timezone_name` | `timezone_name` | string | IANA timezone used for local event reporting. |

## activity_types

Export: `view_activity_type.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `activity_category` | `activity_category` | string | Locally mapped activity category; review unmapped source sport types before grouping. |
| `activity_type` | `activity_type` | string | Source sport/type label for this dimension row. |
| `activity_type_key` | `activity_type_key` | string | Activity type key; source identifier or relationship key, not a measure. |

## dates

Export: `view_date.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `date` | `date` | dateTime | Modeled calendar date spanning earliest through latest point date, including inactive dates. |
| `date_key` | `date_key` | int64 | YYYYMMDD point-local calendar key (UTC when timezone metadata is missing). |
| `day_of_week` | `day_of_week` | int64 | SQLite numbering: Sunday=0 through Saturday=6. |
| `month_number` | `month_number` | int64 | Calendar month number, January=1 through December=12. |
| `quarter_number` | `quarter_number` | int64 | Calendar quarter number, 1 through 4. |
| `week_end_date` | `week_end_date` | dateTime | Sunday of the containing local calendar week. |
| `week_number` | `week_number` | int64 | SQLite %W: Monday-based week 00–53; use week_start_date across years. |
| `week_start_date` | `week_start_date` | dateTime | Monday of the containing local calendar week. |
| `year` | `year` | int64 | Calendar year of the modeled point date. |

## gear

Export: `view_gear.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `athlete_id` | `athlete_id` | int64 | Source equipment owner athlete identifier; categorical, never summed. |
| `brand_name` | `brand_name` | string | Source equipment brand; NULL when not provided. |
| `created_at` | `created_at_utc` | dateTime | Source equipment row creation timestamp. |
| `description` | `description` | string | Source free-text description for the row entity; may be missing. |
| `detail_loaded_at` | `detail_loaded_at_utc` | dateTime | Timestamp of the last equipment-detail load; NULL when detail is unavailable. |
| `distance_miles` | `distance` | double | Source Strava lifetime equipment miles, rounded to 2 decimals; not restricted to GPS dataset history or report slicers. |
| `frame_type` | `frame_type` | int64 | Strava frame-type code retained from source; consult source meaning before labeling. |
| `gear_id` | `gear_id` | string | Gear id; source identifier or relationship key, not a measure. |
| `gear_key` | `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `gear_name` | `gear_name` | string | Source equipment display name; use gear_key for identity. |
| `is_primary` | `is_primary` | int64 | Is primary flag: 1 yes, 0 no; NULL unknown. |
| `is_retired` | `is_retired` | int64 | Is retired flag: 1 yes, 0 no; NULL unknown. |
| `model_name` | `model_name` | string | Source equipment model; NULL when not provided. |
| `updated_at` | `updated_at_utc` | dateTime | Source equipment row last-update timestamp. |

## segment_efforts

Export: `view_point_segment_effort.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `activity_key` | `activity_key` | int64 | Activity key; source identifier or relationship key, not a measure. |
| `distance_miles` | `distance` | double | Stored full-effort distance converted to miles; repeated/overlapping efforts can double-count route distance. |
| `elapsed_time_seconds` | `time` | double | Point table: elapsed seconds from activity start. Effort table: stored whole-effort elapsed seconds. |
| `end_index` | `end_index` | int64 | Inclusive original stream end index for effort membership. |
| `moving_time_seconds` | `moving_time` | double | Point table: eligible interval seconds when moving, zero when stopped, otherwise NULL. Effort table: stored whole-effort moving seconds. |
| `segment_effort_key` | `segment_effort_key` | int64 | Segment effort key; source identifier or relationship key, not a measure. |
| `segment_key` | `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |
| `start_index` | `start_index` | int64 | Inclusive original stream start index for effort membership. |

## segments

Export: `view_segment.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `activity_type` | `activity_type` | string | Source sport/type label for this dimension row. |
| `average_grade` | `average_grade` | double | Source segment average grade in percent. |
| `city` | `city` | string | Catalog/source city label for this entity; not inferred from selected points. |
| `climb_category` | `climb_category` | int64 | Strava segment climb-category code. |
| `country` | `country` | string | Catalog/source country label for this entity. |
| `distance_miles` | `distance` | double | Source segment catalog length converted to miles; not traversed activity distance. |
| `elevation_high_feet` | `elevation_high_feet` | double | Source segment highest elevation converted to feet. |
| `elevation_low_feet` | `elevation_low_feet` | double | Source segment lowest elevation converted to feet. |
| `end_latitude` | `end_latitude` | double | Source segment end latitude in WGS84 decimal degrees. |
| `end_longitude` | `end_longitude` | double | Source segment end longitude in WGS84 decimal degrees. |
| `maximum_grade` | `maximum_grade` | double | Source segment maximum grade in percent. |
| `segment_id` | `segment_id` | int64 | Segment id; source identifier or relationship key, not a measure. |
| `segment_key` | `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |
| `segment_name` | `segment_name` | string | Source Strava segment display name; names need not be unique. |
| `start_latitude` | `start_latitude` | double | Source segment start latitude in WGS84 decimal degrees. |
| `start_longitude` | `start_longitude` | double | Source segment start longitude in WGS84 decimal degrees. |
| `state` | `state` | string | Source segment state/region label. |

## segment_trail_associations

Export: `view_segment_trail_association.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `association_basis` | `association_basis` | string | verified_point_assignments; inferred observation, not ownership. |
| `evidence_status` | `evidence_status` | string | distance_supported for positive eligible distance; otherwise point_only. |
| `first_observed_at` | `first_observed_at_utc` | dateTime | Earliest observed membership timestamp in UTC. |
| `last_observed_at` | `last_observed_at_utc` | dateTime | Latest observed membership timestamp in UTC. |
| `observed_distance_miles` | `distance` | double | Observed eligible effort traversal miles; excludes interval ending at effort start, repeated traversals accumulate. |
| `observed_distance_share` | `observed_distance_share` | double | 0–1 fraction of segment eligible observed distance including unmatched denominator; not confidence or geographic coverage. |
| `point_memberships` | `point_memberships` | int64 | Sample/effort pair count; repeated memberships are not unique physical points. |
| `segment_key` | `segment_key` | int64 | Segment key; source identifier or relationship key, not a measure. |
| `supporting_activities` | `supporting_activities` | int64 | Distinct supporting activities for this association; not additive across associations. |
| `supporting_efforts` | `supporting_efforts` | int64 | Distinct supporting efforts for this association; not additive across associations. |
| `trail_key` | `trail_key` | int64 | Trail key; source identifier or relationship key, not a measure. |
| `trail_system_key` | `trail_system_key` | int64 | Trail system key; source identifier or relationship key, not a measure. |

## trails

Export: `view_trail.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `bicycle_access` | `bicycle_access` | string | Catalog bicycle-access tag; source text, not an access guarantee. |
| `length_miles` | `length` | double | Full mapped trail catalog length in miles; not ridden distance. |
| `mtb_scale` | `mtb_scale` | string | Catalog mountain-bike difficulty tag; source classification, may be missing. |
| `mtb_type` | `mtb_type` | string | Catalog mountain-bike trail type tag; source classification, may be missing. |
| `normalized_name` | `normalized_name` | string | Trail name normalized for catalog matching/grouping. |
| `primary_surface` | `primary_surface` | string | Catalog primary trail surface tag; source text, may be missing. |
| `trail_key` | `trail_key` | int64 | Trail key; source identifier or relationship key, not a measure. |
| `trail_name` | `trail_name` | string | Normalized trail display name; use trail_key for identity. |

## trail_systems

Export: `view_trail_system.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `boundary_confirmed` | `boundary_confirmed` | int64 | 1 confirmed boundary, 0 unconfirmed; only confirmed polygons assign points. |
| `boundary_source` | `boundary_source` | string | Provenance label for the stored trail-system boundary. |
| `city` | `city` | string | Catalog/source city label for this entity; not inferred from selected points. |
| `country` | `country` | string | Catalog/source country label for this entity. |
| `description` | `description` | string | Source free-text description for the row entity; may be missing. |
| `latitude` | `latitude` | double | Catalog system representative latitude in WGS84 decimal degrees; not a GPS fact sample. |
| `longitude` | `longitude` | double | Catalog system representative longitude in WGS84 decimal degrees; not a GPS fact sample. |
| `osm_element_id` | `osm_element_id` | int64 | Source OpenStreetMap element identifier; interpret with osm_element_type. |
| `osm_element_type` | `osm_element_type` | string | OpenStreetMap source element type associated with osm_element_id. |
| `state` | `state` | string | Source segment state/region label. |
| `trail_system_key` | `trail_system_key` | int64 | Trail system key; source identifier or relationship key, not a measure. |
| `trail_system_name` | `trail_system_name` | string | Catalog trail-system display name; use trail_system_key for identity. |

## gear_components

Export: `view_gear_components.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `component_key` | `component_key` | int64 | Stable component identifier linking gear_components, service events and current service status; do not sum. |
| `gear_key` | `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `component_type` | `component_type` | string | Tracked component category, such as fork or chain. |
| `manufacturer` | `manufacturer` | string | Component manufacturer as entered in the maintenance catalog. |
| `model` | `model` | string | Component model as entered in the maintenance catalog. |
| `installed_at` | `installed_at` | dateTime | Component installation timestamp; usage before installation is excluded. |
| `removed_at` | `removed_at` | dateTime | Component removal timestamp; NULL means currently installed. Usage after removal is excluded. |
| `service_interval_type` | `service_interval_type` | string | Schedule unit: hours or miles. Determines which usage total drives status. |
| `service_interval_value` | `service_interval_value` | double | Scheduled interval in service_interval_type units; NULL means no complete schedule. |
| `notes` | `notes` | string | User-entered notes for this component or service event at the table row grain. |

## component_services

Export: `view_component_services.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `service_id` | `service_id` | int64 | Unique maintenance service-event identifier; do not sum. |
| `component_key` | `component_key` | int64 | Stable component identifier linking gear_components, service events and current service status; do not sum. |
| `service_date` | `service_date` | dateTime | Recorded date/timestamp of this maintenance event. |
| `service_type` | `service_type` | string | User-entered maintenance service category. |
| `notes` | `notes` | string | User-entered notes for this component or service event at the table row grain. |

## component_service_status

Export: `view_component_service_status.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `component_key` | `component_key` | int64 | Stable component identifier linking gear_components, service events and current service status; do not sum. |
| `component_id` | `component_id` | int64 | Original component identifier; same value as component_key. |
| `gear_key` | `gear_key` | string | Gear key; source identifier or relationship key, not a measure. |
| `gear_name` | `gear_name` | string | Source equipment display name; use gear_key for identity. |
| `component_type` | `component_type` | string | Tracked component category, such as fork or chain. |
| `manufacturer` | `manufacturer` | string | Component manufacturer as entered in the maintenance catalog. |
| `model` | `model` | string | Component model as entered in the maintenance catalog. |
| `component_name` | `component_name` | string | Display name: manufacturer plus model, falling back to component type when model is absent. |
| `installed_at` | `installed_at` | dateTime | Component installation timestamp; usage before installation is excluded. |
| `removed_at` | `removed_at` | dateTime | Component removal timestamp; NULL means currently installed. Usage after removal is excluded. |
| `is_active` | `is_active` | int64 | 1 when removed_at is NULL, otherwise 0; installed-component flag rather than recent riding activity. |
| `service_interval_type` | `service_interval_type` | string | Schedule unit: hours or miles. Determines which usage total drives status. |
| `service_interval_value` | `service_interval_value` | double | Scheduled interval in service_interval_type units; NULL means no complete schedule. |
| `latest_service_id` | `latest_service_id` | int64 | Most recent eligible service-event identifier, ordered by service timestamp then ID; NULL if none. |
| `latest_service_date` | `latest_service_date` | dateTime | Most recent service within component installation/removal dates and no later than the SQL export date; NULL if none. |
| `latest_service_type` | `latest_service_type` | string | Category of the most recent eligible service; NULL if no eligible service exists. |
| `latest_service_notes` | `latest_service_notes` | string | Notes on the most recent eligible service; NULL if unavailable. |
| `service_baseline_date` | `service_baseline_date` | dateTime | Latest eligible service timestamp, or installation timestamp when no eligible service exists. |
| `service_baseline_date_key` | `service_baseline_date_key` | int64 | YYYYMMDD calendar key derived from service_baseline_date; not a local GPS point date. |
| `hours_since_service` | `hours_since_service` | double | Stored source activity moving hours for this gear since baseline, within component installation/removal bounds; rounded to 2 decimals. |
| `miles_since_service` | `miles_since_service` | double | Stored source activity miles for this gear since baseline, within component installation/removal bounds; rounded to 2 decimals. |
| `lifetime_component_hours` | `lifetime_component_hours` | double | Stored source activity moving hours for this gear during the installation window, through SQL now; rounded to 2 decimals. |
| `lifetime_component_miles` | `lifetime_component_miles` | double | Stored source activity miles for this gear during the installation window, through SQL now; rounded to 2 decimals. |
| `usage_since_service` | `usage_since_service` | double | Hours or miles since baseline according to schedule type; rounded to 2 decimals. Unknown type yields NULL. |
| `usage_remaining` | `usage_remaining` | double | Scheduled interval minus usage, rounded to 2 decimals; negative values indicate overdue usage. |
| `usage_overdue` | `usage_overdue` | double | Usage above scheduled interval, floored at zero and rounded to 2 decimals. |
| `service_interval_percent` | `service_interval_percent` | double | Consumed interval on a 0–100 scale: usage divided by interval times 100; can exceed 100. Zero interval yields NULL. |
| `service_interval_remaining_percent` | `service_interval_remaining_percent` | double | Remaining interval ratio, floored at zero: 1 = 100% remaining. Zero/unknown intervals yield NULL. |
| `service_interval_remaining` | `service_interval_remaining` | double | Remaining hours or miles, rounded to 2 decimals and floored at zero. |
| `service_status` | `service_status` | string | Inactive if removed; No Schedule if type/value missing; Due at 100% usage; Due Soon at 80%; otherwise Current. |
| `component_notes` | `component_notes` | string | User-entered notes about the tracked component. |

## segment_effort_achievements

Export: `view_segment_effort_achievement.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `segment_effort_key` | `segment_effort_key` | int64 | Unique Strava effort ID; one row per stored effort in a GPS-eligible activity. |
| `segment_key` | `segment_key` | int64 | Strava segment identifier. Segment dimension filter key; do not aggregate. |
| `activity_key` | `activity_key` | int64 | Parent activity identifier; distinct from the segment-effort ID. |
| `gear_key` | `gear_key` | string | Known source equipment identifier; NULL for missing/unloaded gear. |
| `activity_type_key` | `activity_type_key` | string | Parent activity sport type, linked to the activity-type dimension. |
| `effort_started_at` | `started_at` | dateTime | Effort start in the resolved activity timezone, or the source local effort timestamp. NULL when neither is available. |
| `effort_local_date` | `date` | dateTime | Local effort-start calendar date. No silent UTC fallback; inspect date_basis for provenance. |
| `date_key` | `date_key` | int64 | YYYYMMDD local effort-start date key, NULL if local time is unresolved. |
| `date_basis` | `date_basis` | string | Timezone provenance: strava, first_gps, source_local or unresolved. No UTC instant is silently presented as local. |
| `elapsed_time_seconds` | `time` | int64 | Source whole-effort elapsed seconds, including stops. Positive values rank stored personal bests; zero/negative values are excluded. |
| `moving_time_seconds` | `moving_time` | int64 | Source whole-effort moving seconds; not the basis of personal-best ranking. |
| `distance_miles` | `distance` | double | Source whole-effort distance converted to miles. Repeated/overlapping efforts are not unique route distance. |
| `effort_hidden` | `effort_hidden` | int64 | Source hidden flag: 1 hidden, 0 visible, NULL unknown. Explicitly hidden efforts do not qualify for stored-best selection. |
| `reported_pr_rank` | `reported_pr_rank` | int64 | Latest stored Strava-reported PR rank for this effort; NULL does not mean zero. Use pr_rank_status and retrieval time to assess coverage. |
| `reported_kom_rank` | `reported_kom_rank` | int64 | Latest stored Strava-reported leaderboard rank for this effort. Rank 1 is a reported first place, not proof of a current crown or historical leaderboard position on activity day. |
| `ranks_retrieved_at` | `ranks_retrieved_at_utc` | dateTime | UTC response retrieval timestamp for the stored ranks. NULL means a legacy observation without verified retrieval provenance. |
| `pr_rank_status` | `pr_rank_status` | string | ranked, no_rank (explicit API null), not_returned (field omitted), or legacy_unobserved (no retrieval metadata). |
| `kom_rank_status` | `kom_rank_status` | string | ranked, no_rank (explicit API null), not_returned (field omitted), or legacy_unobserved (no retrieval metadata). |
| `reported_pr_first` | `reported_pr_first` | int64 | 1 when an observed API response reports pr_rank=1, 0 for an observed nonfirst/null rank, NULL when the field was omitted or never observed. |
| `reported_kom_first` | `reported_kom_first` | int64 | 1 when an observed API response reports kom_rank=1; 0 for nonfirst/null, NULL for omitted/unobserved. Not a current crown indicator. |
| `eligible_for_stored_best` | `eligible_for_pr` | int64 | 1 for positive elapsed time and no explicit hidden flag; otherwise 0. Does not certify GPS quality or exclude other source anomalies. |
| `activity_url` | `activity_url` | string | Source Strava activity URL; access depends on viewer permissions. |
| `segment_url` | `segment_url` | string | Source Strava segment URL; not a leaderboard access grant. |
| `effort_started_at_utc` | `started_at_utc` | dateTime | Original UTC timestamp retained for audit. |
| `timezone_name` | `timezone_name` | string | IANA timezone used for local event reporting. |

## segment_personal_bests

Export: `view_segment_personal_best.parquet`.

| Export field | Model field | Type | Definition |
|---|---|---|---|
| `segment_key` | `segment_key` | int64 | Strava segment identifier. Segment dimension filter key; do not aggregate. |
| `best_segment_effort_key` | `pr_effort_key` | int64 | Chosen fastest-known stored effort ID. Ties choose earliest UTC effort timestamp, then lowest effort ID. |
| `best_activity_key` | `pr_activity_key` | int64 | Parent activity of the chosen best effort; this lifetime summary does not respond to activity/date/gear dimension filters. |
| `best_effort_started_at` | `pr_started_at` | dateTime | Local start timestamp of the current fastest eligible stored effort. |
| `best_effort_local_date` | `pr_date` | dateTime | Local calendar date of the current fastest eligible stored effort. NULL if unresolved. |
| `best_elapsed_time_seconds` | `pr_time` | int64 | Lowest positive stored elapsed seconds among nonhidden efforts in stored GPS-eligible activities; not a certified Strava lifetime PR. |
| `best_moving_time_seconds` | `pr_moving_time` | int64 | Source moving seconds of the chosen best effort; selection ranks elapsed time. |
| `best_distance_miles` | `pr_distance` | double | Full source effort distance in miles for the chosen best. |
| `stored_effort_count` | `stored_effort_count` | int64 | All stored GPS-eligible efforts for this segment, including hidden and nonpositive-time entries. |
| `eligible_effort_count` | `eligible_effort_count` | int64 | Stored efforts eligible for the best-time comparison: positive elapsed time and no explicit hidden flag. |
| `tied_best_effort_count` | `pr_tie_count` | int64 | Eligible efforts tied at the lowest elapsed time. Only one deterministic representative appears in this table. |
| `activity_url` | `activity_url` | string | Source Strava activity URL; access depends on viewer permissions. |
| `segment_url` | `segment_url` | string | Source Strava segment URL; not a leaderboard access grant. |
| `reported_pr_rank` | `reported_pr_rank` | int64 | Latest stored Strava-reported PR rank for this effort; NULL does not mean zero. Use pr_rank_status and retrieval time to assess coverage. |
| `reported_kom_rank` | `reported_kom_rank` | int64 | Latest stored Strava-reported leaderboard rank for this effort. Rank 1 is a reported first place, not proof of a current crown or historical leaderboard position on activity day. |
| `ranks_retrieved_at` | `ranks_retrieved_at_utc` | dateTime | UTC response retrieval timestamp for the stored ranks. NULL means a legacy observation without verified retrieval provenance. |
| `pr_rank_status` | `pr_rank_status` | string | ranked, no_rank (explicit API null), not_returned (field omitted), or legacy_unobserved (no retrieval metadata). |
| `kom_rank_status` | `kom_rank_status` | string | ranked, no_rank (explicit API null), not_returned (field omitted), or legacy_unobserved (no retrieval metadata). |
| `best_basis` | `pr_basis` | string | fastest_visible_positive_time_in_stored_gps_history; scope is imported GPS history, not a complete leaderboard or lifetime guarantee. |
| `best_effort_started_at_utc` | `pr_started_at_utc` | dateTime | Original UTC timestamp retained for audit. |
| `date_basis` | `date_basis` | string | Timezone provenance: strava, first_gps, source_local or unresolved. No UTC instant is silently presented as local. |
| `timezone_name` | `timezone_name` | string | IANA timezone used for local event reporting. |
