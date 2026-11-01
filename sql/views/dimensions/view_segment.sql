DROP VIEW IF EXISTS view_segment;
CREATE VIEW view_segment AS SELECT segment_id AS segment_key, segment_id,
 name AS segment_name, activity_type, distance_meters/1609.344 AS distance_miles,
 average_grade, maximum_grade, elevation_high_meters/0.3048 AS elevation_high_feet,
 elevation_low_meters/0.3048 AS elevation_low_feet, start_latitude,start_longitude,
 end_latitude,end_longitude,climb_category,city,state,country FROM segments s
WHERE EXISTS (
    SELECT 1 FROM segment_efforts e
    WHERE e.segment_id = s.segment_id
      AND EXISTS (SELECT 1 FROM activity_points p WHERE p.activity_id = e.activity_id)
);
