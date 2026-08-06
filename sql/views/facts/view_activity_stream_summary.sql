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
===============================================================================
*/

drop view if exists view_activity_stream_summary;

create view view_activity_stream_summary as

select
      activity_id

    , count(*) as stream_point_count

    , min(time_seconds) as minimum_time_seconds
    , max(time_seconds) as maximum_time_seconds

    , min(distance_meters) as minimum_distance_meters
    , max(distance_meters) as maximum_distance_meters

    , max(distance_meters)
        / 1609.344 as maximum_distance_miles

    , min(altitude_meters) as minimum_altitude_meters

    , min(altitude_meters)
        * 3.280839895 as minimum_altitude_feet

    , max(altitude_meters) as maximum_altitude_meters

    , max(altitude_meters)
        * 3.280839895 as maximum_altitude_feet

    , max(altitude_meters)
        - min(altitude_meters) as altitude_range_meters

    , (
          max(altitude_meters)
        - min(altitude_meters)
      ) * 3.280839895 as altitude_range_feet

    , avg(velocity_mps) as average_velocity_mps

    , avg(velocity_mps)
        * 2.236936292 as average_velocity_mph

    , max(velocity_mps) as maximum_velocity_mps

    , max(velocity_mps)
        * 2.236936292 as maximum_velocity_mph

    , avg(heartrate) as average_heartrate
    , max(heartrate) as maximum_heartrate

    , avg(cadence) as average_cadence
    , max(cadence) as maximum_cadence

    , avg(watts) as average_watts
    , max(watts) as maximum_watts

    , avg(temperature_c) as average_temperature_c
    , min(temperature_c) as minimum_temperature_c
    , max(temperature_c) as maximum_temperature_c

    , avg(temperature_c) * 9.0 / 5.0 + 32.0
        as average_temperature_f

    , min(temperature_c) * 9.0 / 5.0 + 32.0
        as minimum_temperature_f

    , max(temperature_c) * 9.0 / 5.0 + 32.0
        as maximum_temperature_f

    , avg(grade_percent) as average_grade_percent
    , min(grade_percent) as minimum_grade_percent
    , max(grade_percent) as maximum_grade_percent

    , sum(
          case
              when is_moving = 1
                  then 1
              else 0
          end
      ) as moving_point_count

    , sum(
          case
              when is_moving = 0
                  then 1
              else 0
          end
      ) as stopped_point_count

    , round(
          sum(
              case
                  when is_moving = 1
                      then 1
                  else 0
              end
          ) * 100.0
          / nullif(count(*), 0)
        , 1
      ) as moving_point_percent

from activity_streams

group by
    activity_id;