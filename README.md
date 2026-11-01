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
