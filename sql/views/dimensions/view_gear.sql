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
    Exposes lifetime gear distance in miles.
===============================================================================
*/

drop view if exists view_gear;

create view view_gear as

select
      g.gear_id as gear_key
    , g.gear_id
    , g.athlete_id
    , g.name as gear_name
    , g.brand_name
    , g.model_name
    , g.description
    , round(g.distance_meters / 1609.344, 2) as distance_miles
    , g.is_primary
    , g.is_retired
    , g.frame_type
    , g.detail_loaded_at
    , g.created_at
    , g.updated_at
from gear g;
