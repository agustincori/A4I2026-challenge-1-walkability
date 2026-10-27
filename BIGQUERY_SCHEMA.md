# BigQuery dataset structure

## Dataset

| Setting | Value |
|---|---|
| Google Cloud project | `qwiklabs-gcp-03-1578f96a5a7a` |
| BigQuery dataset | `a4i_climate` |
| Location | `US` |
| Tables | 6 |

Fully qualified table names use this format:

```text
qwiklabs-gcp-03-1578f96a5a.a4i_climate.<table_name>
```

The schemas below were read from the dataset's BigQuery `INFORMATION_SCHEMA.COLUMNS`.
All listed columns are currently nullable.

## Tables

### `atlanta_daily_weather_clean`

Cleaned daily weather observations from Atlanta-area stations.

| Column | Type |
|---|---|
| `station_id` | `STRING` |
| `station_name` | `STRING` |
| `latitude` | `FLOAT64` |
| `longitude` | `FLOAT64` |
| `elevation_m` | `FLOAT64` |
| `date` | `DATE` |
| `year` | `INT64` |
| `month` | `INT64` |
| `tmax_f` | `FLOAT64` |
| `tmin_f` | `FLOAT64` |
| `tavg_f` | `FLOAT64` |
| `diurnal_range_f` | `FLOAT64` |
| `prcp_in` | `FLOAT64` |

Partitioned by `date` (daily) and clustered by `station_id`.

### `atlanta_tract_heat_svi_full`

Full tract-level dataset combining measured heat, population, and social-vulnerability features.

| Column | Type |
|---|---|
| `GEOID` | `STRING` |
| `mean_temp` | `FLOAT64` |
| `max_temp` | `FLOAT64` |
| `mean_rh` | `FLOAT64` |
| `mean_hi` | `FLOAT64` |
| `total_observations` | `INT64` |
| `intense_heat_count` | `INT64` |
| `intense_heat_pct` | `FLOAT64` |
| `NAME` | `STRING` |
| `POP100` | `INT64` |
| `pop_density` | `FLOAT64` |
| `RPL_THEMES` | `FLOAT64` |
| `RPL_THEME1` | `FLOAT64` |
| `RPL_THEME2` | `FLOAT64` |
| `RPL_THEME3` | `FLOAT64` |
| `RPL_THEME4` | `FLOAT64` |
| `EP_POV150` | `FLOAT64` |
| `EP_AGE65` | `FLOAT64` |
| `EP_NOVEH` | `FLOAT64` |
| `norm_hi` | `FLOAT64` |
| `norm_svi` | `FLOAT64` |
| `norm_density` | `FLOAT64` |
| `integrated_risk_score` | `FLOAT64` |

### `heat_observations`

Street-level heat measurements for a city campaign.

| Column | Type |
|---|---|
| `city` | `STRING` |
| `longitude` | `FLOAT64` |
| `latitude` | `FLOAT64` |
| `temp_f` | `FLOAT64` |
| `heat_index_f` | `FLOAT64` |
| `humidity_pct` | `FLOAT64` |
| `observed_at` | `TIMESTAMP` |

### `station_daily_temps`

Daily maximum temperatures recorded by weather stations.

| Column | Type |
|---|---|
| `station_id` | `STRING` |
| `station_name` | `STRING` |
| `latitude` | `FLOAT64` |
| `longitude` | `FLOAT64` |
| `observation_date` | `DATE` |
| `max_temp_f` | `FLOAT64` |

### `top_heat_svi_vulnerable_tracts`

Tract-level heat and social-vulnerability results for the selected vulnerable tracts.

| Column | Type |
|---|---|
| `GEOID` | `STRING` |
| `mean_temp` | `FLOAT64` |
| `max_temp` | `FLOAT64` |
| `mean_rh` | `FLOAT64` |
| `mean_hi` | `FLOAT64` |
| `total_observations` | `INT64` |
| `intense_heat_count` | `INT64` |
| `intense_heat_pct` | `FLOAT64` |
| `NAME` | `STRING` |
| `POP100` | `INT64` |
| `pop_density` | `FLOAT64` |
| `RPL_THEMES` | `FLOAT64` |
| `RPL_THEME1` | `FLOAT64` |
| `RPL_THEME2` | `FLOAT64` |
| `RPL_THEME3` | `FLOAT64` |
| `RPL_THEME4` | `FLOAT64` |
| `EP_POV150` | `FLOAT64` |
| `EP_AGE65` | `FLOAT64` |
| `EP_NOVEH` | `FLOAT64` |
| `norm_hi` | `FLOAT64` |
| `norm_svi` | `FLOAT64` |
| `norm_density` | `FLOAT64` |
| `integrated_risk_score` | `FLOAT64` |

### `tract_demographics`

Census-tract population, demographic, housing, and vehicle-access measures.

| Column | Type |
|---|---|
| `geo_id` | `STRING` |
| `tract_lat` | `FLOAT64` |
| `tract_lon` | `FLOAT64` |
| `total_pop` | `FLOAT64` |
| `median_age` | `FLOAT64` |
| `median_income` | `FLOAT64` |
| `housing_units` | `FLOAT64` |
| `median_year_structure_built` | `FLOAT64` |
| `no_cars` | `FLOAT64` |
| `households` | `FLOAT64` |
| `poverty_rate` | `FLOAT64` |
| `no_vehicle_rate` | `FLOAT64` |

## Refresh the schema listing

Run this query to inspect the current column names, data types, and nullability:

```sql
SELECT
  table_name,
  ordinal_position,
  column_name,
  data_type,
  is_nullable
FROM `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.INFORMATION_SCHEMA.COLUMNS`
ORDER BY table_name, ordinal_position;
```
