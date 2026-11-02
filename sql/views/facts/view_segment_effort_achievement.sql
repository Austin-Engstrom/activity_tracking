-- Latest reported rankings for every stored effort in GPS-eligible activities.
DROP VIEW IF EXISTS view_segment_effort_achievement;
CREATE VIEW view_segment_effort_achievement AS
SELECT e.segment_effort_id AS segment_effort_key,
       e.segment_id AS segment_key, e.activity_id AS activity_key,
       g.gear_id AS gear_key, a.sport_type AS activity_type_key,
       CASE WHEN o.offset_seconds IS NOT NULL THEN datetime(e.start_date,printf('%+d seconds',o.offset_seconds)) ELSE datetime(e.start_date_local) END AS effort_started_at,
       e.start_date AS effort_started_at_utc,
       date(CASE WHEN o.offset_seconds IS NOT NULL THEN datetime(e.start_date,printf('%+d seconds',o.offset_seconds)) ELSE datetime(e.start_date_local) END) AS effort_local_date,
       cast(strftime('%Y%m%d',CASE WHEN o.offset_seconds IS NOT NULL THEN datetime(e.start_date,printf('%+d seconds',o.offset_seconds)) ELSE datetime(e.start_date_local) END) AS INTEGER) AS date_key,
       CASE WHEN o.offset_seconds IS NOT NULL THEN z.timezone_source
            WHEN e.start_date_local IS NOT NULL THEN 'source_local' ELSE 'unresolved' END AS date_basis,
       z.timezone_name,
       e.elapsed_time_seconds, e.moving_time_seconds,
       e.distance_meters / 1609.344 AS distance_miles,
       e.hidden AS effort_hidden,
       e.pr_rank AS reported_pr_rank, e.kom_rank AS reported_kom_rank,
       m.retrieved_at AS ranks_retrieved_at,
       CASE WHEN m.segment_effort_id IS NULL THEN 'legacy_unobserved'
            WHEN m.pr_rank_returned=0 THEN 'not_returned'
            WHEN e.pr_rank IS NULL THEN 'no_rank' ELSE 'ranked' END AS pr_rank_status,
       CASE WHEN m.segment_effort_id IS NULL THEN 'legacy_unobserved'
            WHEN m.kom_rank_returned=0 THEN 'not_returned'
            WHEN e.kom_rank IS NULL THEN 'no_rank' ELSE 'ranked' END AS kom_rank_status,
       CASE WHEN m.pr_rank_returned=1 THEN CASE WHEN e.pr_rank=1 THEN 1 ELSE 0 END END AS reported_pr_first,
       CASE WHEN m.kom_rank_returned=1 THEN CASE WHEN e.kom_rank=1 THEN 1 ELSE 0 END END AS reported_kom_first,
       CASE WHEN e.elapsed_time_seconds>0 AND coalesce(e.hidden,0)=0 THEN 1 ELSE 0 END AS eligible_for_stored_best,
       'https://www.strava.com/activities/' || e.activity_id AS activity_url,
       'https://www.strava.com/segments/' || e.segment_id AS segment_url
FROM segment_efforts e JOIN activities a ON a.activity_id=e.activity_id
LEFT JOIN reporting_activity_timezones z ON z.activity_id=e.activity_id
LEFT JOIN reporting_timezone_offsets o ON o.activity_id=e.activity_id
 AND datetime(e.start_date)>=o.utc_start AND datetime(e.start_date)<o.utc_end
LEFT JOIN gear g ON g.gear_id=a.gear_id
LEFT JOIN segment_effort_record_metadata m ON m.segment_effort_id=e.segment_effort_id
WHERE EXISTS (SELECT 1 FROM activity_points p WHERE p.activity_id=e.activity_id);
