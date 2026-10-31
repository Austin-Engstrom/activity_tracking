DROP VIEW IF EXISTS view_point_segment_effort;
CREATE VIEW view_point_segment_effort AS SELECT e.segment_effort_id AS segment_effort_key,
 e.activity_id AS activity_key,e.segment_id AS segment_key,e.start_index,e.end_index,
 e.elapsed_time_seconds,e.moving_time_seconds,e.distance_meters/1609.344 AS distance_miles
FROM segment_efforts e WHERE EXISTS (SELECT 1 FROM activity_points p WHERE p.activity_id=e.activity_id);
