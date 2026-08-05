drop view if exists view_date;

create view view_date as
with recursive
date_bounds as (
    select
        date(min(start_date_local)) as minimum_date,
        date(
            max(start_date_local),
            'start of year',
            '+1 year',
            '-1 day'
        ) as maximum_date
    from activities
),
calendar_dates as (
    select
        minimum_date as calendar_date,
        maximum_date
    from date_bounds

    union all

    select
        date(calendar_date, '+1 day'),
        maximum_date
    from calendar_dates
    where calendar_date < maximum_date
)
select
    cast(
        strftime('%Y%m%d', calendar_date)
        as integer
    ) as date_key,

    calendar_date as date,

    date(
        calendar_date,
        'start of year'
    ) as year,

    date(
        calendar_date,
        'start of month'
    ) as month,

    date(
        calendar_date,
        '-' || (
            cast(
                strftime('%m', calendar_date)
                as integer
            ) - 1
        ) % 3 || ' months',
        'start of month'
    ) as quarter,

    date(
        calendar_date,
        '-' || (
            (
                cast(
                    strftime('%w', calendar_date)
                    as integer
                ) + 6
            ) % 7
        ) || ' days'
    ) as week,

    cast(
        strftime('%m', calendar_date)
        as integer
    ) as month_number,

    cast(
        (
            (
                cast(
                    strftime('%m', calendar_date)
                    as integer
                ) - 1
            ) / 3
        ) + 1
        as integer
    ) as quarter_number,

    cast(
        strftime('%W', calendar_date)
        as integer
    ) + 1 as week_number,

    (
        (
            cast(
                strftime('%w', calendar_date)
                as integer
            ) + 6
        ) % 7
    ) + 1 as day_of_week_number,

    case
        when strftime('%w', calendar_date) in ('0', '6')
            then 1
        else 0
    end as is_weekend

from calendar_dates;