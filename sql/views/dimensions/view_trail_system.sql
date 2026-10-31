DROP VIEW IF EXISTS view_trail_system;
CREATE VIEW view_trail_system AS SELECT trail_system_id AS trail_system_key,
name AS trail_system_name,city,state,country,latitude,longitude,description,
boundary_source,boundary_confirmed,osm_element_type,osm_element_id
FROM trail_systems;
