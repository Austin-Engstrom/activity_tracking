# Component maintenance

Edit `data/maintenance/gear_components.csv` and `component_services.csv`, then run:

```sh
python -m src.tools.import_maintenance
python -m src.tools.export_power_bi
```

Load gear and activities into the local database first. Components referencing
unknown gear are skipped; the importer reports counts. The cloud checkout's
database may be empty and is separate from your local database.

The importer accepts ISO dates and US month/day/year dates, normalizes them to
ISO, upserts components and service history, and rebuilds the three maintenance
views. It does not delete rows omitted from a CSV.

The default export includes `view_gear_components.parquet`,
`view_component_services.parquet`, and `view_component_service_status.parquet`.
They have explicit types even when empty. The GPS Power BI model imports them
through ExportFolder and relates services and status to components, and
components to gear.

Status is a current snapshot per component, using all available activity totals
on its gear, not GPS point coverage or report date filters. Moving seconds become
hours; meters become miles. Usage starts at installation or the latest recorded
service within the installed period, and stops at removal. Every service record
resets the interval; use separate component schedules if different service types
need independent clocks. Date-only service records include rides on that day.

`service_interval_remaining_percent` is a ratio (0.5 = 50% remaining), clamped at
zero when due. `service_interval_remaining` is nonnegative hours or miles,
selected by `service_interval_type`. `usage_remaining` retains a negative value
when overdue, and `usage_overdue` reports the excess. The existing
`service_interval_percent` is percent **used**, on a 0–100 scale and can exceed
100. Status becomes Due Soon at 80% used and Due at 100%; removed parts are Inactive.

Use component name/type with the Maintenance measures: Service Interval Remaining
%, Service Interval Remaining, Service Interval Unit, and Next Service Remaining.
These measures return blank across multiple components, avoiding totals that mix
hours and miles.
