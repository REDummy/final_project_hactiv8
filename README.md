# Final Project - Mitsubishi Sales Training RAG Assistant

Mitsubishi sales-training assistant with a web frontend (HTML/CSS/JS) and Flask backend.
- LLM: OpenAI chat models (with optional OpenAI fallback model)
- Embeddings: OpenAI embeddings
- Observability: Prometheus metrics + Grafana Cloud via Alloy

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` from `.env.example`
3. Set `OPENAI_API_KEY`
4. Run app:
   ```bash
   python app.py
   ```
5. Open:
   - App: `http://localhost:8501`
   - Metrics endpoint (app route): `http://localhost:8501/metrics`
   - Metrics endpoint (Prometheus exporter, when `START_PROMETHEUS_HTTP_SERVER=true`): `http://localhost:8000/metrics`

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
- `src/llm_service.py` - LLM prompt + safety flow
- `src/rag_pipeline.py` - chunking + embeddings + FAISS
- `src/monitoring.py` - Prometheus metrics

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

OpenAI:
- `OPENAI_API_KEY`
- `LLM_MODEL`
- `LLM_FALLBACK_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- OPENAI_INPUT_PRICE_PER_1M (for monitoring cost estimation)
- OPENAI_OUTPUT_PRICE_PER_1M (for monitoring cost estimation)
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_MAX_OUTPUT_TOKENS`

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
