/*
===============================================================================
Script Name : build_views.sql

Purpose:
    Rebuilds all reporting views used by the Power BI semantic model.

Execution:
    Run from the activity_tracking project root:

    sqlite3 database/strava_analytics.db < sql/build_views.sql

Notes:
    Views must be listed in dependency order.
    Each view script is responsible for dropping and recreating its view.
===============================================================================
*/

.bail on

.print ''
.print '============================================================'
.print 'BUILDING DIMENSION VIEWS'
.print '============================================================'
.print ''

.print 'Creating view_date...'
.read sql/views/dimensions/view_date.sql

.print 'Creating view_activity_type...'
.read sql/views/dimensions/view_activity_type.sql

.print 'Creating view_gear...'
.read sql/views/dimensions/view_gear.sql

.print 'Creating view_segment...'
.read sql/views/dimensions/view_segment.sql

.print 'Creating view_official_trail...'
.read sql/views/dimensions/view_official_trail.sql

.print 'Creating view_trail_system...'
.read sql/views/dimensions/view_trail_system.sql

.print ''
.print '============================================================'
.print 'BUILDING FACT VIEWS'
.print '============================================================'
.print ''

.print 'Creating view_activity...'
.read sql/views/facts/view_activity.sql

.print 'Creating view_segment_effort...'
.read sql/views/facts/view_segment_effort.sql

.print 'Creating view_trail_activity...'
.read sql/views/facts/view_trail_activity.sql

.print 'Creating view_trail_progress...'
.read sql/views/facts/view_trail_progress.sql

.print 'Creating view_activity_stream_summary...'
.read sql/views/facts/view_activity_stream_summary.sql

.print 'Creating view_component_service_status...'
.read sql/views/facts/view_component_service_status.sql

.print ''
.print '============================================================'
.print 'REPORTING VIEWS BUILT SUCCESSFULLY'
.print '============================================================'
.print ''
.print ''
.print 'Reporting views currently available:'

select
    name
from sqlite_master
where type = 'view'
    and name like 'view_%'
order by name;

.print ''
.print '============================================================'
.print 'REPORTING VIEWS BUILT SUCCESSFULLY'
.print '============================================================'
.print ''