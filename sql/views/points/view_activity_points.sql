DROP VIEW IF EXISTS view_activity_points;
CREATE VIEW view_activity_points AS
SELECT p.activity_point_key, p.activity_id AS activity_key, p.activity_id,
 p.point_index, g.gear_id AS gear_key, a.sport_type AS activity_type_key,
 p.date_key, p.trail_system_key, p.trail_key, p.recorded_at_utc,
 s.latitude, s.longitude, s.time_seconds AS elapsed_time_seconds,
 s.distance_meters / 1609.344 AS cumulative_distance_miles,
 p.incremental_distance_meters / 1609.344 AS incremental_distance_miles,
 p.incremental_time_seconds,
 CASE WHEN s.is_moving=1 THEN p.incremental_time_seconds WHEN s.is_moving=0 THEN 0 END AS moving_time_seconds,
 s.altitude_meters / 0.3048 AS elevation_feet,
 s.velocity_mps * 3600 / 1609.344 AS speed_mph,
 s.temperature_c * 1.8 + 32 AS temperature_f,
 s.heartrate, s.cadence, s.watts, s.is_moving, s.grade_percent,
 p.quality_status, p.match_method,
 CASE WHEN m.timezone_name IS NULL THEN 'utc_fallback' ELSE 'activity_timezone' END AS date_basis
FROM activity_points p JOIN activity_streams s USING(activity_id,point_index)
JOIN activities a USING(activity_id)
LEFT JOIN gear g ON g.gear_id=a.gear_id
LEFT JOIN point_reporting_metadata m USING(activity_id);
