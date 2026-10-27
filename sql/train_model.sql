-- Rebuilds the BQML model from cleaned Atlanta Heat Watch and tract data.
-- This statement REPLACES the existing heat_offset_model when executed.
-- Validate first with sql/validate_data.sql; execute only when a model rebuild is approved:
-- bq query --location=US --use_legacy_sql=false < sql/train_model.sql

CREATE OR REPLACE MODEL
  `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model`
OPTIONS (
  MODEL_TYPE = 'LINEAR_REG',
  INPUT_LABEL_COLS = ['offset_f'],
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COL = 'is_eval',
  ENABLE_GLOBAL_EXPLAIN = TRUE
) AS
WITH valid_observations AS (
  SELECT
    ROW_NUMBER() OVER () AS observation_id,
    latitude,
    longitude,
    temp_f,
    AVG(temp_f) OVER () AS city_mean_temp_f
  FROM `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_observations`
  WHERE latitude BETWEEN -90 AND 90
    AND longitude BETWEEN -180 AND 180
    AND temp_f BETWEEN 40 AND 140
),
nearest_tract AS (
  SELECT
    observation_id,
    latitude,
    longitude,
    temp_f,
    city_mean_temp_f,
    geo_id,
    median_income,
    poverty_rate,
    no_vehicle_rate,
    median_age,
    housing_units,
    median_year_structure_built
  FROM (
    SELECT
      observation.observation_id,
      observation.latitude,
      observation.longitude,
      observation.temp_f,
      observation.city_mean_temp_f,
      tract.geo_id,
      tract.median_income,
      tract.poverty_rate,
      tract.no_vehicle_rate,
      tract.median_age,
      tract.housing_units,
      tract.median_year_structure_built,
      ROW_NUMBER() OVER (
        PARTITION BY observation.observation_id
        ORDER BY ST_DISTANCE(
          ST_GEOGPOINT(observation.longitude, observation.latitude),
          ST_GEOGPOINT(tract.tract_lon, tract.tract_lat)
        ), tract.geo_id
      ) AS tract_rank
    FROM valid_observations AS observation
    JOIN `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.tract_demographics` AS tract
      ON tract.tract_lat IS NOT NULL
     AND tract.tract_lon IS NOT NULL
  )
  WHERE tract_rank = 1
),
model_rows AS (
  SELECT
    CAST(latitude AS FLOAT64) AS latitude,
    CAST(longitude AS FLOAT64) AS longitude,
    CASE
      WHEN median_income >= 0 THEN CAST(median_income AS FLOAT64)
      ELSE 65000.0
    END AS median_income,
    CASE
      WHEN poverty_rate BETWEEN 0 AND 1 THEN CAST(poverty_rate AS FLOAT64)
      ELSE 0.15
    END AS poverty_rate,
    CASE
      WHEN no_vehicle_rate BETWEEN 0 AND 1 THEN CAST(no_vehicle_rate AS FLOAT64)
      ELSE 0.10
    END AS no_vehicle_rate,
    CASE
      WHEN median_age BETWEEN 0 AND 120 THEN CAST(median_age AS FLOAT64)
      ELSE 36.0
    END AS median_age,
    CASE
      WHEN housing_units >= 0 THEN CAST(housing_units AS FLOAT64)
      ELSE 1500.0
    END AS housing_units,
    CASE
      WHEN median_year_structure_built > 1800
        THEN CAST(median_year_structure_built AS FLOAT64)
      ELSE 1975.0
    END AS median_year_structure_built,
    CAST(temp_f - city_mean_temp_f AS FLOAT64) AS offset_f,
    MOD(
      MOD(
        FARM_FINGERPRINT(
          FORMAT(
            '%d:%d',
            CAST(FLOOR(latitude * 50) AS INT64),
            CAST(FLOOR(longitude * 50) AS INT64)
          )
        ),
        5
      ) + 5,
      5
    ) = 0 AS is_eval
  FROM nearest_tract
)
SELECT
  latitude,
  longitude,
  median_income,
  poverty_rate,
  no_vehicle_rate,
  median_age,
  housing_units,
  median_year_structure_built,
  offset_f,
  is_eval
FROM model_rows;
