-- Observed relationships across verified history, not geographic ownership.
DROP VIEW IF EXISTS view_segment_trail_association;
CREATE VIEW view_segment_trail_association AS
WITH memberships AS (
    SELECT m.segment_key, m.segment_effort_key, e.activity_id,
           p.trail_key, p.trail_system_key, p.recorded_at_utc,
           CASE WHEN p.point_index > e.start_index
                THEN p.incremental_distance_meters END AS distance_meters
    FROM view_activity_point_segments m
    JOIN segment_efforts e ON e.segment_effort_id = m.segment_effort_key
    JOIN activity_points p ON p.activity_point_key = m.activity_point_key
),
segment_totals AS (
    SELECT segment_key, sum(distance_meters) AS distance_meters
    FROM memberships
    GROUP BY segment_key
),
associations AS (
    SELECT segment_key, trail_key, trail_system_key,
           count(DISTINCT segment_effort_key) AS supporting_efforts,
           count(DISTINCT activity_id) AS supporting_activities,
           count(*) AS point_memberships,
           sum(distance_meters) AS distance_meters,
           min(recorded_at_utc) AS first_observed_at,
           max(recorded_at_utc) AS last_observed_at
    FROM memberships
    WHERE trail_key IS NOT NULL OR trail_system_key IS NOT NULL
    GROUP BY segment_key, trail_key, trail_system_key
)
SELECT a.segment_key, a.trail_key, a.trail_system_key,
       a.supporting_efforts, a.supporting_activities, a.point_memberships,
       a.distance_meters / 1609.344 AS observed_distance_miles,
       a.distance_meters / nullif(t.distance_meters, 0) AS observed_distance_share,
       a.first_observed_at, a.last_observed_at,
       'verified_point_assignments' AS association_basis,
       CASE WHEN a.distance_meters > 0 THEN 'distance_supported'
            ELSE 'point_only' END AS evidence_status
FROM associations a
JOIN segment_totals t ON t.segment_key = a.segment_key;
