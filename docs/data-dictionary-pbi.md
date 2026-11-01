# Data dictionary in Power BI

`data_dictionary` is a visible, disconnected Power Query import table in the GPS
semantic model. Its embedded rows are generated from native TMDL metadata, including
maintenance and hidden objects, without runtime INFO.VIEW metadata queries. Its columns are:

| Column | Meaning |
|---|---|
| Object Type | Measure or Column |
| Object Name | Current native measure or column name |
| Table Name | Measure home table or column table |
| Description | Full native description, including filter and interpretation notes |
| Display Folder | Native display folder path; blank when unassigned |
| Data Type | Declared column type; measures show Inferred by DAX |
| Format String | Native format string; blank when unassigned |
| DAX Expression | Native DAX calculation for measures/calculated columns; blank for imported columns |
| Is Hidden | Native hidden flag; use false to show author-facing measures only |

All 189 columns across the 14 current fact, dimension and bridge tables now have
native descriptions alongside the existing measure descriptions. The analytical
column scope excludes `measures_` placeholders, field parameters and the dictionary
itself. Hidden technical columns are included for completeness.

Names, definitions and descriptions come from native TMDL metadata. The generator
writes a typed M `#table` into the dictionary partition, with no SQL view, Parquet
file, file path or new relationship. Table and column lineage IDs remain stable.
The catalog is a checked-in snapshot: regenerate it after editing native metadata,
then refresh Desktop. It does not update from Desktop-only metadata edits until
those edits are saved to TMDL and the generator is rerun.

## Apply and use

Close Desktop before checking out this fix. Reopen
`power_bi/gps/activity_tracking.pbip` and refresh/apply the model. No ETL, database
rebuild or Parquet re-export is needed. A normal full refresh still requires the
existing analytical Parquet files. If Desktop retains an old local model cache,
close Desktop, back up then remove only the project's ignored
`power_bi/gps/activity_tracking.SemanticModel/.pbi/cache.abf`, reopen and refresh.
Preserve other `.pbi` files and local report edits. This discards the imported cache,
so confirm the Parquet files are available before doing so.

The previous calculated-table implementation used `INFO.VIEW.MEASURES()` and
`INFO.VIEW.COLUMNS()`. After a Desktop internal `XMStringStore::StringByIndex` error
was reported, this implementation removes that runtime metadata calculation path.
The screenshot alone does not establish the underlying engine defect. Target
Desktop refresh remains required to verify the workaround.

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

## Validation

In Desktop, verify one row per native measure and scoped column (including maintenance),
no duplicate object-type/table/name triples, and exact description text
against Model view. Check a point-distance measure, a weekly/daily streak measure, a maintenance
measure and columns such as date_key, incremental_distance_miles and
service_interval_remaining_percent. Confirm folder/name slicers work and activity/date
slicers leave the catalog unchanged. Edit a native TMDL description temporarily, regenerate the dictionary and refresh
to confirm the change; undo the edit, regenerate and refresh again.
Publish and test the same visual from a thin report as an intended viewer.

Repository checks verify registration, isolation and the metadata column bindings.
They do not execute DAX or certify Desktop/Service refresh. Those checks remain
required on the target Power BI installation.

## Maintaining definitions

Update each measure or column's native TMDL `///` description with semantic changes,
then run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.tools.build_data_dictionary
.\.venv\Scripts\python.exe -m src.tools.build_data_dictionary --check
```

Commit the generated table with the native metadata changes. Tests reject stale
catalogs. New analytical tables are included automatically; helpers listed in the
generator are excluded. All included objects must have native descriptions. The
generator handles the checked-in TMDL convention rather than arbitrary TMDL syntax.
Use Object Type = Measure or Column to limit a reference visual. Maintenance usage
is based on whole source activities at export time, including non-GPS history;
GPS fields describe the point reporting scope.
