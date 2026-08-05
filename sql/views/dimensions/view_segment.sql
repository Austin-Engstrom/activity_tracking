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
    Exposes both metric and imperial distance and elevation fields.
===============================================================================
*/

drop view if exists view_segment;

create view view_segment as

select
      s.segment_id as segment_key
    , s.segment_id

    , s.name as segment_name
    , s.activity_type

    , s.distance_meters

    , s.distance_meters
        / 1609.344 as distance_miles

    , s.average_grade
    , s.maximum_grade

    , s.elevation_high_meters

    , s.elevation_high_meters
        * 3.280839895 as elevation_high_feet

    , s.elevation_low_meters

    , s.elevation_low_meters
        * 3.280839895 as elevation_low_feet

    , (
          s.elevation_high_meters
        - s.elevation_low_meters
      ) as elevation_range_meters

    , (
          s.elevation_high_meters
        - s.elevation_low_meters
      ) * 3.280839895 as elevation_range_feet

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

from segments s;