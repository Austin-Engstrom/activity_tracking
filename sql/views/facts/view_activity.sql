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

drop view if exists view_activity_all;

create view view_activity_all as

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
    , a.description
    , a.device_name
    , a.workout_type
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

DROP VIEW IF EXISTS view_activity;
CREATE VIEW view_activity AS
SELECT date(CASE WHEN o.offset_seconds IS NOT NULL THEN datetime(src.start_date,printf('%+d seconds',o.offset_seconds)) END) AS activity_date,
       cast(strftime('%Y%m%d',CASE WHEN o.offset_seconds IS NOT NULL THEN datetime(src.start_date,printf('%+d seconds',o.offset_seconds)) END) AS INTEGER) AS activity_date_key,
       a.activity_id AS activity_id,
       src.activity_id AS activity_key,
       a.activity_name AS activity_name,
       a.activity_type_key AS activity_type_key,
       a.average_cadence AS average_cadence,
       a.average_heartrate AS average_heartrate,
       a.average_speed_mph AS average_speed_mph,
       a.average_watts AS average_watts,
       a.calories AS calories,
       a.description AS description,
       a.device_name AS device_name,
       a.distance_miles AS distance_miles,
       src.elapsed_time_seconds AS elapsed_time_seconds,
       a.gear_key AS gear_key,
       a.is_commute AS is_commute,
       a.is_trainer AS is_trainer,
       a.kilojoules AS kilojoules,
       a.max_heartrate AS max_heartrate,
       a.max_speed_mph AS max_speed_mph,
       src.moving_time_seconds AS moving_time_seconds,
       a.segment_effort_count AS segment_effort_count,
       a.sport_type AS sport_type,
       CASE WHEN o.offset_seconds IS NOT NULL THEN datetime(src.start_date,printf('%+d seconds',o.offset_seconds)) END AS start_date,
       a.stream_point_count AS stream_point_count,
       a.suffer_score AS suffer_score,
       a.total_elevation_gain_feet AS total_elevation_gain_feet,
       a.workout_type AS workout_type,
       src.start_date AS start_date_utc,
       z.timezone_name AS timezone_name,
       coalesce(z.timezone_source,'unresolved') AS date_basis
FROM view_activity_all a JOIN activities src USING(activity_id)
LEFT JOIN reporting_activity_timezones z USING(activity_id)
LEFT JOIN reporting_timezone_offsets o ON o.activity_id=src.activity_id
    AND datetime(src.start_date)>=o.utc_start AND datetime(src.start_date)<o.utc_end
WHERE EXISTS (SELECT 1 FROM activity_points p WHERE p.activity_id=a.activity_id);
