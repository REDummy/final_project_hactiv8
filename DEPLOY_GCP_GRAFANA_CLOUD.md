# GCP Deployment Guide (Cloud Run + Debian VM Alloy + Grafana Cloud)

This version is adjusted for a Debian VM.

## 0) Setup Values

- Project ID: `project-1b553d65-984a-4d5b-a4f`
- Region: `us-central1`
- Artifact Registry repo: `rag-repo`
- Cloud Run service: `mitsubishi-rag`
- VM: `final-project-hactiv8`
- VM zone: `us-central1-a`

Architecture:
- App on Cloud Run
- Alloy on Debian VM
- Alloy scrapes Cloud Run `/metrics`
- Alloy forwards metrics to Grafana Cloud

## 1) Local gcloud setup

```bash
gcloud auth login
gcloud config set project project-1b553d65-984a-4d5b-a4f
gcloud config set run/region us-central1
```

Enable required APIs:

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com compute.googleapis.com
```

## 2) Build and push image

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev

gcloud artifacts repositories create rag-repo --repository-format=docker --location=us-central1
```

If repo already exists, continue.

```bash
docker build -t us-central1-docker.pkg.dev/project-1b553d65-984a-4d5b-a4f/rag-repo/mitsubishi-rag:latest .
docker push us-central1-docker.pkg.dev/project-1b553d65-984a-4d5b-a4f/rag-repo/mitsubishi-rag:latest
```

## 3) Deploy to Cloud Run

```bash
gcloud run deploy mitsubishi-rag \
  --image us-central1-docker.pkg.dev/project-1b553d65-984a-4d5b-a4f/rag-repo/mitsubishi-rag:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=prod,APP_VERSION=1.0.0,LOG_LEVEL=INFO,START_PROMETHEUS_HTTP_SERVER=false,LLM_MODEL=gemini-3.1-flash-lite,LLM_FALLBACK_MODEL=gemini-2.5-flash-lite,LLM_BACKUP_MODEL=gpt-4.1-mini,GOOGLE_EMBEDDING_MODEL=models/text-embedding-004,OPENAI_EMBEDDING_MODEL=text-embedding-3-small,OPENAI_INPUT_PRICE_PER_1M=0.15,OPENAI_OUTPUT_PRICE_PER_1M=0.60,GOOGLE_API_KEY=<your-google-api-key>,OPENAI_API_KEY=<your-openai-api-key>
```

Get URL:

```bash
gcloud run services describe mitsubishi-rag --region us-central1 --format="value(status.url)"
```

Update env vars on an existing Cloud Run service without rebuilding image:

```bash
gcloud run services update mitsubishi-rag \
  --region us-central1 \
  --update-env-vars LLM_MODEL=gemini-3.1-flash-lite,LLM_FALLBACK_MODEL=gemini-2.5-flash-lite,LLM_BACKUP_MODEL=gpt-4.1-mini,GOOGLE_EMBEDDING_MODEL=models/text-embedding-004,OPENAI_EMBEDDING_MODEL=text-embedding-3-small,GOOGLE_API_KEY=<your-google-api-key>,OPENAI_API_KEY=<your-openai-api-key>
```

Validate:

```bash
curl -i <CLOUD_RUN_URL>/api/health
curl -i <CLOUD_RUN_URL>/metrics
```

## 4) Configure Debian VM

SSH:

```bash
gcloud compute ssh final-project-hactiv8 --zone=us-central1-a
```

Install Docker + Compose (Debian-friendly):

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version
docker-compose --version
```

## 5) Run Alloy on VM

```bash
git clone https://github.com/REDummy/final_project_hactiv8
cd final_project_hactiv8/deploy/gcp/alloy
```

`config.alloy` now reads all sensitive values from environment variables.

Create `.env` in this folder:

```.env
CLOUD_RUN_HOSTNAME=<your-cloud-run-hostname-only>
GRAFANA_CLOUD_PROM_URL=https://<your-grafana-cloud-prom-endpoint>/api/prom/push
GRAFANA_CLOUD_PROM_USER=<your-prom-username>
GRAFANA_CLOUD_API_KEY=<your-metrics-publisher-key>
```

Notes:
- `CLOUD_RUN_HOSTNAME` should be hostname only (no `https://`, no path).
- Do not commit this `.env` file.
- If you prefer GCP Secret Manager, inject these values as environment variables when running Alloy.

Start Alloy (Debian package uses `docker-compose`):

```bash
docker-compose up -d
docker-compose ps
docker logs -f mitsubishi-rag-alloy
```

## 6) Validate in Grafana Cloud

In Grafana Explore:

```promql
rag_requests_total
rate(rag_requests_total[1m])
rag_prompt_tokens_total
rag_completion_tokens_total
rag_total_tokens_total
rag_estimated_openai_cost_usd_total
histogram_quantile(0.95, sum(rate(rag_request_latency_seconds_bucket[5m])) by (le))
```

## 7) Troubleshooting

- `docker-compose-plugin` not found on Debian:
  - Use `docker-compose` package and `docker-compose ...` commands.
- Provider auth/model errors on Cloud Run:
  - Check `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `LLM_MODEL`, `LLM_FALLBACK_MODEL`, `LLM_BACKUP_MODEL`, `GOOGLE_EMBEDDING_MODEL`, and `OPENAI_EMBEDDING_MODEL`.
- No metrics in Grafana:
  - Check Alloy logs and `.env` credentials.
  - Confirm Cloud Run `/metrics` is reachable.
  - Confirm Alloy target hostname has no scheme/path.
## 8) Run Evaluation and Stress Test on Cloud Run URL

Assume URL:
- `https://mitsubishi-rag-697353833582.us-central1.run.app/`

Run expanded evaluation set:
```bash
python evaluation/run_eval.py --base-url https://mitsubishi-rag-697353833582.us-central1.run.app/
```

Run stress evaluation set:
```bash
python evaluation/run_eval.py --base-url https://mitsubishi-rag-697353833582.us-central1.run.app/ --cases evaluation/eval_cases_stress.jsonl --top-k 8 --min-pass-rate 0.67
```

Run headless stress load test:
```bash
locust -f loadtest/locustfile.py --host https://mitsubishi-rag-697353833582.us-central1.run.app RagApiStressUser --headless -u 20 -r 2 -t 3m --only-summary
```

Run headless normal load test (about 4 users for 5 minutes):
```bash
locust -f loadtest/locustfile.py --host https://mitsubishi-rag-697353833582.us-central1.run.app RagApiUser --headless -u 4 -r 1 -t 5m --only-summary
```

PowerShell fallback if proxy variables interfere:
```powershell
$env:HTTPS_PROXY=''; $env:HTTP_PROXY=''; $env:ALL_PROXY=''; python evaluation/run_eval.py --base-url https://mitsubishi-rag-697353833582.us-central1.run.app/
$env:HTTPS_PROXY=''; $env:HTTP_PROXY=''; $env:ALL_PROXY=''; locust -f loadtest/locustfile.py --host https://mitsubishi-rag-697353833582.us-central1.run.app RagApiStressUser --headless -u 20 -r 2 -t 3m --only-summary
$env:HTTPS_PROXY=''; $env:HTTP_PROXY=''; $env:ALL_PROXY=''; locust -f loadtest/locustfile.py --host https://mitsubishi-rag-697353833582.us-central1.run.app RagApiUser --headless -u 4 -r 1 -t 5m --only-summary
```
