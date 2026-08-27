/*
===============================================================================
View Name : view_component_service_status

Purpose:
    Provides the current maintenance status for each tracked gear component.

Grain:
    One row per component_id.

Dependencies:
    gear_components
    component_services
    gear
    activities

Consumers:
    Power BI

Notes:
    Ride hours are calculated from activity moving time for the gear on which
    the component is installed.

    The most recent service event resets the service interval. If no service
    event exists, the component installation date is used as the baseline.

    Activities after a component removal date are excluded.

    Hours remaining may be negative when a component is overdue for service.
===============================================================================
*/

drop view if exists view_component_service_status;

create view view_component_service_status as

with latest_service as (
    select
          cs.component_id
        , cs.service_id
        , cs.service_date
        , cs.service_type
        , cs.notes as service_notes
        , row_number() over (
              partition by cs.component_id
              order by
                    datetime(cs.service_date) desc
                  , cs.service_id desc
          ) as service_rank
    from component_services cs
),

component_baseline as (
    select
          gc.component_id
        , gc.gear_id
        , gc.component_type
        , gc.manufacturer
        , gc.model
        , gc.installed_at
        , gc.removed_at
        , gc.service_interval_hours
        , gc.notes as component_notes

        , ls.service_id as latest_service_id
        , ls.service_date as latest_service_date
        , ls.service_type as latest_service_type
        , ls.service_notes as latest_service_notes

        , coalesce(
              ls.service_date,
              gc.installed_at
          ) as service_baseline_date

    from gear_components gc

    left join latest_service ls
        on gc.component_id = ls.component_id
       and ls.service_rank = 1
),

ride_time as (
    select
          cb.component_id

        , sum(
              case
                  when datetime(a.start_date)
                       >= datetime(cb.service_baseline_date)
                   and (
                          cb.removed_at is null
                          or datetime(a.start_date)
                             <= datetime(cb.removed_at)
                       )
                      then a.moving_time_seconds
                  else 0
              end
          ) / 3600.0 as hours_since_service

        , sum(
              case
                  when datetime(a.start_date)
                       >= datetime(cb.installed_at)
                   and (
                          cb.removed_at is null
                          or datetime(a.start_date)
                             <= datetime(cb.removed_at)
                       )
                      then a.moving_time_seconds
                  else 0
              end
          ) / 3600.0 as lifetime_component_hours

    from component_baseline cb

    left join activities a
        on cb.gear_id = a.gear_id

    group by
        cb.component_id
)

select
      cb.component_id as component_key
    , cb.component_id
    , cb.gear_id as gear_key

    , g.name as gear_name

    , cb.component_type
    , cb.manufacturer
    , cb.model

    , trim(
          coalesce(cb.manufacturer || ' ', '')
          || coalesce(cb.model, cb.component_type)
      ) as component_name

    , cb.installed_at
    , cb.removed_at

    , case
          when cb.removed_at is null then 1
          else 0
      end as is_active

    , cb.service_interval_hours

    , cb.latest_service_id
    , cb.latest_service_date
    , cb.latest_service_type
    , cb.latest_service_notes

    , cb.service_baseline_date

    , cast(
          strftime(
              '%Y%m%d',
              date(cb.service_baseline_date)
          ) as integer
      ) as service_baseline_date_key

    , round(
          coalesce(rt.hours_since_service, 0.0),
          2
      ) as hours_since_service

    , round(
          coalesce(rt.lifetime_component_hours, 0.0),
          2
      ) as lifetime_component_hours

    , round(
          cb.service_interval_hours
          - coalesce(rt.hours_since_service, 0.0),
          2
      ) as hours_remaining

    , round(
          max(
              coalesce(rt.hours_since_service, 0.0)
              - cb.service_interval_hours,
              0.0
          ),
          2
      ) as hours_overdue

    , round(
          coalesce(rt.hours_since_service, 0.0)
          / nullif(cb.service_interval_hours, 0)
          * 100.0,
          2
      ) as service_interval_percent

    , case
          when cb.removed_at is not null
              then 'Inactive'

          when cb.service_interval_hours is null
              then 'No Schedule'

          when coalesce(rt.hours_since_service, 0.0)
               >= cb.service_interval_hours
              then 'Due'

          when coalesce(rt.hours_since_service, 0.0)
               >= cb.service_interval_hours * 0.80
              then 'Due Soon'

          else 'Current'
      end as service_status

    , cb.component_notes

from component_baseline cb

left join ride_time rt
    on cb.component_id = rt.component_id

left join gear g
    on cb.gear_id = g.gear_id;