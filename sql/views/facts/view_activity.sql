/*
===============================================================================
View Name : view_activity

Purpose:
    Provides one analytics-ready row per Strava activity.

Grain:
    One row per activity_id.

Dependencies:
    activities
    activity_streams
    segment_efforts

Consumers:
    Power BI

Notes:
    Exposes reporting measures using imperial units. Distance is reported in
    miles, elevation in feet, speed in miles per hour, and duration in minutes.
    Activity dates use the stored start_date value because activities does not
    currently persist a local start timestamp.
===============================================================================
*/

drop view if exists view_activity;

create view view_activity as

with stream_summary as (
    select
          activity_id
        , count(*) as stream_point_count
    from activity_streams
    group by activity_id
),
segment_effort_summary as (
    select
          activity_id
        , count(*) as segment_effort_count
    from segment_efforts
    group by activity_id
)
select
      a.activity_id
    , cast(strftime('%Y%m%d', date(a.start_date)) as integer) as activity_date_key
    , a.sport_type as activity_type_key
    , a.gear_id as gear_key
    , a.name as activity_name
    , a.sport_type
    , a.start_date
    , date(a.start_date) as activity_date
    , round(a.distance_meters / 1609.344, 2) as distance_miles
    , round(a.moving_time_seconds / 60.0, 2) as moving_time_minutes
    , round(a.elapsed_time_seconds / 60.0, 2) as elapsed_time_minutes
    , round(a.total_elevation_gain_meters * 3.280839895, 2) as total_elevation_gain_feet
    , round(a.average_speed_mps * 2.236936292, 2) as average_speed_mph
    , round(a.max_speed_mps * 2.236936292, 2) as max_speed_mph
    , a.average_heartrate
    , a.max_heartrate
    , a.average_cadence
    , a.average_watts
    , a.kilojoules
    , a.calories
    , a.suffer_score
    , a.commute as is_commute
    , a.trainer as is_trainer
    , coalesce(ss.stream_point_count, 0) as stream_point_count
    , coalesce(ses.segment_effort_count, 0) as segment_effort_count
from activities a
left join stream_summary ss
    on a.activity_id = ss.activity_id
left join segment_effort_summary ses
    on a.activity_id = ses.activity_id;
