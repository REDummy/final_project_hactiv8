# GCP Deployment Guide (Cloud Run + Alloy VM + Grafana Cloud)

This guide is prefilled for your setup:

- Project ID: `project-1b553d65-984a-4d5b-a4f`
- VM name: `final-project-hactiv8`
- Zone: `us-central1-a`
- Region: `us-central1`
- LLM target: Claude Haiku on Vertex AI (`claude-haiku-4-5`)
- Embedding target: Vertex AI embeddings (`text-embedding-005`)

Architecture:
- App on Cloud Run (no app VM)
- Grafana Alloy on existing VM (`final-project-hactiv8`)
- Alloy scrapes Cloud Run `/metrics`
- Alloy remote_write to Grafana Cloud

## 1) Local setup

```bash
gcloud auth login
gcloud config set project project-1b553d65-984a-4d5b-a4f
gcloud config set run/region us-central1
```

Enable APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  aiplatform.googleapis.com
```

## 2) Build and push container

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev

gcloud artifacts repositories create rag-repo \
  --repository-format=docker \
  --location=us-central1

docker build -t us-central1-docker.pkg.dev/project-1b553d65-984a-4d5b-a4f/rag-repo/mitsubishi-rag:latest ./final_project

docker push us-central1-docker.pkg.dev/project-1b553d65-984a-4d5b-a4f/rag-repo/mitsubishi-rag:latest
```

## 3) Deploy to Cloud Run with Vertex Claude + Vertex Embeddings

```bash
gcloud run deploy mitsubishi-rag \
  --image us-central1-docker.pkg.dev/project-1b553d65-984a-4d5b-a4f/rag-repo/mitsubishi-rag:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=prod,APP_VERSION=1.0.0,LOG_LEVEL=INFO,START_PROMETHEUS_HTTP_SERVER=false,LLM_PROVIDER=vertex_claude,EMBEDDING_PROVIDER=vertex,LLM_MODEL=claude-haiku-4-5,VERTEX_PROJECT_ID=project-1b553d65-984a-4d5b-a4f,VERTEX_LOCATION=us-central1,VERTEX_EMBEDDING_MODEL=text-embedding-005
```

Get URL:

```bash
gcloud run services describe mitsubishi-rag \
  --region us-central1 \
  --format='value(status.url)'
```

Validate:

- `https://<cloud-run-host>/api/health`
- `https://<cloud-run-host>/metrics`

## 4) Configure existing VM (`final-project-hactiv8`)

SSH:

```bash
gcloud compute ssh final-project-hactiv8 --zone=us-central1-a
```

Install Docker (if not installed):

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
```

## 5) Run Alloy on VM

On VM:

```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_PATH>/final_project/deploy/gcp/alloy
```

Edit `config.alloy` and replace `YOUR_CLOUD_RUN_HOSTNAME` with hostname only (no `https://`).

Create `.env` in this same folder:

```env
GRAFANA_CLOUD_PROM_URL=https://<your-grafana-cloud-prom-endpoint>/api/prom/push
GRAFANA_CLOUD_PROM_USER=<your-prom-username>
GRAFANA_CLOUD_API_KEY=<your-metrics-publisher-key>
```

Start Alloy:

```bash
docker compose up -d
docker compose ps
docker logs -f mitsubishi-rag-alloy
```

## 6) Validate in Grafana Cloud

In Grafana Cloud Explore:

```promql
rag_requests_total
rate(rag_requests_total[1m])
rag_total_tokens_total
histogram_quantile(0.95, sum(rate(rag_request_latency_seconds_bucket[5m])) by (le))
```

## 7) Troubleshooting

- If Cloud Run fails with Claude model:
  - Confirm Anthropic Claude model is enabled for your Vertex AI project/region.
  - Confirm model ID availability in `us-central1`.
- If embedding calls fail:
  - Confirm `text-embedding-005` is available in your project/region.
  - Confirm service account has Vertex AI User permissions.
- If no metrics in Grafana Cloud:
  - Check Alloy logs for auth/remote_write issues.
  - Check `.env` values.
- If no scrape:
  - Confirm `/metrics` is publicly reachable.
  - Ensure hostname in Alloy has no scheme/path.

