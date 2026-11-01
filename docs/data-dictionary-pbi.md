# Data dictionary in Power BI

`data_dictionary` is a visible, disconnected calculated table in the GPS semantic
model. It contains one row per measure from `INFO.VIEW.MEASURES()` and per analytical column
from `INFO.VIEW.COLUMNS()`, including maintenance and hidden objects. Its columns are:

| Column | Meaning |
|---|---|
| Object Type | Measure or Column |
| Object Name | Current native measure or column name |
| Table Name | Measure home table or column table |
| Description | Full native description, including filter and interpretation notes |
| Display Folder | Native display folder path; blank when unassigned |
| Data Type | Native metadata data type |
| Format String | Native format string; blank when unassigned |
| DAX Expression | Native DAX calculation for measures/calculated columns; blank for imported columns |
| Is Hidden | Native hidden flag; use false to show author-facing measures only |

All 189 columns across the 14 current fact, dimension and bridge tables now have
native descriptions alongside the existing measure descriptions. The analytical
column scope excludes `measures_` placeholders, field parameters and the dictionary
itself. Hidden technical columns are included for completeness.

Names, definitions and descriptions come directly from model metadata, with no
hand-maintained duplicate list, SQL views, Parquet files or new relationships.
Missing descriptions stay blank so documentation gaps remain visible. The table
contains metadata, not evaluated measure values. It updates on model recalculation/
refresh; it is not a live query of metadata every time a viewer opens a page.

## Apply and use

Close Desktop before checking out the branch, then reopen
`power_bi/gps/activity_tracking.pbip` in a current Power BI Desktop version that
supports `INFO.VIEW.MEASURES()` and `INFO.VIEW.COLUMNS()` in calculated tables. Refresh/recalculate the model
to populate the dictionary. No ETL, database rebuild or Parquet re-export is needed;
normal full Desktop refresh still requires access to the existing export files.

Create a table visual using **Object Type**, **Table Name**, **Object Name**, **Display Folder** and
**Description** from `data_dictionary`. Enable value text wrapping and give the
description column sufficient width. Add searchable slicers on Object Type, Table Name, Object Name and
Display Folder; add Is Hidden = false if desired. DAX Expression and Format String
are optional detail columns. Do not add the actual measures to this visual: they
would calculate results rather than display definitions. No page layout is changed
by this implementation.

Activity/date/trail slicers intentionally do not filter the disconnected catalog.
Dictionary slicers filter its rows normally. Publish the shared model after refresh;
connected thin reports can use these columns without issuing metadata queries.
Readers see the stored dictionary rows. DAX expressions and descriptions are thus
report-accessible metadata, not confidential author-only properties. Review that
content as part of normal publication.

The metadata function requires appropriate model permissions for calculation;
perform Desktop refresh as the model author/owner. Older engines or unsupported
connection modes can reject it: update Desktop/use the imported shared model
workflow rather than silently maintaining a stale fallback snapshot.

## Validation

In Desktop, verify one row per native measure and scoped column (including maintenance),
no duplicate object-type/table/name triples, and exact description text
against Model view. Check a point-distance measure, a weekly/daily streak measure, a maintenance
measure and columns such as date_key, incremental_distance_miles and
service_interval_remaining_percent. Confirm folder/name slicers work and activity/date
slicers leave the catalog unchanged. Edit a native measure or column description temporarily,
recalculate and confirm the dictionary changes; undo the edit and recalculate.
Publish and test the same visual from a thin report as an intended viewer.

Repository checks verify registration, isolation and the metadata column bindings.
They do not execute DAX or certify Desktop/Service refresh. Those checks remain
required on the target Power BI installation.

## Maintaining definitions

Update each measure or column's native TMDL `///` description with semantic changes.
The dictionary materializes those descriptions; do not edit its rows. Use Object
Type = Measure for the original measure-only visual, or Column for field reference.
To include a new analytical table, add its name to the column filter in
`tables/data_dictionary.tmdl` and document its fields. The column whitelist avoids
self-references and internal helper rows. Current maintenance usage is calculated
from whole source activities at export time, including non-GPS activity history;
GPS point fields describe the GPS reporting scope. Table/name context distinguishes
shared field names with different grains.
