Strava Activity Tracking --- PowerShell Command Reference

A quick reference for commonly used PowerShell commands in the Strava
Activity Tracking project.

Core ETL Commands

Run the main Strava ETL pipeline
``` powershel
python -m src.main
```
Use this for the normal day-to-day incremental refresh.

Export Power BI Parquet files
``` powershell
python -m src.export_power_bi
```

Use this when the database is already current and you only need to
regenerate the files in exports\power_bi.

Trail Mapping

Run spatial segment-to-trail-system mapping
``` powershell
python -m src.tools.run_spatial_trail_mapping
```
Run this after adding or changing trail-system boundaries.

Import manual trail-system boundaries

``` powershell
python -m src.tools.import_manual_boundaries
```

After importing boundaries, rerun spatial mapping:

``` powershell
python -m src.tools.run_spatial_trail_mapping
```

Open the interactive trail-system mapping tool

``` powershell
python -m src.tools.map_trail_systems
```

Official Trail Data

Import official trails

``` powershell
python -m src.tools.import_official_trails
```

Use this for the OSM/official-trail portion of the pipeline.

Reporting Views

Rebuild SQLite reporting views

Run this after modifying sql\build_views.sql:

``` powershell
python -c "import sqlite3; from pathlib import Path; conn = sqlite3.connect('database/strava_analytics.db'); conn.executescript(Path('sql/build_views.sql').read_text()); conn.close(); print('Views rebuilt successfully.')"
```

Then regenerate the Power BI Parquet exports:
``` powershell
python -m src.export_power_bi
```

Typical reporting-view update sequence

``` powershell
python -c "import sqlite3; from pathlib import Path; conn = sqlite3.connect('database/strava_analytics.db'); conn.executescript(Path('sql/build_views.sql').read_text()); conn.close(); print('Views rebuilt successfully.')"
```

``` powershell
python -m src.export_power_bi
```

Python Environment

Activate the Windows virtual environment

``` powershell
.\.venv\Scripts\Activate.ps1
```

Install project dependencies

``` powershell
pip install -r requirements.txt
```

Install Shapely

``` powershell
pip install shapely
```

# Normal ETL refresh

``` powershell
python -m src.main
```

# Rebuild reporting views

``` powershell
python -c "import sqlite3; from pathlib import Path; conn = sqlite3.connect('database/strava_analytics.db'); conn.executescript(Path('sql/build_views.sql').read_text()); conn.close(); print('Views rebuilt successfully.')"
```

# Re-export Power BI data

``` powershell
python -m src.export_power_bi
```
# Re-run trail-system spatial mapping

``` powershell
python -m src.tools.run_spatial_trail_mapping
```