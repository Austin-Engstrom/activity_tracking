-- One fastest known visible positive-time GPS effort per segment, not an official lifetime PR.
DROP VIEW IF EXISTS view_segment_personal_best;
CREATE VIEW view_segment_personal_best AS
WITH counts AS (
    SELECT segment_key, count(*) AS stored_effort_count,
           sum(eligible_for_stored_best) AS eligible_effort_count
    FROM view_segment_effort_achievement GROUP BY segment_key
), ranked AS (
    SELECT e.*,
           row_number() OVER (PARTITION BY segment_key ORDER BY elapsed_time_seconds,effort_started_at_utc,segment_effort_key) AS position,
           count(*) OVER (PARTITION BY segment_key,elapsed_time_seconds) AS tied_best_effort_count
    FROM view_segment_effort_achievement e WHERE eligible_for_stored_best=1
)
SELECT r.segment_key,r.segment_effort_key AS best_segment_effort_key,
       r.activity_key AS best_activity_key,
       r.effort_started_at AS best_effort_started_at,
       r.effort_started_at_utc AS best_effort_started_at_utc,
       r.date_basis, r.timezone_name,
       r.effort_local_date AS best_effort_local_date,
       r.elapsed_time_seconds AS best_elapsed_time_seconds,
       r.moving_time_seconds AS best_moving_time_seconds,
       r.distance_miles AS best_distance_miles,
       c.stored_effort_count,c.eligible_effort_count,r.tied_best_effort_count,
       r.reported_pr_rank,r.reported_kom_rank,r.ranks_retrieved_at,
       r.pr_rank_status,r.kom_rank_status,
       r.activity_url,r.segment_url,
       'fastest_visible_positive_time_in_stored_gps_history' AS best_basis
FROM ranked r JOIN counts c USING(segment_key) WHERE r.position=1;
