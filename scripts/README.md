# scripts/

## Validate and train the BQML offset model

The SQL scripts in `sql/` use the Atlanta project settings (`qwiklabs-gcp-03-1578f96a5a7a`,
`a4i_climate`, location `US`):

```bash
bq query --location=US --use_legacy_sql=false < sql/normalize_city_label.sql
bq query --location=US --use_legacy_sql=false < sql/validate_data.sql
bq query --location=US --use_legacy_sql=false < sql/train_model.sql
bq query --location=US --use_legacy_sql=false < sql/evaluate_model.sql
```

The label-normalization script updates only NULL/blank `city` values in the existing Atlanta
snapshot; it is idempotent. `validate_data.sql` then checks the four-table schemas, the recorded
row counts, city-label coverage, and a live four-table integration row. Future loads through
`scripts/load.sh` fill missing labels automatically.

`train_model.sql` uses `CREATE OR REPLACE MODEL` and will replace the existing model when
executed. It computes the target as street temperature minus the Atlanta campaign mean, maps each
reading to its nearest tract, replaces invalid Census sentinel values, and reserves spatial grid
cells for evaluation. The evaluation script checks the model feature count and verifies that
`median_income` statistics are free of negative sentinel values.

The prediction caller must apply the same feature fallbacks as training. In particular,
`median_income` values below zero must be replaced with `65000.0`; `COALESCE` alone does not
remove Census sentinel values. Neither the label update nor the model rebuild has been run
automatically.

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
