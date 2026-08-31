const M02_DATA_URL = "assets/data/m02_progress_report.json";
const M02_NOTICE = "M02 PROGRESS REPORT — OBSERVED / MANUAL PROGRESS CONTRACT";

let m02Dataset = null;
let m02RenderQueued = false;

function m02EscapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function m02SelectedProjectCode() {
  return document.getElementById("detail-code")?.textContent?.trim() || "";
}

function m02ProjectForCode(code) {
  return m02Dataset?.projects?.find((project) => project.company_project_code === code) || null;
}

function m02StatusMeta(status) {
  if (status === "COMPLETED") return ["✓ Completed", "done"];
  if (status === "IN_PROGRESS") return ["▶ In progress", "current"];
  if (status === "BLOCKED") return ["● Blocked", "blocked"];
  if (status === "ON_HOLD") return ["● On hold", "blocked"];
  if (status === "NOT_APPLICABLE") return ["— N/A", "pending"];
  return ["○ Not started", "pending"];
}

function m02ProgressCard(update) {
  const [statusLabel, statusClass] = m02StatusMeta(update.status);
  const progress = Math.max(0, Math.min(100, Number(update.progress_percent) || 0));
  return `<div class="site-ops-activity-button" data-m02-work="${m02EscapeHTML(update.work_id)}">
    <span class="site-ops-step">${m02EscapeHTML(statusLabel.split(" ")[0])}</span>
    <span class="site-ops-activity-copy">
      <strong>${m02EscapeHTML(update.work_name)}</strong>
      <small>${m02EscapeHTML(update.work_id)} · ${m02EscapeHTML(statusLabel)} · ${progress}% · Updated ${m02EscapeHTML(update.update_date)}</small>
      <small>${m02EscapeHTML(update.evidence_note)}</small>
      <small>Evidence ref: ${m02EscapeHTML(update.evidence_reference)}</small>
      <span class="site-ops-progress-track" aria-label="${progress}% complete"><span style="width:${progress}%"></span></span>
    </span>
    <span class="site-ops-readiness ${statusClass}">${progress}%</span>
  </div>`;
}

function renderM02() {
  const panel = document.getElementById("panel-works");
  if (!panel) return;

  const code = m02SelectedProjectCode();
  const project = m02ProjectForCode(code);
  const existing = panel.querySelector('[data-site-ops-progress][data-m02="true"]');

  if (!project) {
    existing?.remove();
    return;
  }

  existing?.remove();

  const updates = Array.isArray(project.progress_updates) ? [...project.progress_updates] : [];
  const current = updates.filter((item) => ["IN_PROGRESS", "BLOCKED", "ON_HOLD"].includes(item.status));
  const completed = updates.filter((item) => item.status === "COMPLETED")
    .sort((a, b) => String(b.update_date).localeCompare(String(a.update_date)))
    .slice(0, 5);
  const next = updates.filter((item) => item.status === "NOT_STARTED").slice(0, 5);
  const latest = updates.reduce((best, item) => !best || String(item.update_date) > String(best.update_date) ? item : best, null);
  const blockedCount = updates.filter((item) => ["BLOCKED", "ON_HOLD"].includes(item.status)).length;

  const root = document.createElement("div");
  root.dataset.siteOpsProgress = "true";
  root.dataset.m02 = "true";
  root.className = "site-ops-prototype";

  const dataLabel = m02Dataset.dataset_status === "SYNTHETIC_DEMO_NOT_LIVE_SITE_DATA"
    ? "🧪 SYNTHETIC DEMO — NOT LIVE SITE DATA"
    : "📝 MANUAL M02 PROGRESS SNAPSHOT";

  root.innerHTML = `<div class="site-ops-demo-banner"><strong>${dataLabel}</strong><span>${m02EscapeHTML(M02_NOTICE)} · ${m02EscapeHTML(project.canonical_project_id)} · Snapshot ${m02EscapeHTML(project.update_date)} · Source ${m02EscapeHTML(project.source_status)}</span></div>
    <div class="site-ops-kpi-grid">
      <div class="site-ops-kpi"><span>Observed current works</span><strong>${current.length}</strong><small>${latest ? `Latest update ${m02EscapeHTML(latest.update_date)}` : "No observations"}</small></div>
      <div class="site-ops-kpi"><span>Blocked / on hold</span><strong>${blockedCount}</strong><small>M02 reports observation only; it does not invent missing reasons.</small></div>
    </div>
    <section class="site-ops-section">
      <div class="site-ops-section-head"><h3>📝 M02 field progress snapshot</h3><span>${m02EscapeHTML(project.update_date)}</span></div>
      ${current.length ? `<div class="site-ops-activity-list">${current.map(m02ProgressCard).join("")}</div>` : '<div class="site-ops-placeholder"><span>No current/blocked work reported in M02.</span></div>'}
    </section>
    <section class="site-ops-section">
      <h3>✅ Recently completed</h3>
      <div class="site-ops-activity-list previous">${completed.length ? completed.map(m02ProgressCard).join("") : '<div class="site-ops-placeholder"><span>No completed work reported in M02.</span></div>'}</div>
    </section>
    <section class="site-ops-section">
      <h3>⏭ Reported next / not started</h3>
      <div class="site-ops-activity-list">${next.length ? next.map(m02ProgressCard).join("") : '<div class="site-ops-placeholder"><span>No not-started work reported in M02.</span></div>'}</div>
    </section>`;

  const m01 = panel.querySelector('[data-site-ops-schedule][data-m01="true"]');
  if (m01) m01.insertAdjacentElement("afterend", root);
  else panel.prepend(root);

  const count = document.getElementById("works-tab-count");
  if (count) count.textContent = "M01+M02";
}

function queueM02Render() {
  if (m02RenderQueued) return;
  m02RenderQueued = true;
  window.requestAnimationFrame(() => {
    m02RenderQueued = false;
    renderM02();
  });
}

async function loadM02() {
  try {
    const response = await fetch(M02_DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`M02 data load failed: HTTP ${response.status}`);
    const payload = await response.json();
    if (payload?.module !== "M02_PROGRESS_REPORT" || !Array.isArray(payload.projects)) {
      throw new Error("M02 data contract is invalid");
    }
    m02Dataset = payload;
  } catch (error) {
    console.error("M02 Progress Report disabled:", error);
  } finally {
    queueM02Render();
  }
}

function initializeM02() {
  const detailCode = document.getElementById("detail-code");
  if (detailCode) {
    const observer = new MutationObserver(queueM02Render);
    observer.observe(detailCode, { childList: true, subtree: true, characterData: true });
  }
  loadM02();
}

initializeM02();
