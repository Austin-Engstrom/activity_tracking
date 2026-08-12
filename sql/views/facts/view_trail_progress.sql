/*
===============================================================================
View Name : view_trail_progress

Purpose:
    Provides the current lifetime completion state for each official trail.

Grain:
    One row per official_trail_id.

Dependencies:
    official_trail_progress
    official_trails

Consumers:
    Power BI

Notes:
    Unique covered distance is derived from official trail length multiplied
    by lifetime coverage percentage. All distance measures are reported in
    miles. Total ridden distance represents repeated riding and can exceed the
    official trail length.
===============================================================================
*/

drop view if exists view_trail_progress;

create view view_trail_progress as

select
      otp.official_trail_id as official_trail_key
    , cast(strftime('%Y%m%d', date(otp.first_ridden_at)) as integer) as first_ridden_date_key
    , cast(strftime('%Y%m%d', date(otp.last_ridden_at)) as integer) as last_ridden_date_key
    , cast(strftime('%Y%m%d', date(otp.updated_at)) as integer) as progress_updated_date_key
    , otp.activity_count
    , otp.first_ridden_at
    , otp.last_ridden_at
    , round(otp.total_ridden_distance_meters / 1609.344, 2) as total_ridden_distance_miles
    , round(otp.estimated_coverage_percent, 2) as estimated_coverage_percent
    , round(
          (ot.total_length_meters * otp.estimated_coverage_percent / 100.0) / 1609.344
        , 2
      ) as unique_covered_distance_miles
    , round(
          (
              ot.total_length_meters
            - (ot.total_length_meters * otp.estimated_coverage_percent / 100.0)
          ) / 1609.344
        , 2
      ) as remaining_distance_miles
    , otp.progress_status
    , case when otp.progress_status = 'completed' then 1 else 0 end as is_completed
    , case when otp.progress_status = 'nearly_complete' then 1 else 0 end as is_nearly_complete
    , case when otp.progress_status = 'partial' then 1 else 0 end as is_partial
    , case when otp.progress_status = 'started' then 1 else 0 end as is_started
    , case when otp.progress_status = 'unridden' then 1 else 0 end as is_unridden
    , otp.updated_at
from official_trail_progress otp
inner join official_trails ot
    on otp.official_trail_id = ot.official_trail_id;
