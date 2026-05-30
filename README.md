# Final Project - Mitsubishi Sales Training RAG Assistant

Mitsubishi sales-training assistant with a web frontend (HTML/CSS/JS) and Flask backend, now Google-first:
- LLM: Vertex AI Claude Haiku
- Embeddings: Vertex AI text embeddings
- Observability: Prometheus metrics + Grafana Cloud via Alloy

## Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` from `.env.example`
3. Fill Vertex settings (`VERTEX_PROJECT_ID`, `VERTEX_LOCATION`) and provider flags
4. Run app:
   ```bash
   python app.py
   ```
5. Open:
   - App: `http://localhost:8501`
   - Metrics endpoint: `http://localhost:8501/metrics`

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

## Environment Variables (Naming Convention)

Provider and model:
- `LLM_PROVIDER` (`vertex_claude` or `openai`)
- `EMBEDDING_PROVIDER` (`vertex` or `openai`)
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_MAX_OUTPUT_TOKENS`

Vertex:
- `VERTEX_PROJECT_ID`
- `VERTEX_LOCATION`
- `VERTEX_EMBEDDING_MODEL`

Optional OpenAI (only if provider uses openai):
- `OPENAI_API_KEY`

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
