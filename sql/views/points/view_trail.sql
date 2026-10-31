DROP VIEW IF EXISTS view_trail;
CREATE VIEW view_trail AS SELECT official_trail_id AS trail_key, name AS trail_name,
 normalized_name, total_length_meters / 1609.344 AS length_miles,
 primary_surface, bicycle_access, mtb_scale, mtb_type
FROM official_trails;
