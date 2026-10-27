-- Read-only evaluation and feature-quality checks for heat_offset_model.
-- Run after sql/train_model.sql:
-- bq query --location=US --use_legacy_sql=false < sql/evaluate_model.sql

ASSERT (
  SELECT COUNT(*) = 8
  FROM ML.FEATURE_INFO(
    MODEL `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model`
  )
) AS 'Expected exactly 8 model input features.';

ASSERT (
  SELECT COUNTIF(
    input = 'median_income'
    AND SAFE_CAST(min AS FLOAT64) >= 0
    AND SAFE_CAST(mean AS FLOAT64) >= 0
    AND SAFE_CAST(null_count AS INT64) = 0
  ) = 1
  FROM ML.FEATURE_INFO(
    MODEL `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model`
  )
) AS 'median_income still has a sentinel, invalid minimum/mean, or NULLs.';

SELECT *
FROM ML.EVALUATE(
  MODEL `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model`
);

SELECT
  input,
  min,
  max,
  mean,
  null_count
FROM ML.FEATURE_INFO(
  MODEL `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model`
)
ORDER BY input;

SELECT *
FROM ML.TRAINING_INFO(
  MODEL `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.heat_offset_model`
)
ORDER BY iteration;
