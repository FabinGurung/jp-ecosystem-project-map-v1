const M01_DATA_URL = "assets/data/m01_schedule_gantt.json";
const M01_NOTICE = "M01 SCHEDULE / GANTT — MANUAL DATA CONTRACT";

let m01Dataset = null;
let m01LoadError = null;
let m01RenderQueued = false;

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function selectedProjectCode() {
  return document.getElementById("detail-code")?.textContent?.trim() || "";
}

function parseDate(value) {
  if (!value) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function fmtDate(value) {
  const date = parseDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", timeZone: "UTC" }).format(date);
}

function fmtRange(start, finish) {
  if (!start && !finish) return "No dates";
  if (start === finish || !finish) return fmtDate(start || finish);
  return `${fmtDate(start)}–${fmtDate(finish)}`;
}

function projectForCode(code) {
  return m01Dataset?.projects?.find((project) => project.company_project_code === code) || null;
}

function statusClass(status) {
  if (status === "COMPLETED") return "done";
  if (status === "IN_PROGRESS") return "current";
  if (status === "BLOCKED" || status === "ON_HOLD") return "blocked";
  return "pending";
}

function activityButton(work, prefix, meta) {
  return `<button class="site-ops-activity-button" type="button" data-m01-work="${escapeHTML(work.work_id)}">
    <span class="site-ops-step">${escapeHTML(prefix)}</span>
    <span class="site-ops-activity-copy"><strong>${escapeHTML(work.work_name)}</strong><small>${escapeHTML(work.work_id)} · ${escapeHTML(meta)}</small></span>
    <span class="site-ops-open-resource" aria-hidden="true">›</span>
  </button>`;
}

function milestoneRows(works) {
  const groups = new Map();
  for (const work of works) {
    const name = work.milestone || "Unassigned";
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(work);
  }
  return [...groups.entries()].map(([name, items]) => {
    let state = "pending";
    if (items.every((item) => item.status === "COMPLETED")) state = "done";
    else if (items.some((item) => ["IN_PROGRESS", "BLOCKED", "ON_HOLD"].includes(item.status))) state = "current";
    const icon = state === "done" ? "✓" : state === "current" ? "●" : "○";
    return `<div class="site-ops-milestone ${state}"><span>${icon}</span><strong>${escapeHTML(name)}</strong></div>`;
  }).join("");
}

function ganttRows(works) {
  const visible = works.filter((work) => work.status !== "COMPLETED" && parseDate(work.planned_start) && parseDate(work.planned_finish));
  if (!visible.length) return '<div class="site-ops-placeholder"><span>No dated current/upcoming work in M01.</span></div>';

  const starts = visible.map((work) => parseDate(work.planned_start).getTime());
  const finishes = visible.map((work) => parseDate(work.planned_finish).getTime());
  const min = Math.min(...starts);
  const max = Math.max(...finishes);
  const span = Math.max(max - min, 86400000);

  return visible.map((work) => {
    const start = parseDate(work.planned_start).getTime();
    const finish = parseDate(work.planned_finish).getTime();
    const left = Math.max(0, ((start - min) / span) * 100);
    const width = Math.max(3, ((finish - start + 86400000) / span) * 100);
    const state = statusClass(work.status);
    return `<div class="site-ops-gantt-row">
      <span class="site-ops-gantt-label">${escapeHTML(work.work_name)}</span>
      <span class="site-ops-gantt-track"><span class="site-ops-gantt-bar ${state === "pending" ? "next" : state}" style="--gantt-start:${left.toFixed(2)}%;--gantt-width:${Math.min(width, 100-left).toFixed(2)}%"></span></span>
    </div>`;
  }).join("");
}

function renderM01() {
  const panel = document.getElementById("panel-works");
  if (!panel) return;

  const code = selectedProjectCode();
  const project = projectForCode(code);
  const existing = panel.querySelector("[data-site-ops-schedule]");

  if (!project) {
    if (existing?.dataset.m01 === "true") existing.remove();
    return;
  }

  if (existing?.dataset.m01 !== "true") existing?.remove();
  const old = panel.querySelector('[data-site-ops-schedule][data-m01="true"]');
  old?.remove();

  const works = [...project.works].sort((a, b) => Number(a.sequence) - Number(b.sequence));
  const current = works.find((work) => work.status === "IN_PROGRESS")
    || works.find((work) => ["BLOCKED", "ON_HOLD"].includes(work.status))
    || works.find((work) => work.status === "NOT_STARTED")
    || works[0];
  const next = works.filter((work) => work.status === "NOT_STARTED" && work.work_id !== current?.work_id).slice(0, 5);
  const previous = works.filter((work) => work.status === "COMPLETED")
    .sort((a, b) => (b.actual_finish || b.planned_finish || "").localeCompare(a.actual_finish || a.planned_finish || ""))
    .slice(0, 5);

  const root = document.createElement("div");
  root.dataset.siteOpsSchedule = "true";
  root.dataset.m01 = "true";
  root.className = "site-ops-prototype";

  const dataLabel = m01Dataset.dataset_status === "SYNTHETIC_DEMO_NOT_LIVE_SITE_DATA"
    ? "🧪 SYNTHETIC DEMO — NOT LIVE SITE DATA"
    : "📝 MANUAL M01 SNAPSHOT";

  root.innerHTML = `<div class="site-ops-demo-banner"><strong>${dataLabel}</strong><span>${escapeHTML(M01_NOTICE)} · ${escapeHTML(project.canonical_project_id)} · Updated ${escapeHTML(project.update_date)} · Source ${escapeHTML(project.source_status)}</span></div>
    <div class="site-ops-kpi-grid">
      <div class="site-ops-kpi"><span>Overall progress</span><strong>${Number(project.overall_progress_percent) || 0}%</strong><div class="site-ops-progress-track"><span style="width:${Math.max(0, Math.min(100, Number(project.overall_progress_percent) || 0))}%"></span></div></div>
      <div class="site-ops-kpi"><span>Current activity</span><strong>${escapeHTML(current?.work_name || "No active work")}</strong><small>${current ? `${Number(current.progress_percent) || 0}% · ${fmtRange(current.planned_start, current.planned_finish)}` : "—"}</small></div>
    </div>
    <section class="site-ops-section">
      <h3>▶ Current work</h3>
      ${current ? activityButton(current, "▶", `${fmtRange(current.planned_start, current.planned_finish)} · ${Number(current.progress_percent) || 0}% complete`) : '<div class="site-ops-placeholder"><span>No current work in M01.</span></div>'}
    </section>
    <section class="site-ops-section">
      <h3>⏭ Next 5 works</h3>
      <div class="site-ops-activity-list">${next.length ? next.map((work, index) => activityButton(work, String(index + 1), fmtRange(work.planned_start, work.planned_finish))).join("") : '<div class="site-ops-placeholder"><span>No upcoming work in M01.</span></div>'}</div>
    </section>
    <section class="site-ops-section">
      <h3>✅ Previous 5 completed</h3>
      <div class="site-ops-activity-list previous">${previous.length ? previous.map((work) => activityButton(work, "✓", `Completed ${fmtDate(work.actual_finish || work.planned_finish)}`)).join("") : '<div class="site-ops-placeholder"><span>No completed work in M01.</span></div>'}</div>
    </section>
    <section class="site-ops-section">
      <h3>📍 Milestones</h3>
      <div class="site-ops-milestones">${milestoneRows(works)}</div>
    </section>
    <section class="site-ops-section">
      <div class="site-ops-section-head"><h3>📊 Mini Gantt / look-ahead</h3><span>M01 dates</span></div>
      <div class="site-ops-gantt">${ganttRows(works)}</div>
    </section>`;

  panel.prepend(root);
  const count = document.getElementById("works-tab-count");
  if (count) count.textContent = "M01";

  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-m01-work]");
    if (!button) return;
    const workId = button.dataset.m01Work;
    window.dispatchEvent(new CustomEvent("jp:m01-work-selected", { detail: { workId } }));
  });
}

function queueRender() {
  if (m01RenderQueued) return;
  m01RenderQueued = true;
  window.requestAnimationFrame(() => {
    m01RenderQueued = false;
    renderM01();
  });
}

async function loadM01() {
  try {
    const response = await fetch(M01_DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`M01 data load failed: HTTP ${response.status}`);
    const payload = await response.json();
    if (payload?.module !== "M01_SCHEDULE_GANTT" || !Array.isArray(payload.projects)) {
      throw new Error("M01 data contract is invalid");
    }
    m01Dataset = payload;
  } catch (error) {
    m01LoadError = error;
    console.error("M01 Schedule/Gantt disabled:", error);
  } finally {
    queueRender();
  }
}

function initializeM01() {
  const detailCode = document.getElementById("detail-code");
  if (detailCode) {
    const observer = new MutationObserver(queueRender);
    observer.observe(detailCode, { childList: true, subtree: true, characterData: true });
  }
  loadM01();
}

initializeM01();
