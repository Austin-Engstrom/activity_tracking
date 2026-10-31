DROP VIEW IF EXISTS view_segment;
CREATE VIEW view_segment AS SELECT segment_id AS segment_key, segment_id,
 name AS segment_name, activity_type, distance_meters/1609.344 AS distance_miles,
 average_grade, maximum_grade, elevation_high_meters/0.3048 AS elevation_high_feet,
 elevation_low_meters/0.3048 AS elevation_low_feet, start_latitude,start_longitude,
 end_latitude,end_longitude,climb_category,city,state,country FROM segments;
