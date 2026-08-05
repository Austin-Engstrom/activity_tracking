/*
===============================================================================
View Name : view_activity_type

Purpose:
    Provides the activity-type dimension used to categorize Strava activities.

Grain:
    One row per distinct sport_type.

Dependencies:
    activities

Consumers:
    Power BI

Notes:
    The sport_type value serves as the dimension key because it is stable,
    descriptive, and already stored on each activity.
===============================================================================
*/

drop view if exists view_activity_type;

create view view_activity_type as

select distinct
      a.sport_type as activity_type_key
    , a.sport_type as activity_type

from activities a

where a.sport_type is not null

order by
    a.sport_type;