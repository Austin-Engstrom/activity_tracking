# Strava Analytics

A personal data engineering and business intelligence project.

## Architecture

Strava API
    ↓
Python ETL
    ↓
SQLite
    ↓
Power BI

## Goals

- Automatically sync Strava activities
- Store activities in a relational database
- Build a dimensional model
- Create interactive Power BI dashboards
- Track bike usage and maintenance
- Analyze long-term training trends

## GPS reporting redesign

See [schema, measurement rules, and migration steps](docs/gps-schema.md).
The new point-grain Power BI semantic model is in `power_bi/gps`.

See the [dataset measure library](docs/measure-library.md) for adapted measures,
filter behavior and Power BI validation steps, and [Quanta Check](docs/quanta-check.md)
for the dataset's single-page validation report.

[Observed segment associations](docs/segment-trail-associations.md) explains the
segment/trail/system bridge, local installation and Power BI usage.

[Weekly consistency measures](docs/activity-consistency.md) cover active weeks,
local active days and slicer-aware consecutive-week streaks.

All dataset measures include [native Power BI descriptions](docs/measure-descriptions.md)
with their meaning, filter behavior and interpretation notes.

[Selection field parameters](docs/selection-parameters.md) provide dynamic measure
and dimension choices for visuals without changing the star-schema relationships.

[Data dictionary](docs/data-dictionary-pbi.md) exposes native measure and analytical column definitions, folders and DAX as reportable rows in the GPS model.

## Publishing and report building

Start with the [publishing handoff and manual refresh runbook](docs/publishing-handoff.md),
[exported data dictionary](docs/data-dictionary.md) and [proposed report outline](docs/report-outline.md).
The handoff includes a release validation record; Desktop and deployed-model checks
remain manual.

## Cycling report draft

Open `power_bi/report/draft.pbip` for the five-page cycling report connected to the
published semantic model. See the [layout and Desktop review notes](docs/cycling-report.md).
