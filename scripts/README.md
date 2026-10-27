# scripts/

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

## Building and deploying the agent

[`../cloudbuild.yaml`](../cloudbuild.yaml) defines the CI/CD pipeline. It builds the existing
Cloud Run container, runs the agent's unit tests inside that exact image, pushes the image to
Artifact Registry, and deploys a digest-pinned candidate revision. It promotes that revision
only after Cloud Run reports it ready. When public access is explicitly enabled, it also checks
the candidate's `/health` endpoint before promotion.

### One-time project setup

Choose a Cloud Run runtime service account for the app and a separate Cloud Build service
account for CI/CD. Enable the required APIs and create the Artifact Registry repository:

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="us-central1"
BUILD_SA="walkability-build@${PROJECT_ID}.iam.gserviceaccount.com"
RUN_SA="walkability-runtime@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud services enable \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  --project="$PROJECT_ID"

gcloud iam service-accounts create walkability-build --project="$PROJECT_ID"
gcloud iam service-accounts create walkability-runtime --project="$PROJECT_ID"
gcloud artifacts repositories create walkability \
  --project="$PROJECT_ID" \
  --location="$REGION" \
  --repository-format=docker \
  --description="Walkability agent container images"
```

Grant the build identity only what the pipeline needs. Artifact Registry write access is scoped
to the image repository; Cloud Run administration and service-account impersonation are needed
to deploy the runtime:

```bash
gcloud artifacts repositories add-iam-policy-binding walkability \
  --project="$PROJECT_ID" --location="$REGION" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/run.admin"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/serviceusage.serviceUsageConsumer"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/logging.logWriter"
gcloud iam service-accounts add-iam-policy-binding "$RUN_SA" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"
```

Grant the runtime identity Vertex AI access, BigQuery job creation, and read access only to the
agent's dataset. The dataset must already exist and the configured BQML models must be trained:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUN_SA}" \
  --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUN_SA}" \
  --role="roles/bigquery.jobUser"
bq add-iam-policy-binding "${PROJECT_ID}:a4i_climate" \
  --member="serviceAccount:${RUN_SA}" \
  --role="roles/bigquery.dataViewer"
```

The identity submitting a build also needs permission to create builds and act as `BUILD_SA`.
For repository triggers, configure the trigger to use the same dedicated build service account
and provide the substitutions used below.

### Run the pipeline

From the repository root, submit a build. The default service is private; Cloud Run callers need
`roles/run.invoker`. Use `--public` only for an intentionally unauthenticated demo endpoint.

```bash
bash scripts/deploy.sh \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --build-service-account "$BUILD_SA" \
  --runtime-service-account "$RUN_SA"

# Optional: publish the service to unauthenticated callers.
bash scripts/deploy.sh \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --build-service-account "$BUILD_SA" \
  --runtime-service-account "$RUN_SA" \
  --public
```

The pipeline pins deployment to the pushed Artifact Registry digest, disables runtime BQML
model bootstrapping, and keeps traffic on the current revision until the candidate is ready.
Resource sizing and model/dataset values are configurable through the substitutions in
[`../cloudbuild.yaml`](../cloudbuild.yaml). Avoid passing credentials as substitutions or
environment variables; use Secret Manager references for any future secret configuration.
