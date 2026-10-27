# scripts/

## Versioned BQML candidates and training history

The candidate runner requires Python 3.10+, `bq`, `git`, and an authenticated Cloud CLI. It uses
the standard library, so no additional Python packages or downloaded service-account keys are
needed. It reads environment variables, not dotenv files; export the settings first:

```bash
export GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-03-1578f96a5a7a
export BQ_DATASET=a4i_climate
export BQ_LOCATION=US

python3 scripts/train_candidate.py            # Plan only; no BigQuery calls or writes.
python3 scripts/train_candidate.py --execute  # Creates and tests a versioned candidate.
```

This workflow is scoped to the Atlanta dataset. It never replaces `heat_offset_model`, updates
source tables, changes agent configuration, or promotes a candidate. Each execution gets a UTC
timestamp plus random suffix and creates:

- Read-only `heat_snapshot_<run_id>` and `tract_snapshot_<run_id>` at the same point in time.
- `training_data_<run_id>` with the cleaned features, raw temperatures, target, geographic
  assignments, imputation flags, baseline anchor, spatial cells, and evaluation split.
- `heat_offset_model_<run_id>`, using exactly the eight features expected by the agent.
- Append-only rows in `model_training_events`, partitioned by date and clustered by run/stage.
  These retain the Git commit and dirty status, the exact source files and their combined SHA-256,
  configuration, SQL and parameters, submitted job IDs, stage results, metrics, and errors.
  Successful stages also persist job timestamps, processed/billed bytes, slot time, and available
  BQML training statistics; model metadata is retained after training.
  A local dirty working tree is allowed because its actual training code is stored, not just HEAD.

The runner uses `CREATE`, never `CREATE OR REPLACE`, for run artifacts. Immutability is a workflow
convention except for the read-only source snapshots; use IAM if you need enforced restrictions.
Nothing expires automatically: snapshots and feature tables consume storage. Keep validated runs
and apply an explicit retention policy before running large experiments.

### Data and validation choices

Each reading is assigned to its nearest valid tract centroid with a stable GEOID tie-breaker.
That is an approximation, not polygon containment, and has no maximum-distance cutoff; the run
records the maximum matching distance. Invalid Census values receive documented fixed fallbacks
from [clean_tracts.sql](../sql/clean_tracts.sql), reused by training and explain-prediction.

Cells of 0.02 degrees are assigned deterministically to a roughly 20% holdout using a normalized
hash modulo five. The realized fraction depends on where observations cluster. Cells never occur
on both sides, but no spatial buffer is enforced, so adjacent cells can still be correlated.
The offset is temperature minus the **training-only campaign mean**, also applied unchanged to
evaluation rows. This prevents evaluation temperatures from determining the baseline. Its anchor
can differ slightly from the full campaign mean; both are recorded. Temperature, identifiers,
imputation flags, and split metadata are explicitly excluded from the model feature list.

Checks require one feature row per source reading, nonempty training/evaluation splits, no shared
cells, clean income values, the exact feature contract, finite metrics, and a real
`ML.EXPLAIN_PREDICT` response with three finite feature attributions. A candidate must not have worse
holdout MAE than a zero-offset (training-mean) predictor. R2 >= 0.98 blocks acceptance for leakage
review, but a lower R2 does not prove there is no leakage. This single campaign cannot establish
temporal generalization or causal intervention effects.

The legacy active model is not used as a quality baseline: it may have seen the held-out readings,
and its income statistics contain a Census sentinel. Its metadata is recorded before the run and
its etag checked afterward to confirm it was not changed during training. Operational failures and
quality-gate failures are recorded as `FAILED`, with artifacts preserved for investigation. The
final `VALIDATED_CANDIDATE` status is not a production approval. Negative holdout R2 and worse
MSE than baseline are explicitly preserved as quality warnings, even if the MAE gate passes;
every candidate still requires promotion review.

Missing source city labels are reported and retained in raw snapshots, not silently rewritten;
the candidate uses the known Atlanta-only dataset without filtering this nullable field.
For explicitly authorized source repair, run `sql/normalize_city_label.sql` before the strict
snapshot regression checks in `sql/validate_data.sql`. Future loads through `scripts/load.sh`
fill missing labels automatically. These are separate from candidate execution.

### Inspect training history

```sql
SELECT run_id, event_time, stage, state, candidate_model, payload
FROM `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.model_training_events`
WHERE event_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY event_time DESC
LIMIT 50;
```

For a compact experiment comparison (metrics from different snapshots/splits are not directly
comparable):

```sql
SELECT
  run_id,
  candidate_model,
  JSON_VALUE(payload, '$.metrics.mean_absolute_error') AS holdout_mae_f,
  JSON_VALUE(payload, '$.metrics.mean_squared_error') AS holdout_mse,
  JSON_VALUE(payload, '$.metrics.r2_score') AS holdout_r2,
  JSON_QUERY(payload, '$.quality_warnings') AS quality_warnings
FROM `qwiklabs-gcp-03-1578f96a5a7a.a4i_climate.model_training_events`
WHERE stage = 'run' AND state = 'VALIDATED_CANDIDATE'
ORDER BY event_time DESC;
```

All jobs carry a `training_run` label; submitted IDs also live in registry events for failed or
interrupted jobs. Inspect job details in BigQuery or `bq show --job` for processed/billed bytes,
slot time, errors, and training configuration. Key statistics are also copied into successful
stage events so the registry does not depend on BigQuery job-history retention.
`--maximum-bytes-billed` defaults to 1 GB per query;
this is not a total budget or a cap on separately priced BQML training/storage costs.
Interruption does not automatically cancel an already-submitted job; inspect its recorded ID.

### Agent-lane handoff

`sql/train_model.sql`, `sql/evaluate_model.sql`, `sql/prepare_features.sql`, and
`sql/explain_prediction.sql` are templates, not standalone `bq` commands. The runner resolves
their identifiers and records the exact executed SQL. The explain SQL and parameters are available
in the `explain` / `SUBMITTED` event; its successful result is in `explain` / `SUCCEEDED`.
For serving, the agent lane should use the candidate model explicitly and the same cleaning
contract on live demographics. Coordinates must be validated against supported coverage before
inference; nearest-tract lookup alone does not enforce that coverage. Nothing rewires the agent.
Its old `COALESCE(median_income, ...)` still needs the shared negative-value handling, and ranking
still needs per-site explanations before the full application can be called synchronized.

Run local tests without Cloud access:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
```

## Improving a candidate without tuning on the holdout

Run a bounded ridge-regression experiment against the preserved features from a validated run:

```bash
python3 scripts/tune_candidate.py --parent-run 20261027_163945_a1f7fcb70be3
python3 scripts/tune_candidate.py --parent-run 20261027_163945_a1f7fcb70be3 --execute
```

This reuses the parent data/outer split, snapshots its prepared feature table, and trains nine
inner models: L2 strengths 0, 1000, and 10000 across three spatial folds drawn **only from outer
training rows**. Each fold's target anchor is computed solely from that fold's fitting rows.
The configuration with lowest equal-fold mean MSE is recorded before the selected model is fit
on all outer training rows and scored once against the original outer holdout. The eight-feature
agent contract remains unchanged; no heat aggregates, SVI indices, or risk scores become inputs.

The original holdout was already inspected during development, so its score is not a new,
independent certification. Adjacent spatial cells can still be correlated, and this experiment
does not add new physical environment signals. It can reduce coefficient variance, not invent
missing information. Results use `EXPERIMENT_COMPLETED`, not a validated/promoted production
status; even failed-quality experiments retain metrics, fold results, code, and job statistics.
Inspect that status as well as `VALIDATED_CANDIDATE` when comparing experiments. All intermediate
models/tables are retained and incur storage; the runner never changes the active model or agent.

The first ridge experiment (`20261027_164544_b1e872144cc1`) selected L2=1000. On the same
3,218-row outer holdout its MAE improved from 1.4984 to 1.4626 F and MSE from 3.6317 to 3.3254,
but R2 remained -0.0112 and MSE still exceeded the zero-offset baseline (3.2956). This is a
measured improvement, not evidence that the model is ready for production. The next meaningful
step is independently sourced physical-environment features (for example licensed canopy or
impervious-surface data) and new/buffered spatial validation, not repeated tuning on this holdout.

## Residual audit and a physical separation stress test

```bash
python3 scripts/audit_candidate.py --parent-run 20261027_164544_b1e872144cc1
python3 scripts/audit_candidate.py --parent-run 20261027_164544_b1e872144cc1 --execute
```

This snapshots the tuned experiment's features, retains the same holdout, and removes fitting
observations within **500 meters** of any holdout observation. It verifies there are no violating
pairs, recomputes the target anchor from retained fitting rows, and refits exactly the previously
selected regularization without another search. The buffered result is a stress test, not a
replacement score or a new independent test: fitting rows and baseline anchor have changed.

Both original and buffered candidates get persisted holdout residual tables. Aggregate reports
record row/tract counts, MAE, MSE, signed bias (prediction minus actual offset), approximate 90th
percentile absolute error, and zero-offset baseline MAE. Reports cover geographic cells, income
imputation, poverty/vehicle-rate bands, and tract-centroid matching distance; groups under 30
readings are omitted. These are aggregate error slices, not a fairness certification. Poverty and
vehicle slices use cleaned values, so missing values are assigned to their imputed bands.
The error quantile describes this holdout; it is **not** a calibrated prediction interval.
The result is recorded as `BUFFER_AUDIT_COMPLETED`; source data, active model, and agent remain
unchanged. No risk-score, SVI, or measured-temperature aggregate is introduced as a feature.

The first buffer experiment (`20261027_165503_b3dad3b996e2`) retained 18,018 of 20,168 fitting
readings, preserved all 3,218 evaluation readings, and found zero fitting/evaluation pairs within
500 m. Its MAE was 1.4496 F (baseline 1.5819 F), MSE 3.1382 (baseline 3.3064), and R2 0.0458.
This beats that stress test's baseline on both errors, but explains little of the holdout
variance. Some parent-model spatial cells had MAE near 3 F despite the aggregate improvement.
Use persisted residuals to identify those failures rather than hiding them behind average scores.

## Loading the seed data

Headless alternatives to the notebook, for when a Colab Enterprise runtime is slow or
unavailable.

`load.sh` reaches the same end state as `notebooks/c1_01_load_explore.ipynb`—the same tables, in
the same dataset, in your project. Use the notebook if you can: it explains what it's doing and
why, and the explanations matter. Use this if you can't.

## Running it

From the **root of the repo**, in Cloud Shell:

```bash
bash scripts/load.sh              # loads the default city
bash scripts/load.sh --list       # show every available city
bash scripts/load.sh --help       # usage
```

Invoke it with `bash` rather than `./scripts/load.sh`. That way it works whether or not the
file's executable bit survived however your copy of this repo was created.

## It is safe to run more than once

Every table is fully replaced, never appended to. So if you cancel it halfway through, or you
aren't sure whether it finished, just run it again—the end state is the same either way.
