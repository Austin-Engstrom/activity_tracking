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
    Calculates both ride hours and ride miles since the most recent service.

    The component's service_interval_type determines whether maintenance
    status is evaluated using hours or miles.

    If no service event exists, the component installation date is used
    as the service baseline.

    Activities after a component removal date are excluded.
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
        , gc.service_interval_type
        , gc.service_interval_value
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

component_usage as (
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
                       >= datetime(cb.service_baseline_date)
                   and (
                          cb.removed_at is null
                          or datetime(a.start_date)
                             <= datetime(cb.removed_at)
                       )
                      then a.distance_meters
                  else 0
              end
          ) / 1609.344 as miles_since_service

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

        , sum(
              case
                  when datetime(a.start_date)
                       >= datetime(cb.installed_at)
                   and (
                          cb.removed_at is null
                          or datetime(a.start_date)
                             <= datetime(cb.removed_at)
                       )
                      then a.distance_meters
                  else 0
              end
          ) / 1609.344 as lifetime_component_miles

    from component_baseline cb

    left join activities a
        on cb.gear_id = a.gear_id

    group by
        cb.component_id
),

usage_calculation as (
    select
          cb.*
        , coalesce(cu.hours_since_service, 0.0)
            as hours_since_service
        , coalesce(cu.miles_since_service, 0.0)
            as miles_since_service
        , coalesce(cu.lifetime_component_hours, 0.0)
            as lifetime_component_hours
        , coalesce(cu.lifetime_component_miles, 0.0)
            as lifetime_component_miles

        , case
              when cb.service_interval_type = 'hours'
                  then coalesce(cu.hours_since_service, 0.0)

              when cb.service_interval_type = 'miles'
                  then coalesce(cu.miles_since_service, 0.0)
          end as usage_since_service

    from component_baseline cb

    left join component_usage cu
        on cb.component_id = cu.component_id
)

select
      uc.component_id as component_key
    , uc.component_id
    , uc.gear_id as gear_key

    , g.name as gear_name

    , uc.component_type
    , uc.manufacturer
    , uc.model

    , trim(
          coalesce(uc.manufacturer || ' ', '')
          || coalesce(uc.model, uc.component_type)
      ) as component_name

    , uc.installed_at
    , uc.removed_at

    , case
          when uc.removed_at is null then 1
          else 0
      end as is_active

    , uc.service_interval_type
    , uc.service_interval_value

    , uc.latest_service_id
    , uc.latest_service_date
    , uc.latest_service_type
    , uc.latest_service_notes

    , uc.service_baseline_date

    , cast(
          strftime(
              '%Y%m%d',
              date(uc.service_baseline_date)
          ) as integer
      ) as service_baseline_date_key

    , round(
          uc.hours_since_service,
          2
      ) as hours_since_service

    , round(
          uc.miles_since_service,
          2
      ) as miles_since_service

    , round(
          uc.lifetime_component_hours,
          2
      ) as lifetime_component_hours

    , round(
          uc.lifetime_component_miles,
          2
      ) as lifetime_component_miles

    , round(
          uc.usage_since_service,
          2
      ) as usage_since_service

    , round(
          uc.service_interval_value
          - uc.usage_since_service,
          2
      ) as usage_remaining

    , round(
          max(
              uc.usage_since_service
              - uc.service_interval_value,
              0.0
          ),
          2
      ) as usage_overdue

    , round(
          uc.usage_since_service
          / nullif(uc.service_interval_value, 0)
          * 100.0,
          2
      ) as service_interval_percent

    , case
          when uc.removed_at is not null
              then 'Inactive'

          when uc.service_interval_type is null
              then 'No Schedule'

          when uc.service_interval_value is null
              then 'No Schedule'

          when uc.usage_since_service
               >= uc.service_interval_value
              then 'Due'

          when uc.usage_since_service
               >= uc.service_interval_value * 0.80
              then 'Due Soon'

          else 'Current'
      end as service_status

    , uc.component_notes

from usage_calculation uc

left join gear g
    on uc.gear_id = g.gear_id;