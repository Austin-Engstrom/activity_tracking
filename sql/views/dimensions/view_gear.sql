/*
===============================================================================
View Name : view_gear

Purpose:
    Provides the gear dimension used to analyze activities by bike or other
    Strava equipment.

Grain:
    One row per gear_id.

Dependencies:
    gear

Consumers:
    Power BI

Notes:
    Metric and imperial lifetime-distance fields are both exposed.
===============================================================================
*/

drop view if exists view_gear;

create view view_gear as

select
      g.gear_id as gear_key
    , g.gear_id

    , g.name as gear_name
    , g.brand_name
    , g.model_name
    , g.description

    , g.distance_meters

    , g.distance_meters
        / 1609.344 as distance_miles

    , g.primary as is_primary

    , g.frame_type

    , g.created_at
    , g.updated_at

from gear g;