/*
===============================================================================
View Name : view_official_trail

Purpose:
    Provides the official-trail dimension used for GPS-derived trail activity
    and lifetime trail-progress reporting.

Grain:
    One row per official_trail_id.

Dependencies:
    official_trails
    trail_systems

Consumers:
    Power BI

Notes:
    Trail-system attributes are flattened into the dimension to support a
    cleaner Power BI star schema. Official trail length is reported in miles.
    Large GeoJSON fields are intentionally excluded from the reporting view.
===============================================================================
*/

drop view if exists view_official_trail;

create view view_official_trail as

select
      ot.official_trail_id as official_trail_key
    , ot.official_trail_id
    , ot.trail_system_id as trail_system_key
    , ts.name as trail_system_name
    , ts.city as trail_system_city
    , ts.state as trail_system_state
    , ts.country as trail_system_country
    , ts.latitude as trail_system_latitude
    , ts.longitude as trail_system_longitude
    , ot.name as official_trail_name
    , ot.normalized_name
    , round(ot.total_length_meters / 1609.344, 2) as total_length_miles
    , ot.section_count
    , ot.primary_surface
    , ot.bicycle_access
    , ot.mtb_scale
    , ot.mtb_type
    , ts.boundary_source
    , ts.boundary_confirmed
    , ts.osm_element_type
    , ts.osm_element_id
    , ts.osm_display_name
    , ot.created_at
    , ot.updated_at
from official_trails ot
inner join trail_systems ts
    on ot.trail_system_id = ts.trail_system_id;
