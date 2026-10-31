DROP VIEW IF EXISTS view_activity_point_segments;
CREATE VIEW view_activity_point_segments AS SELECT p.activity_point_key,
 e.segment_effort_id AS segment_effort_key, e.segment_id AS segment_key
FROM activity_points p JOIN stream_index_alignment alignment ON alignment.activity_id=p.activity_id AND alignment.verified=1
JOIN segment_efforts e ON e.activity_id=p.activity_id
 AND p.point_index BETWEEN e.start_index AND e.end_index;
