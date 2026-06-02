const quickPrompts = [
  "Build a follow-up script for a customer who asked for a discount and went silent for 3 days.",
  "What SOP checks should be completed before SPK submission to avoid delivery disputes?",
  "Create a weekly coaching plan for a consultant with low conversion.",
  "How should sales handle a delivery delay complaint from first response to escalation?"
];

const state = {
  viewMode: "public",
  deviceMode: "web",
  themeMode: "auto",
  defaultTopK: 4,
  mock: {
    questions: [],
    answers: [],
    index: 0,
    deadline: 0,
    timerId: null,
    submitted: false,
  },
  monitoringPoller: null,
  monitoringLoading: false
};

const el = (id) => document.getElementById(id);

function currentTopK() {
  if (state.viewMode === "public") return state.defaultTopK;
  const value = Number(el("topK").value || state.defaultTopK);
  return Math.max(2, Math.min(8, value));
}

function setHtml(id, html) {
  el(id).innerHTML = html;
}

function loadingMarkup(text = "Loading...") {
  return `<div class="loading-inline"><span class="spinner"></span><span>${text}</span></div>`;
}

function metricChips(items) {
  const chips = items
    .map((item) => `<span class="metric-chip"><strong>${escapeHtml(String(item.label))}</strong> ${escapeHtml(String(item.value))}</span>`)
    .join("");
  return `<div class="metric-row">${chips}</div>`;
}

function setButtonLoading(buttonId, isLoading, loadingText = "Loading...") {
  const button = el(buttonId);
  if (!button) return;

  if (isLoading) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }
    button.disabled = true;
    button.innerHTML = `<span class="btn-spinner"></span>${loadingText}`;
  } else {
    button.disabled = false;
    if (button.dataset.originalText) {
      button.textContent = button.dataset.originalText;
    }
  }
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function setActiveTab(tabName) {
  document.querySelectorAll(".tab-panel").forEach((x) => x.classList.remove("active"));
  document.querySelectorAll(".tab-trigger").forEach((x) => x.classList.remove("active"));

  const panel = el(tabName);
  if (panel) panel.classList.add("active");

  document.querySelectorAll(`.tab-trigger[data-tab="${tabName}"]`).forEach((btn) => {
    btn.classList.add("active");
  });
}

function initTabs() {
  document.querySelectorAll(".tab-trigger").forEach((btn) => {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
  });
}

function detectDeviceMode() {
  const isMobile = window.matchMedia("(max-width: 980px)").matches;
  state.deviceMode = isMobile ? "mobile" : "web";
  document.body.classList.toggle("is-mobile", isMobile);
  document.body.classList.toggle("is-web", !isMobile);
  el("deviceBadge").textContent = `Device: ${isMobile ? "Mobile" : "Web"}`;
}

function initDeviceMode() {
  detectDeviceMode();
  window.addEventListener("resize", detectDeviceMode);
}

function prefersDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function renderTheme() {
  const resolved = state.themeMode === "auto" ? (prefersDark() ? "dark" : "light") : state.themeMode;
  document.body.classList.remove("theme-light", "theme-dark");
  document.body.classList.add(`theme-${resolved}`);
}

function applyThemeMode(mode) {
  state.themeMode = ["auto", "light", "dark"].includes(mode) ? mode : "auto";
  localStorage.setItem("app_theme_mode", state.themeMode);
  el("themeMode").value = state.themeMode;
  renderTheme();
}

function initThemeMode() {
  const saved = localStorage.getItem("app_theme_mode") || "auto";
  applyThemeMode(saved);
  el("themeMode").addEventListener("change", (event) => {
    applyThemeMode(String(event.target.value));
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (state.themeMode === "auto") renderTheme();
  });
}

function applyViewMode(mode) {
  state.viewMode = mode === "developer" ? "developer" : "public";
  localStorage.setItem("app_view_mode", state.viewMode);

  const devPanel = el("developerPanel");
  const publicBtn = el("publicViewBtn");
  const devBtn = el("developerViewBtn");
  const topKInput = el("topK");
  const monitoringNote = el("monitoringNote");

  if (state.viewMode === "developer") {
    devPanel.classList.remove("hidden");
    if (monitoringNote) monitoringNote.classList.remove("hidden");
    publicBtn.classList.remove("active");
    devBtn.classList.add("active");
    topKInput.disabled = false;
    startMonitoringPolling();
  } else {
    devPanel.classList.add("hidden");
    if (monitoringNote) monitoringNote.classList.add("hidden");
    publicBtn.classList.add("active");
    devBtn.classList.remove("active");
    topKInput.disabled = true;
    stopMonitoringPolling();
  }

  el("activeTopK").textContent = String(currentTopK());
}

function initViewMode() {
  state.defaultTopK = Number(el("topK").value || 4);
  el("publicViewBtn").addEventListener("click", () => applyViewMode("public"));
  el("developerViewBtn").addEventListener("click", () => applyViewMode("developer"));
  applyViewMode(localStorage.getItem("app_view_mode") || "public");
}

function initTopK() {
  el("topK").addEventListener("input", () => {
    el("activeTopK").textContent = String(currentTopK());
  });
}

function initAssistant() {
  el("assistantRefreshBtn").addEventListener("click", () => {
    el("assistantQuery").value = "";
    setHtml("assistantResult", "");
  });

  el("randomPromptBtn").addEventListener("click", () => {
    const idx = Math.floor(Math.random() * quickPrompts.length);
    el("assistantQuery").value = quickPrompts[idx];
  });

  el("generateAnswerBtn").addEventListener("click", async () => {
    const query = el("assistantQuery").value.trim();
    if (!query) return setHtml("assistantResult", "<p>Question cannot be empty.</p>");

    setButtonLoading("generateAnswerBtn", true, "Generating...");
    setHtml("assistantResult", loadingMarkup("Generating answer..."));

    try {
      const data = await postJson("/api/assistant", { query, top_k: currentTopK() });
      const contexts = data.contexts
        .map((c, i) => `<details><summary>Doc ${i + 1}</summary><p>${escapeHtml(c.content)}</p></details>`)
        .join("");
      const metricsHtml = metricChips([
        { label: "Response Time", value: `${data.metrics.response_time_ms} ms` },
        { label: "Total Tokens", value: data.metrics.total_tokens },
        { label: "Retrieved Docs", value: data.metrics.retrieved_docs }
      ]);
      setHtml(
        "assistantResult",
        `<p class="result-title"><strong>${data.blocked ? "Blocked" : "Answer generated"}</strong></p>
         ${metricsHtml}
         <p class="result-body">${escapeHtml(data.answer)}</p>
         <div>${contexts}</div>`
      );
    } catch (err) {
      setHtml("assistantResult", `<p>${escapeHtml(err.message)}</p>`);
    } finally {
      setButtonLoading("generateAnswerBtn", false);
    }
  });
}

function initTrainee() {
  el("traineeRefreshBtn").addEventListener("click", () => {
    el("practiceQuestion").value = "";
    el("traineeAnswer").value = "";
    el("expectedFocus").textContent = "";
    setHtml("evaluationResult", "");
  });

  el("generatePracticeBtn").addEventListener("click", async () => {
    setButtonLoading("generatePracticeBtn", true, "Generating...");
    setHtml("evaluationResult", loadingMarkup("Generating practice question..."));

    try {
      const data = await postJson("/api/practice-question", {
        topic: el("practiceTopic").value,
        difficulty: el("practiceDifficulty").value,
        top_k: currentTopK()
      });
      if (data.blocked) {
        setHtml("evaluationResult", `<p>${escapeHtml(data.block_reason || "Input blocked by safety guardrails.")}</p>`);
        return;
      }
      el("practiceQuestion").value = data.question || "";
      el("expectedFocus").textContent = data.expected_focus?.length ? `Expected focus: ${data.expected_focus.join(" | ")}` : "";
      setHtml("evaluationResult", "");
    } catch (err) {
      setHtml("evaluationResult", `<p>${escapeHtml(err.message)}</p>`);
    } finally {
      setButtonLoading("generatePracticeBtn", false);
    }
  });

  el("evaluateAnswerBtn").addEventListener("click", async () => {
    const question = el("practiceQuestion").value.trim();
    const trainee_answer = el("traineeAnswer").value.trim();
    if (!question || !trainee_answer) {
      return setHtml("evaluationResult", "<p>Both question and trainee answer are required.</p>");
    }

    setButtonLoading("evaluateAnswerBtn", true, "Evaluating...");
    setHtml("evaluationResult", loadingMarkup("Evaluating trainee answer..."));

    try {
      const data = await postJson("/api/evaluate", { question, trainee_answer, top_k: currentTopK() });
      const report = data.evaluation;
      const m = report.metric_scores || {};
      const strengths = (report.strengths || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
      const gaps = (report.gaps || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
      const tips = (report.improvement_tips || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");

      const scoreMetricsHtml = metricChips([
        { label: "Overall", value: `${report.overall_score}/100 (${data.quality_band})` },
        { label: "Accuracy", value: `${m.accuracy || 0}/100` },
        { label: "Completeness", value: `${m.completeness || 0}/100` },
        { label: "SOP", value: `${m.sop_alignment || 0}/100` },
        { label: "Clarity", value: `${m.clarity || 0}/100` },
        { label: "Actionability", value: `${m.actionability || 0}/100` },
        { label: "Evaluation Time", value: `${data.metrics.response_time_ms} ms` }
      ]);

      setHtml(
        "evaluationResult",
        `${scoreMetricsHtml}
         <p><strong>Strengths</strong></p><ul>${strengths}</ul>
         <p><strong>Gaps</strong></p><ul>${gaps}</ul>
         <p><strong>Improvement Tips</strong></p><ul>${tips}</ul>
         ${report.reference_answer ? `<details><summary>Reference Answer</summary><p>${escapeHtml(report.reference_answer)}</p></details>` : ""}`
      );
    } catch (err) {
      setHtml("evaluationResult", `<p>${escapeHtml(err.message)}</p>`);
    } finally {
      setButtonLoading("evaluateAnswerBtn", false);
    }
  });
}

function openMockResultModal(html) {
  const modal = el("mockResultModal");
  const body = el("mockModalBody");
  if (!modal || !body) return;
  body.innerHTML = html;
  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");
}

function closeMockResultModal() {
  const modal = el("mockResultModal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");
}

function initMockModal() {
  const closeBtn = el("mockModalCloseBtn");
  const resetBtn = el("mockModalResetBtn");
  const backdrop = el("mockModalBackdrop");

  if (closeBtn) closeBtn.addEventListener("click", closeMockResultModal);
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (!resetMockAnswers(true)) return;
      closeMockResultModal();
      setHtml("mockResult", "<p>Mock test reset. You can start again from question 1.</p>");
    });
  }
  if (backdrop) backdrop.addEventListener("click", closeMockResultModal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMockResultModal();
  });
}

function renderMockQuestion() {
  const i = state.mock.index;
  const total = state.mock.questions.length;
  if (!total) return;

  el("mockProgress").textContent = `Question ${i + 1} of ${total}`;
  el("mockQuestionText").textContent = state.mock.questions[i];
  el("mockAnswer").value = state.mock.answers[i] || "";
  el("mockPrevBtn").disabled = i <= 0;
  el("mockNextBtn").disabled = i >= total - 1;
}

function updateMockTimer() {
  const ms = state.mock.deadline - Date.now();
  const s = Math.max(0, Math.floor(ms / 1000));
  const min = String(Math.floor(s / 60)).padStart(2, "0");
  const sec = String(s % 60).padStart(2, "0");
  el("mockTimer").textContent = `Time remaining: ${min}:${sec}`;

  if (s <= 0 && !state.mock.submitted) {
    submitMockTest(true);
  }
}

function startMockTimer(minutes) {
  if (state.mock.timerId) clearInterval(state.mock.timerId);
  state.mock.deadline = Date.now() + minutes * 60 * 1000;
  state.mock.timerId = setInterval(updateMockTimer, 1000);
  updateMockTimer();
}

function resetMockAnswers(restartTimer = false) {
  if (!state.mock.questions.length) return false;

  state.mock.answers = new Array(state.mock.questions.length).fill("");
  state.mock.index = 0;
  state.mock.submitted = false;
  renderMockQuestion();

  if (restartTimer) {
    startMockTimer(Number(el("mockMinutes").value || 15));
  }

  return true;
}

async function submitMockTest(auto = false) {
  state.mock.answers[state.mock.index] = el("mockAnswer").value;
  state.mock.submitted = true;
  if (state.mock.timerId) clearInterval(state.mock.timerId);

  if (!auto) {
    setButtonLoading("mockSubmitBtn", true, "Submitting...");
  }
  openMockResultModal(loadingMarkup("Evaluating mock test..."));

  try {
    const data = await postJson("/api/mock/evaluate", {
      questions: state.mock.questions,
      answers: state.mock.answers,
      top_k: currentTopK()
    });

    const reports = (data.reports || []).map((r) => {
      const strengths = (r.report.strengths || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
      const gaps = (r.report.gaps || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
      const tips = (r.report.improvement_tips || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("");
      return `<details><summary>Result Q${r.index}: ${r.score}/100</summary>
                <p><strong>Question:</strong> ${escapeHtml(r.question)}</p>
                <p><strong>Strengths</strong></p><ul>${strengths}</ul>
                <p><strong>Gaps</strong></p><ul>${gaps}</ul>
                <p><strong>Improvement Tips</strong></p><ul>${tips}</ul>
              </details>`;
    }).join("");

    const modalHtml = `<p><strong>${auto ? "Time is up. Test submitted automatically." : "Mock test submitted."}</strong></p>
       <p><strong>Average Score:</strong> ${data.average_score}/100 (${data.quality_band})</p>
       <p><strong>Answered:</strong> ${data.answered_count}/${state.mock.questions.length} | <strong>Total Evaluation Time:</strong> ${data.total_eval_ms} ms</p>
       <div>${reports}</div>`;
    setHtml("mockResult", "");
    openMockResultModal(modalHtml);
  } catch (err) {
    setHtml("mockResult", `<p>${escapeHtml(err.message)}</p>`);
    openMockResultModal(`<p>${escapeHtml(err.message)}</p>`);
  } finally {
    if (!auto) {
      setButtonLoading("mockSubmitBtn", false);
    }
  }
}

function initMock() {
  el("generateMockBtn").addEventListener("click", async () => {
    setButtonLoading("generateMockBtn", true, "Generating...");
    setHtml("mockResult", loadingMarkup("Generating mock test questions..."));

    try {
      const data = await postJson("/api/mock/generate", {
        topic: el("mockTopic").value,
        difficulty: el("mockDifficulty").value,
        count: 5,
        top_k: currentTopK()
      });
      if (data.blocked) {
        return setHtml("mockResult", `<p>${escapeHtml(data.block_reason || "Input blocked by safety guardrails.")}</p>`);
      }
      state.mock.questions = data.questions || [];
      state.mock.answers = new Array(state.mock.questions.length).fill("");
      state.mock.index = 0;
      state.mock.submitted = false;
      el("mockTestArea").classList.remove("hidden");
      setHtml("mockResult", "");
      renderMockQuestion();
      startMockTimer(Number(el("mockMinutes").value || 15));
    } catch (err) {
      setHtml("mockResult", `<p>${escapeHtml(err.message)}</p>`);
    } finally {
      setButtonLoading("generateMockBtn", false);
    }
  });

  el("mockRefreshBtn").addEventListener("click", () => {
    if (!state.mock.questions.length) return;
    state.mock.answers[state.mock.index] = "";
    el("mockAnswer").value = "";
    setHtml("mockResult", "<p>Current mock answer input refreshed.</p>");
  });

  el("mockPrevBtn").addEventListener("click", () => {
    state.mock.answers[state.mock.index] = el("mockAnswer").value;
    state.mock.index = Math.max(0, state.mock.index - 1);
    renderMockQuestion();
  });

  el("mockNextBtn").addEventListener("click", () => {
    state.mock.answers[state.mock.index] = el("mockAnswer").value;
    state.mock.index = Math.min(state.mock.questions.length - 1, state.mock.index + 1);
    renderMockQuestion();
  });

  el("mockAnswer").addEventListener("input", () => {
    if (!state.mock.questions.length) return;
    state.mock.answers[state.mock.index] = el("mockAnswer").value;
  });

  el("mockSubmitBtn").addEventListener("click", () => submitMockTest(false));
}


function formatUsd(value) {
  return `$${Number(value || 0).toFixed(6)}`;
}

function truncateText(text, max = 120) {
  const value = String(text || "").trim();
  if (!value) return "-";
  return value.length > max ? `${escapeHtml(value.slice(0, max))}...` : escapeHtml(value);
}

function renderMonitoringView(data) {
  const summary = data.summary || {};
  const pricing = data.pricing || {};
  const events = Array.isArray(data.events) ? data.events : [];

  setHtml(
    "monitoringSummary",
    `<div class="monitoring-chip"><div>Requests (shown)</div><strong>${summary.request_count || 0}</strong></div>
     <div class="monitoring-chip"><div>Input Tokens</div><strong>${summary.prompt_tokens || 0}</strong></div>
     <div class="monitoring-chip"><div>Output Tokens</div><strong>${summary.completion_tokens || 0}</strong></div>
     <div class="monitoring-chip"><div>Estimated Cost</div><strong>${formatUsd(summary.estimated_cost_usd || 0)}</strong></div>`
  );

  const rows = events.length
    ? events.map((event) => `<tr>
        <td>${escapeHtml(String(event.ts || "-"))}</td>
        <td>${escapeHtml(String(event.endpoint || "-"))}</td>
        <td class="monitoring-query">${truncateText(event.query)}</td>
        <td>${Number(event.prompt_tokens || 0)}</td>
        <td>${Number(event.completion_tokens || 0)}</td>
        <td>${Number(event.total_tokens || 0)}</td>
        <td>${formatUsd(event.estimated_cost_usd || 0)}</td>
      </tr>`).join("")
    : `<tr><td colspan="7">No requests yet.</td></tr>`;

  setHtml("monitoringRows", rows);
  el("monitoringMeta").textContent =
    `Pricing: input ${formatUsd(Number(pricing.input_price_per_1m || 0))}/1M tokens, output ${formatUsd(Number(pricing.output_price_per_1m || 0))}/1M tokens.`;
}

async function refreshMonitoringView(manual = false) {
  if (state.monitoringLoading) return;
  state.monitoringLoading = true;
  if (manual) {
    setButtonLoading("refreshMonitoringBtn", true, "Refreshing...");
  }

  try {
    const res = await fetch("/api/monitoring/recent?limit=20");
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to load monitoring view");
    renderMonitoringView(data);
  } catch (err) {
    setHtml("monitoringSummary", `<div class="monitoring-chip"><div>Error</div><strong>${escapeHtml(err.message)}</strong></div>`);
    setHtml("monitoringRows", `<tr><td colspan="7">${escapeHtml(err.message)}</td></tr>`);
  } finally {
    state.monitoringLoading = false;
    if (manual) {
      setButtonLoading("refreshMonitoringBtn", false);
    }
  }
}

function initResultA11y() {
  ["assistantResult", "evaluationResult", "mockResult", "monitoringMeta"].forEach((id) => {
    const node = el(id);
    if (!node) return;
    node.setAttribute("aria-live", "polite");
  });
}

function initMonitoringControls() {
  const refreshBtn = el("refreshMonitoringBtn");
  if (!refreshBtn) return;
  refreshBtn.addEventListener("click", () => {
    refreshMonitoringView(true);
  });
}

function startMonitoringPolling() {
  if (state.monitoringPoller) return;
  refreshMonitoringView();
  state.monitoringPoller = setInterval(() => refreshMonitoringView(), 10000);
}

function stopMonitoringPolling() {
  if (!state.monitoringPoller) return;
  clearInterval(state.monitoringPoller);
  state.monitoringPoller = null;
}
function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

initTabs();
initDeviceMode();
initThemeMode();
initViewMode();
initTopK();
initAssistant();
initTrainee();
initMockModal();
initMock();
initResultA11y();
initMonitoringControls();























