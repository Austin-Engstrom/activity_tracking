/*
===============================================================================
View Name : view_trail_system

Purpose:
    Provides trail-system attributes and current network-level summary metrics.

Grain:
    One row per trail_system_id.

Dependencies:
    trail_systems
    official_trails
    official_trail_progress

Consumers:
    Power BI

Notes:
    Trail-system attributes are also flattened into view_official_trail.
    This view supports trail-system maps, cards, rankings, and summaries.
    All distance measures are reported in miles.
===============================================================================
*/

drop view if exists view_trail_system;

create view view_trail_system as

with trail_summary as (
    select
          ot.trail_system_id
        , count(*) as official_trail_count
        , sum(ot.section_count) as assigned_osm_section_count
        , round(sum(ot.total_length_meters) / 1609.344, 2) as official_trail_length_miles
        , sum(case when coalesce(otp.progress_status, 'unridden') = 'completed' then 1 else 0 end) as completed_trail_count
        , sum(case when coalesce(otp.progress_status, 'unridden') = 'nearly_complete' then 1 else 0 end) as nearly_complete_trail_count
        , sum(case when coalesce(otp.progress_status, 'unridden') = 'partial' then 1 else 0 end) as partial_trail_count
        , sum(case when coalesce(otp.progress_status, 'unridden') = 'started' then 1 else 0 end) as started_trail_count
        , sum(case when coalesce(otp.progress_status, 'unridden') = 'unridden' then 1 else 0 end) as unridden_trail_count
        , round(
              sum(
                  ot.total_length_meters
                  * coalesce(otp.estimated_coverage_percent, 0)
                  / 100.0
              ) / 1609.344
            , 2
          ) as unique_covered_distance_miles
        , round(
              sum(
                  ot.total_length_meters
                  * (100.0 - coalesce(otp.estimated_coverage_percent, 0))
                  / 100.0
              ) / 1609.344
            , 2
          ) as remaining_distance_miles
        , round(
              sum(
                  ot.total_length_meters
                  * coalesce(otp.estimated_coverage_percent, 0)
                  / 100.0
              )
              / nullif(sum(ot.total_length_meters), 0)
              * 100.0
            , 2
          ) as weighted_completion_percent
    from official_trails ot
    left join official_trail_progress otp
        on ot.official_trail_id = otp.official_trail_id
    group by ot.trail_system_id
)
select
      ts.trail_system_id as trail_system_key
    , ts.trail_system_id
    , ts.name as trail_system_name
    , ts.city
    , ts.state
    , ts.country
    , ts.latitude
    , ts.longitude
    , ts.description
    , ts.osm_element_type
    , ts.osm_element_id
    , ts.osm_display_name
    , ts.boundary_source
    , ts.boundary_confirmed
    , ts.boundary_updated_at
    , coalesce(summary.official_trail_count, 0) as official_trail_count
    , coalesce(summary.assigned_osm_section_count, 0) as assigned_osm_section_count
    , coalesce(summary.official_trail_length_miles, 0.0) as official_trail_length_miles
    , coalesce(summary.completed_trail_count, 0) as completed_trail_count
    , coalesce(summary.nearly_complete_trail_count, 0) as nearly_complete_trail_count
    , coalesce(summary.partial_trail_count, 0) as partial_trail_count
    , coalesce(summary.started_trail_count, 0) as started_trail_count
    , coalesce(summary.unridden_trail_count, 0) as unridden_trail_count
    , coalesce(summary.unique_covered_distance_miles, 0.0) as unique_covered_distance_miles
    , coalesce(summary.remaining_distance_miles, 0.0) as remaining_distance_miles
    , coalesce(summary.weighted_completion_percent, 0.0) as weighted_completion_percent
    , ts.created_at
    , ts.updated_at
from trail_systems ts
left join trail_summary summary
    on ts.trail_system_id = summary.trail_system_id;
