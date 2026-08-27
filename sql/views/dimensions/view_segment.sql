/*
===============================================================================
View Name : view_segment

Purpose:
    Provides the segment dimension used to analyze Strava segment efforts.

Grain:
    One row per segment_id.

Dependencies:
    segments

Consumers:
    Power BI

Notes:
    Exposes reporting measures using imperial units. Distance is reported in
    miles and elevation in feet.
===============================================================================
*/

drop view if exists view_segment;

create view view_segment as

select
      s.segment_id as segment_key
    , s.segment_id
    , s.name as segment_name
    , s.activity_type
    , round(s.distance_meters / 1609.344, 2) as distance_miles
    , round(s.average_grade, 2) as average_grade
    , round(s.maximum_grade, 2) as maximum_grade
    , round(s.elevation_high_meters * 3.280839895, 2) as elevation_high_feet
    , round(s.elevation_low_meters * 3.280839895, 2) as elevation_low_feet
    , round((s.elevation_high_meters - s.elevation_low_meters) * 3.280839895, 2) as elevation_range_feet
    , s.start_latitude
    , s.start_longitude
    , s.end_latitude
    , s.end_longitude
    , s.climb_category
    , s.city
    , s.state
    , s.country
    , s.private as is_private
    , s.hazardous as is_hazardous
    , s.starred as is_starred
    , s.effort_count
    , s.athlete_count
    , s.star_count
    , s.created_at
    , s.updated_at
    , sts.trail_system_id as trail_system_key
from segments s
left join segment_trail_systems sts
    on s.segment_id = sts.segment_id;
