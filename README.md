# Final Project - Mitsubishi Sales Training RAG Assistant

Mitsubishi sales-training assistant with a web frontend (HTML/CSS/JS) and Flask backend.
- LLM routing: configurable mode (`hybrid` or `openai`); default is Google Gemini primary (`gemini-3.1-flash-lite`) -> Google Gemini fallback (`gemini-2.5-flash-lite`) -> OpenAI backup model
- Embeddings: Google embedding primary with OpenAI embedding fallback
- Observability: Prometheus metrics + Grafana Cloud via Alloy

## Live Links
- Deployed App: `https://mitsubishi-rag-697353833582.us-central1.run.app/`
- Monitoring Dashboard: `https://redummy.grafana.net/public-dashboards/adf96896cd51481e85157cc3eafd2c0e`
- Pitch Deck (PowerPoint): `https://365bsi-my.sharepoint.com/:p:/g/personal/bsi80269_bsi_co_id/IQCxWEJCtxDmS4JgVjA5TYVeATKRiCAH79EONGP8hGV35Wg?e=6h2w2M`

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` from `.env.example`
3. Choose provider mode in `.env` (`LLM_PROVIDER_MODE` / `EMBEDDING_PROVIDER_MODE`) and set required API key(s).
4. Run app:
   ```bash
   python app.py
   ```
5. Open:
   - App: `http://localhost:8501`
   - Metrics endpoint (app route): `http://localhost:8501/metrics`
   - Metrics endpoint (Prometheus exporter, when `START_PROMETHEUS_HTTP_SERVER=true`): `http://localhost:8000/metrics`

## Quality Gates: Test, Evaluation, Load Test
Install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

Run unit/integration tests:
```bash
pytest
```

Run penetration tests:
```bash
pytest -m pentest -q
```

Run host-based penetration checks:
```bash
python evaluation/run_pentest_host.py --base-url http://localhost:8501 --verbose
```

See detailed guide: `PENETRATION_TESTING.md`

Run API evaluation cases (default):
```bash
python evaluation/run_eval.py --base-url http://localhost:8501
```

Run stress evaluation cases:
```bash
python evaluation/run_eval.py --base-url http://localhost:8501 --cases evaluation/eval_cases_stress.jsonl --top-k 8 --min-pass-rate 0.67
```

Run evaluation directly to deployed Cloud Run URL:
```bash
python evaluation/run_eval.py --base-url https://mitsubishi-rag-697353833582.us-central1.run.app/
```

Run stress evaluation directly to deployed Cloud Run URL:
```bash
python evaluation/run_eval.py --base-url https://mitsubishi-rag-697353833582.us-central1.run.app/ --cases evaluation/eval_cases_stress.jsonl --top-k 8 --min-pass-rate 0.67
```

Evaluation report output:
- `evaluation/reports/latest.json`

Run load test with Locust (normal profile):
```bash
locust -f loadtest/locustfile.py --host http://localhost:8501 RagApiUser
```

Run stress load test with Locust (stress profile):
```bash
locust -f loadtest/locustfile.py --host http://localhost:8501 RagApiStressUser
```

Run stress load test headless to deployed Cloud Run URL:
```bash
locust -f loadtest/locustfile.py --host https://mitsubishi-rag-697353833582.us-central1.run.app RagApiStressUser --headless -u 20 -r 2 -t 3m --only-summary
```

Run normal load test headless to deployed Cloud Run URL (about 4 users for 5 minutes):
```bash
locust -f loadtest/locustfile.py --host https://mitsubishi-rag-697353833582.us-central1.run.app RagApiUser --headless -u 4 -r 1 -t 5m --only-summary
```

Then open `http://localhost:8089` for the load-test UI (when not headless).


## Run OpenAI-only
Set these in `.env`:
```env
LLM_PROVIDER_MODE=openai
EMBEDDING_PROVIDER_MODE=openai
OPENAI_LLM_MODEL=gpt-4.1-mini
OPENAI_LLM_FALLBACK_MODEL=gpt-4o-mini
```
Only `OPENAI_API_KEY` is required in this mode.
## Docker Run
```bash
docker compose up --build
```

## Project Structure
- `app.py` - Flask app and API endpoints
- `web/templates/index.html` - UI markup
- `web/static/styles.css` - CSS
- `web/static/app.js` - frontend logic
- `src/services/resources.py` - resource loading
- `src/llm_service.py` - LLM prompt + safety flow + provider fallback chain
- `src/rag_pipeline.py` - chunking + embeddings + FAISS
- `src/monitoring.py` - Prometheus metrics
- `tests/` - pytest test suite for API endpoints/helpers/monitoring
- `evaluation/` - evaluation datasets + runner + reports
- `loadtest/` - Locust load test profiles (normal + stress)

## Monitoring Metrics
- `rag_requests_total`
- `rag_request_latency_seconds`
- `rag_prompt_tokens_total`
- `rag_completion_tokens_total`
- `rag_total_tokens_total`
- `rag_retrieved_docs_per_query`
- `rag_last_response_time_ms`

## Deployment
Use:
- `DEPLOY_GCP_GRAFANA_CLOUD.md`

## Environment Variables

Providers:
- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`

Provider modes:
- `LLM_PROVIDER_MODE` (`hybrid` or `openai`)
- `EMBEDDING_PROVIDER_MODE` (`hybrid` or `openai`)

LLM routing:
- `LLM_MODEL` (default `gemini-3.1-flash-lite`, used in `hybrid` mode)
- `LLM_FALLBACK_MODEL` (default `gemini-2.5-flash-lite`, used in `hybrid` mode)
- `LLM_BACKUP_MODEL` (OpenAI backup model, used in `hybrid` mode)
- `OPENAI_LLM_MODEL` (used in `openai` mode)
- `OPENAI_LLM_FALLBACK_MODEL` (used in `openai` mode)
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_MAX_OUTPUT_TOKENS`

Embeddings:
- `GOOGLE_EMBEDDING_MODEL` (used in `hybrid` mode)
- `OPENAI_EMBEDDING_MODEL` (used in both modes)
- `OPENAI_INPUT_PRICE_PER_1M` (for monitoring cost estimation)
- `OPENAI_OUTPUT_PRICE_PER_1M` (for monitoring cost estimation)

App/runtime:
- `APP_ENV`
- `APP_VERSION`
- `LOG_LEVEL`
- `TOP_K`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `MOCK_TEST_DEFAULT_MINUTES`
- `PROMETHEUS_PORT`
- `START_PROMETHEUS_HTTP_SERVER`

Safety:
- `ENABLE_INPUT_GUARD`
- `MAX_INPUT_CHARS`
- `BLOCKED_WORDS`
- `INJECTION_PATTERNS`

## Developer Monitoring
- In Developer Mode, the Monitoring section now shows recent queries, input/output tokens, and estimated OpenAI cost per request.
- Cost estimation uses OPENAI_INPUT_PRICE_PER_1M and OPENAI_OUTPUT_PRICE_PER_1M.



