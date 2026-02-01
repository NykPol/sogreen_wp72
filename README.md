# SoGreen Task 7.2: Extracting geospatial information from maps
This project was developed at the SGH Warsaw School of Economics.
The author is Nykyta Polituchyi. Scientific supervision was provided by Przemysław Szufel.

## Overview

Built for the **SoGreen project - Working Package 7 (Preparing Contextual Environment Data)** ([SoGreen Project Website](https://sogreen-project.eu)), this tool enables systematic extraction of urban green spaces, sustainable mobility infrastructure, and socioeconomic accessibility across European cities. The main component of the tool is a data pipeline for extracting and analyzing urban geospatial data from OpenStreetMap (OSM).
The pipeline extracts OSM features based on configurable tags, processes geometries, and exports results to GeoJSON files and PostgreSQL/PostGIS databases for further spatial analysis.

## Features

- **Multi-Category OSM Extraction**: Extracts geospatial data from OpenStreetMap across defined categories. As an example:
  - *Environmental/Green Infrastructure*: parks, gardens, forests, nature reserves, wetlands
  - *Sustainable Mobility*: cycleways, footways, transit stops, bike rentals, charging stations
  - *Socioeconomic Context*: schools, hospitals, clinics, universities
- **Flexible Geometry Support**: Handles points, lines, and polygons based on feature type
- **GeoJSON Export**: Outputs standard GeoJSON files compatible with QGIS, ArcGIS, and other GIS tools
- **PostgreSQL/PostGIS Integration**: Direct database export for advanced spatial queries
- **Configurable Pipeline**: Single YAML file to configure cities, countries, and OSM tags
- **HTML Reporting**: Generates summary reports with statistics and visualizations

## Prerequisites

- Python 3.10
- [Miniconda](https://docs.conda.io/en/latest/) (recommended) or pip
- PostgreSQL 17 with PostGIS extension (optional, for database export)
- ogr2ogr (for PostgreSQL import)

---

## Quick Start Guide

### 1. Set Up the Environment

Create and activate a Conda environment with the required Python version:

```bash
conda create -n sogreen_env python=3.10
conda activate sogreen_env
```

### 2. Install Dependencies

Install all required Python packages from the requirements file:

```bash
pip install -r requirements.txt
```

### 3. Configure the Pipeline (Optional)

Edit the configuration file to change the target city or OSM tags:

```bash
# Open the configuration file
nano conf/base/parameters_osm_data_extraction.yml
```

Key configuration options:
- `city_name`: Target city (default: "Warsaw")
- `country`: Country name (default: "Poland")
- `osm_tags`: Categories and tags to extract

### 4. Run the Pipeline

Execute the Kedro pipeline to extract and process the data:

```bash
kedro run
```

> **Note**: For Warsaw (default city), the pipeline takes approximately 5 minutes to complete.

**Outputs:**
- `data/01_raw/{City}_geotags.geojson` — Raw extracted OSM data
- `data/01_raw/{City}_boundary.geojson` — City boundary polygon
- `data/08_reporting/{City}_summary_report.html` — Summary statistics and visualizations

**Summary report example for Warsaw:**
![Example - Warsaw Summary Report](docs/SoGreen%20WP7.2%20Summary%20Report%20-%20Warsaw.png)

---

## PostgreSQL/PostGIS Export

### 1. Install and Start PostgreSQL

Install PostgreSQL 17 via Homebrew and start the service:

```bash
# macOS (Homebrew)
brew install postgresql@17
brew services start postgresql@17

# Ubuntu/Debian
sudo apt-get install postgresql postgis
sudo systemctl start postgresql
```

### 2. Create the Database

Create a new PostgreSQL database for storing the geospatial data:

```bash
createdb sogreen_db
```
> **Troubleshooting**: Sometimes You need to provide the full path to postgre like `/opt/homebrew/opt/postgresql@17/bin/createdb sogreen_db`

### 3. Enable PostGIS Extension

Add PostGIS support for spatial data types and functions:

```bash
psql -d sogreen_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### 4. Import GeoJSON Data

Use `ogr2ogr` to import the extracted GeoJSON into PostgreSQL:

```bash
ogr2ogr -f "PostgreSQL" \
    PG:"dbname=sogreen_db user=YOUR_USERNAME" \
    data/01_raw/Warsaw_geotags.geojson \
    -nln warsaw_geotags \
    -overwrite
```

> **Note**: Replace `YOUR_USERNAME` with your PostgreSQL username.

---

## Database Operations

### Backup & Restore

```bash
# Backup a table to SQL file
pg_dump -U YOUR_USERNAME -d sogreen_db -t warsaw_geotags > warsaw_geotags_backup.sql

# Restore from backup
psql -U YOUR_USERNAME -d sogreen_db < warsaw_geotags_backup.sql
```

### Count Records

```bash
psql -U YOUR_USERNAME -d sogreen_db -c "SELECT COUNT(*) FROM warsaw_geotags;"
```

### Spatial Query Example

Find all parks within 2 km of a reference point (e.g., Palace of Culture and Science in Warsaw):

```sql
SELECT 
    name,
    ROUND((ST_Area(ST_Transform(wkb_geometry, 3857)) / 10000)::numeric, 2) AS area_ha,
    ROUND(ST_Distance(
        ST_Transform(wkb_geometry, 3857),
        ST_Transform(ST_SetSRID(ST_MakePoint(21.00541, 52.23134), 4326), 3857)
    )::numeric, 0) AS distance_m
FROM warsaw_geotags
WHERE osm_tag ILIKE '%park%'
  AND ST_DWithin(
      ST_Transform(wkb_geometry, 3857),
      ST_Transform(ST_SetSRID(ST_MakePoint(21.00541, 52.23134), 4326), 3857),
      2000  -- 2 km radius
  )
ORDER BY distance_m ASC;
```

### Working with Multiple Cities

After extracting data for multiple cities, create a unified view:

```sql
CREATE VIEW all_geotags AS
SELECT 'Warsaw' AS city, * FROM warsaw_geotags
UNION ALL
SELECT 'Berlin' AS city, * FROM berlin_geotags
UNION ALL
SELECT 'Paris' AS city, * FROM paris_geotags;

-- Query across all cities
SELECT city, COUNT(*) AS feature_count
FROM all_geotags
GROUP BY city;
```

---

## Configuration

All pipeline settings are managed in a single configuration file:

**`conf/base/parameters_osm_data_extraction.yml`**

To analyze a different city:
1. Update `city_name` and `country` in the configuration file
2. Optionally modify `osm_tags` to extract different features
3. Run `kedro run` to execute the pipeline

---

## Pipeline Architecture

![Kedro Pipeline](docs/kedro-pipeline.png)

---

## Project Structure

```
sogreen-wp72/
├── conf/                    # Configuration files
│   └── base/
│       └── parameters_osm_data_extraction.yml
├── data/
│   ├── 01_raw/             # Extracted GeoJSON files
│   └── 08_reporting/       # Generated reports
├── docs/                    # Documentation and images
├── notebooks/               # Jupyter notebooks for exploration
├── src/sogreen_wp72/       # Pipeline source code
   └── pipelines/
       ├── osm_data_extraction/
       └── reporting/
```

---

## Additional Resources
- [PostGIS Documentation](https://postgis.net/documentation/)
- [OSMnx Documentation](https://osmnx.readthedocs.io/)
- [OpenStreetMap Wiki - Map Features](https://wiki.openstreetmap.org/wiki/Map_features)


## Funding
<div align="center">

<p>
🔗 <a href="https://sogreen-project.eu">Project website</a>
</p>

<p>
This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No. 101188188.
</p>

<img src="docs/eu-flag.jpeg" alt="EU flag" width="200"/>

<p><em>Funded by the European Union</em></p>

<p>
The project is jointly carried out by the four participating European social science
infrastructures – ESS ERIC, SHARE-ERIC, GGP, and GUIDE.
</p>

<p><em>
Views and opinions expressed are those of the authors only and do not necessarily
reflect those of the European Union or the European Commission.
</em></p>

</div>

<hr>






