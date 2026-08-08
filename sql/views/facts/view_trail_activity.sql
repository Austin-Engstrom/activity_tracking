/*
===============================================================================
View Name : view_trail_activity

Purpose:
    Provides GPS-derived activity usage for official trails.

Grain:
    One row per official_trail_id and activity_id combination.

Dependencies:
    official_trail_activity_matches
    activities

Consumers:
    Power BI

Notes:
    Supports trail ride counts, repeated trail mileage, activity-level trail
    coverage, gear analysis, and time trends. Activity dates use the stored
    activity start_date value.
===============================================================================
*/

drop view if exists view_trail_activity;

create view view_trail_activity as

select
      otam.official_trail_activity_match_id

    , otam.official_trail_id as official_trail_key
    , otam.activity_id

    , cast(
          strftime(
              '%Y%m%d'
            , date(a.start_date)
          )
          as integer
      ) as activity_date_key

    , a.sport_type as activity_type_key
    , a.gear_id as gear_key

    , a.name as activity_name
    , a.start_date

    , otam.matched_trail_length_meters

    , otam.matched_trail_length_meters
        / 1609.344 as matched_trail_length_miles

    , otam.ridden_distance_meters

    , otam.ridden_distance_meters
        / 1609.344 as ridden_distance_miles

    , otam.trail_coverage_percent
    , otam.matched_point_count

    , otam.tolerance_meters

    , otam.created_at
    , otam.updated_at

from official_trail_activity_matches otam

inner join activities a
    on otam.activity_id = a.activity_id;