# Cheat Sheet: Presentation Q&A

## 1) Elevator Pitch

**Q: What did you build?**
A: A Mitsubishi sales-training RAG assistant that gives SOP-grounded answers, generates trainee questions, and scores trainee responses with actionable feedback.

**Q: Why is this useful?**
A: It improves consistency in sales execution, speeds onboarding, and gives managers structured coaching signals.

## 2) Product Demo Q&A

**Q: What can this app do in demo?**
A:
1. Knowledge Assistant: answer SOP/sales questions using retrieved context.
2. Trainee QnA Scoring: evaluate one trainee answer with metric-based scoring.
3. Mock Test (5 Questions): generate 5 random topic-based questions and submit for aggregate scoring.

**Q: What metrics are used for scoring?**
A: Accuracy, completeness, SOP alignment, clarity, and actionability, plus weighted overall score.

**Q: How do you avoid random answers?**
A: Prompts enforce context-only answering. If context is insufficient, the model should state that.

## 3) Data & RAG Q&A

**Q: What dataset is used?**
A: Local JSONL files in `data/`: glossary, FAQ, and guides, all focused on Mitsubishi sales training and SOP.

**Q: How does retrieval work?**
A: JSONL -> normalized text -> chunking -> embeddings -> FAISS vector store -> top-k retrieval -> LLM answer.

**Q: Why ignore slug fields?**
A: Slugs are metadata identifiers, not business knowledge, so excluding them keeps retrieval cleaner.

## 4) Technical Architecture Q&A

**Q: What is the architecture?**
A: Flask API + server-rendered web UI (`web/templates` + `web/static`) + modular service layer (`config`, `data_loader`, `rag_pipeline`, `llm_service`) + Prometheus metrics + Grafana dashboard.

**Q: How is configuration managed?**
A: Typed settings via `pydantic-settings` in one source of truth (`src/config.py`), loaded from environment.

**Q: What reliability controls are applied?**
A: Timeout, retries, output token cap for LLM calls; container health checks; restart policy in compose.

## 5) Monitoring Q&A

**Q: What are you monitoring?**
A:
- total requests
- latency histogram
- prompt/completion/total tokens
- retrieved docs distribution
- last response time

**Q: Where can we see metrics?**
A:
- Prometheus UI: `http://localhost:9090`
- Grafana dashboard: `http://localhost:3001`

**Q: How do you know monitoring is wired correctly?**
A: Prometheus scrape target points to `app:8000`; Grafana datasource points to Prometheus; dashboard queries use exported metric names.

## 6) Deployment Q&A

**Q: How do you run this quickly?**
A:
```bash
docker compose -f final_project/docker-compose.yml up -d --build
```

**Q: If you stop Docker, must you rebuild?**
A: Not always. Rebuild only when code/dependencies changed.

**Q: How to make it publicly accessible for demo?**
A: Fastest is ngrok tunnel to app port 8501. For stable public access, deploy to VM/cloud with reverse proxy + HTTPS.

## 7) Security Q&A

**Q: How are secrets handled?**
A: `.env` is excluded via `.gitignore`; `.env.example` is committed as template only.

**Q: What if API key leaked?**
A: Revoke old key in OpenAI dashboard, issue a new key, update `.env`, restart services.

**Q: Why not inject all env vars into all services?**
A: Principle of least privilege. Grafana only needs Grafana credentials, not OpenAI keys.

## 8) Business Relevance Q&A

**Q: What KPI impact do you expect?**
A:
- improved test-drive to SPK conversion consistency
- lower cancellation from better expectation-setting
- faster onboarding and coaching cycles
- reduced SOP execution errors

**Q: Who benefits most?**
A: Sales consultants (day-to-day support) and sales managers (coaching with measurable scoring).

## 9) Limitation & Next Step Q&A

**Q: Current limitations?**
A: Quality depends on dataset coverage and retrieval relevance; model scoring still needs managerial calibration for high-stakes assessment.

**Q: Next improvements?**
A:
1. role-based rubrics (consultant vs manager)
2. trainee progress history and analytics
3. branch-level score benchmarking
4. stronger automated eval validation set

## 10) Post-Thank-You Technical Deep Dive Q&A

**Q: What is the request lifecycle in technical terms?**
A: UI request -> Flask API -> query embedding -> FAISS top-k retrieval -> grounded prompt assembly -> LLM generation -> structured response + metrics emission.

**Q: How do you validate retrieval quality, not just model fluency?**
A: We review retrieval relevance samples, track low-relevance cases, and tune chunking/top-k by scenario so quality is measured from retrieval first.

**Q: What keeps LLM cost and latency under control?**
A: Output token caps, timeout/retry controls, provider routing, and monitoring of prompt/completion tokens per request.

**Q: How do you make scoring output reliable for manager usage?**
A: The evaluator returns structured JSON with metric breakdown, evidence context, strengths, gaps, and improvement tips so managers can audit decisions.

**Q: How does this scale beyond one branch?**
A: Keep API layer stateless, externalize or shard vector storage as data grows, add RBAC, and place async workers for heavy scoring workloads.

## 11) Decision Rationale Q&A

**Q: Why use RAG instead of a plain LLM chatbot?**
A: Because SOP accuracy matters more than creativity; RAG keeps responses anchored to approved internal documents.

**Q: Why choose Flask + server-rendered UI for this project?**
A: It minimizes engineering overhead, speeds iteration, and is easier to deploy/maintain for a pilot-scale product.

**Q: Why use hybrid LLM routing instead of one provider only?**
A: Hybrid routing gives fallback resilience and flexibility to optimize latency, quality, and cost over time.

**Q: Why deploy with Docker Compose first?**
A: Compose gives reproducible environments and faster team onboarding before moving to more complex cloud orchestration.

**Q: Why invest in Prometheus/Grafana this early?**
A: Without observability, cost and quality drift is hard to detect; metrics are needed to run this as an operational system.

**Q: Why keep managers in the process instead of full AI automation?**
A: Coaching quality and edge-case judgment still require human review; AI accelerates preparation, managers own final accountability.

## 12) Rapid Fire (Short Answers)

**Q: Why RAG instead of plain LLM?**
A: Grounded answers, lower hallucination risk, traceable context.

**Q: Why Flask + vanilla web UI?**
A: It keeps deployment simple, gives full control over API + UI behavior, and stays lightweight for this project scope.

**Q: Why FAISS?**
A: Lightweight, local, and sufficient for current dataset scale.

**Q: Is this production-ready?**
A: It is production-oriented with monitoring and deployment hygiene, and can be hardened further with auth, rate limit, and managed secret store.

**Q: What is your strongest differentiator?**
A: It combines grounded answer generation and structured trainee scoring in one workflow.
