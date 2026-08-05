/*
===============================================================================
View Name : view_segment_effort

Purpose:
    Provides one analytics-ready row per Strava segment effort.

Grain:
    One row per segment_effort_id.

Dependencies:
    segment_efforts

Consumers:
    Power BI

Notes:
    Exposes metric and imperial distance fields and includes date keys for the
    shared date dimension.
===============================================================================
*/

drop view if exists view_segment_effort;
    
create view view_segment_effort as

select
      se.segment_effort_id
    , se.segment_id as segment_key
    , se.activity_id

    , cast(
          strftime(
              '%Y%m%d'
            , date(
                  coalesce(
                      se.start_date_local
                    , se.start_date
                  )
              )
          )
          as integer
      ) as effort_date_key

    , se.name as segment_effort_name

    , se.start_date
    , se.start_date_local

    , se.elapsed_time_seconds

    , se.elapsed_time_seconds
        / 60.0 as elapsed_time_minutes

    , se.moving_time_seconds

    , se.moving_time_seconds
        / 60.0 as moving_time_minutes

    , se.distance_meters

    , se.distance_meters
        / 1609.344 as distance_miles

    , se.start_index
    , se.end_index

    , se.average_cadence
    , se.average_watts
    , se.device_watts as is_device_watts
    , se.average_heartrate
    , se.max_heartrate

    , se.kom_rank
    , se.pr_rank

    , se.hidden as is_hidden

    , se.created_at
    , se.updated_at

from segment_efforts se;