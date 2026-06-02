# Problem Framing, Business Relevance, and Presentation FAQ

## 1) Problem Framing

### Current Situation
Mitsubishi dealership sales teams handle many repeated interactions every day: qualification, objection handling, financing explanation, SOP communication, escalation, and handover guidance. Knowledge is often spread across people, chat history, and static documents. This creates inconsistent answer quality across consultants and branches.

### Core Problem
Teams need fast, consistent, and practical guidance during live sales conversations. Without a structured support system, branches face:
- inconsistent customer communication,
- slower onboarding for new consultants,
- avoidable process mistakes (SPK, handover, escalation),
- weak coaching feedback loops.

### Project Problem Statement
How might we provide a reliable assistant that can retrieve SOP and sales-training knowledge quickly, generate practical responses, and evaluate trainee answers with measurable scoring?

### Scope
This project focuses on:
- Mitsubishi sales training and SOP content,
- retrieval-grounded LLM answers,
- trainee QnA evaluation and scoring,
- operational monitoring (latency, tokens, retrieval behavior).

This project does not aim to replace CRM, DMS, or official compliance systems.

## 2) Business Relevance

### Why It Matters to the Business
1. Better conversion consistency:
   Consultants get grounded responses and scripts for real scenarios (discount pressure, follow-up, objections).
2. Faster onboarding:
   New hires can learn structured SOP and answer patterns sooner.
3. Lower operational errors:
   SOP-driven guidance reduces mistakes in SPK handling, delivery communication, and escalation flow.
4. Stronger coaching discipline:
   Managers can use QnA scoring metrics (accuracy, completeness, SOP alignment, clarity, actionability) to coach with evidence.
5. Improved customer trust:
   More consistent communication quality across customer touchpoints.

### Stakeholders
- Sales consultants: real-time support in customer conversations.
- Sales managers: coaching and capability development.
- Branch leadership: more stable conversion and fewer avoidable errors.
- Customers: clearer, more consistent service experience.

### Expected KPI Impact (example mapping)
- Test-drive to SPK conversion: expected improvement from more structured objection handling.
- Lead response quality and speed: expected improvement via SOP-guided responses.
- Post-SPK cancellation rate: expected reduction via better expectation-setting SOP.
- Time-to-productivity for new hires: expected reduction due to guided training and scoring.

## 3) FAQ for Presentation

### Product and Use Case

**Q: What does this system do in one sentence?**
A: It is a Mitsubishi sales-training RAG assistant that answers SOP questions and scores trainee responses using document-grounded evaluation.

**Q: Who is the primary user?**
A: Sales consultants and sales managers in dealership operations.

**Q: What makes this different from normal chatbot tools?**
A: Answers are grounded in internal training/SOP documents, and it includes a trainee scoring workflow with explicit metrics.

### Data and RAG

**Q: What data sources are used?**
A: Three local JSONL datasets: glossary, FAQ, and guides focused on Mitsubishi sales training and SOP.

**Q: How does retrieval work?**
A: Documents are normalized, chunked, embedded, stored in FAISS, and top-k relevant chunks are retrieved per query.

**Q: How do you reduce hallucination risk?**
A: The system prompt enforces context-grounded answers and asks the model to state when context is insufficient.

### QnA Scoring

**Q: How is trainee scoring done?**
A: The model evaluates trainee answers against retrieved context and returns structured JSON scores plus strengths, gaps, and improvement tips.

**Q: What metrics are used?**
A: Accuracy, completeness, SOP alignment, clarity, and actionability, plus weighted overall score.

**Q: Can evaluators see what evidence was used?**
A: Yes, retrieved evaluation context is displayed so reviewers can audit scoring rationale.

### Business Value and Operations

**Q: How does this support managers?**
A: Managers can use scoring outputs to coach specific behavior gaps instead of generic feedback.

**Q: What business outcomes do you expect first?**
A: Faster consultant readiness, more consistent customer handling, and lower SOP-related execution errors.

**Q: Is this replacing human managers or trainers?**
A: No, it augments trainers/managers by making knowledge access and evaluation faster and more consistent.

### Technical and Monitoring

**Q: What model and infra are used?**
A: Configurable LLM routing (hybrid Google Gemini + OpenAI backup, or OpenAI-only), FAISS retrieval, Flask + web static UI, and Prometheus/Grafana observability.

**Q: What metrics are monitored?**
A: Request count, latency, prompt/completion/total tokens, retrieved docs per query, and last response time.

**Q: Why is monitoring important in this project?**
A: It allows us to track quality-performance trade-offs and maintain predictable operational behavior.

### Risk, Limitation, and Next Steps

**Q: What are current limitations?**
A: Quality depends on dataset coverage and retrieval relevance; scores are model-based and should be reviewed for critical assessments.

**Q: What is the mitigation plan?**
A: Continue expanding SOP datasets, run evaluator calibration reviews, and monitor failed/low-confidence cases for dataset improvements.

**Q: What are logical next enhancements?**
A: Role-based scoring rubrics, historical trainee progress tracking, scenario banks by difficulty, and branch-level performance analytics.

## 4) What Could Be Improved

1. Data coverage depth:
   Expand SOP and scenario coverage in four priority areas so retrieval handles real branch conversations more consistently:
   - After-sales complaints: warranty claim flow, service appointment escalation, compensation boundaries, and customer follow-up scripts.
   - Financing edge cases: rejected applications, DP/installment restructuring options, late-payment handling, and cross-check with finance partner policy.
   - Delivery delays: root-cause communication templates, revised ETA protocol, escalation matrix, and trust-recovery scripts.
   - Competitor comparison: structured comparison guardrails (features, TCO, after-sales value) to avoid ungrounded claims.
2. Evaluation reliability:
   Add a calibration set with manager-reviewed gold answers to measure score consistency and reduce evaluator drift.
3. Stronger retrieval quality controls:
   Track low-relevance retrieval cases, tune chunking/top-k per use case, and add periodic retrieval-quality reviews.
4. Production hardening:
   Add authentication, role-based access, rate limiting, and managed secret storage for safer multi-branch usage.
5. Learning analytics and adoption loop:
   Add trainee progress history, branch-level benchmarking, and manager feedback capture to convert usage into measurable capability growth.

---

## 5) Suggested 60-Second Pitch

This project solves a real dealership pain point: inconsistent sales and SOP guidance across teams. We built a Mitsubishi-focused RAG assistant that retrieves grounded knowledge from curated training documents and gives practical guidance in Bahasa Indonesia. Beyond answering, it includes a trainee QnA scoring mode so managers can evaluate answers on accuracy, completeness, SOP alignment, clarity, and actionability. The result is faster onboarding, more consistent execution, and measurable coaching support, with Prometheus/Grafana monitoring for reliability and performance.
