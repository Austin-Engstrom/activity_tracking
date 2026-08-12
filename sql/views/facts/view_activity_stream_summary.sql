/*
===============================================================================
View Name : view_activity_stream_summary

Purpose:
    Summarizes detailed activity-stream records into one analytics-ready row
    per activity.

Grain:
    One row per activity_id.

Dependencies:
    activity_streams

Consumers:
    Power BI

Notes:
    Prevents the full activity-stream table from being loaded into the primary
    Power BI model while preserving useful stream-derived metrics.

    Reporting measures use imperial units. Distance is reported in miles,
    altitude in feet, speed in miles per hour, temperature in Fahrenheit,
    and duration in minutes.
===============================================================================
*/

drop view if exists view_activity_stream_summary;

create view view_activity_stream_summary as

select
      activity_id
    , count(*) as stream_point_count
    , round(min(time_seconds) / 60.0, 2) as minimum_time_minutes
    , round(max(time_seconds) / 60.0, 2) as maximum_time_minutes
    , round(min(distance_meters) / 1609.344, 2) as minimum_distance_miles
    , round(max(distance_meters) / 1609.344, 2) as maximum_distance_miles
    , round(min(altitude_meters) * 3.280839895, 2) as minimum_altitude_feet
    , round(max(altitude_meters) * 3.280839895, 2) as maximum_altitude_feet
    , round((max(altitude_meters) - min(altitude_meters)) * 3.280839895, 2) as altitude_range_feet
    , round(avg(velocity_mps) * 2.236936292, 2) as average_velocity_mph
    , round(max(velocity_mps) * 2.236936292, 2) as maximum_velocity_mph
    , round(avg(heartrate), 2) as average_heartrate
    , max(heartrate) as maximum_heartrate
    , round(avg(cadence), 2) as average_cadence
    , max(cadence) as maximum_cadence
    , round(avg(watts), 2) as average_watts
    , max(watts) as maximum_watts
    , round(avg(temperature_c) * 9.0 / 5.0 + 32.0, 2) as average_temperature_f
    , round(min(temperature_c) * 9.0 / 5.0 + 32.0, 2) as minimum_temperature_f
    , round(max(temperature_c) * 9.0 / 5.0 + 32.0, 2) as maximum_temperature_f
    , round(avg(grade_percent), 2) as average_grade_percent
    , round(min(grade_percent), 2) as minimum_grade_percent
    , round(max(grade_percent), 2) as maximum_grade_percent
    , sum(case when is_moving = 1 then 1 else 0 end) as moving_point_count
    , sum(case when is_moving = 0 then 1 else 0 end) as stopped_point_count
    , round(
          sum(case when is_moving = 1 then 1 else 0 end) * 100.0
          / nullif(count(*), 0)
        , 2
      ) as moving_point_percent
from activity_streams
group by activity_id;
