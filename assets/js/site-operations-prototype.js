const DEMO_PROJECT_CODE = "FBL-005";
const DEMO_PROJECT_NAME = "31 Sharada Adhikari";
const DEMO_NOTICE = "SYNTHETIC DEMO — NOT LIVE SITE DATA";

const demoSchedule = {
  attention: {
    level: "ATTENTION REQUIRED",
    reason: "Internal plaster is shown as the current activity, while the demo resource check shows a sand shortage.",
  },
  overallProgress: 62,
  current: {
    workId: "WRK-000005",
    name: "Internal Plaster",
    progress: 60,
    planned: "Aug 19–20",
  },
  next: [
    { workId: "WRK-000006", name: "External Plaster", planned: "Aug 21–23" },
    { workId: "WRK-000011", name: "Floor Screed", planned: "Aug 24–25" },
    { workId: "WRK-000013", name: "Porcelain Glazed Tile Flooring", planned: "Aug 26–29" },
    { workId: "WRK-000016", name: "Sal Wood Door/Window Frames", planned: "Aug 30–Sep 1" },
    { workId: "WRK-000009", name: "Internal Emulsion Paint", planned: "Sep 2–5" },
  ],
  previous: [
    { workId: "WRK-000003", name: "Brick Masonry in Cement Mortar", finished: "Aug 18" },
    { workId: "WRK-000023", name: "Cementitious Waterproofing", finished: "Aug 17" },
    { workId: "WRK-000002", name: "Centering and Shuttering for RCC Works", finished: "Aug 15" },
    { workId: "WRK-000027", name: "Reinforcement Steel", finished: "Aug 14" },
    { workId: "WRK-000001", name: "PCC (M20) for RCC Works", finished: "Aug 12" },
  ],
  milestones: [
    { name: "Structural works", status: "done" },
    { name: "Masonry", status: "done" },
    { name: "Plaster", status: "current" },
    { name: "Flooring & joinery", status: "pending" },
    { name: "Finishing & handover", status: "pending" },
  ],
  gantt: [
    { name: "Internal plaster", start: 0, width: 24, status: "current" },
    { name: "External plaster", start: 20, width: 28, status: "next" },
    { name: "Floor screed", start: 43, width: 18, status: "next" },
    { name: "Tile flooring", start: 56, width: 26, status: "next" },
    { name: "Door frames", start: 73, width: 17, status: "next" },
    { name: "Internal paint", start: 84, width: 16, status: "next" },
  ],
};

const demoResources = {
  "WRK-000005": {
    name: "Internal Plaster",
    resources: [
      { type: "Material", name: "Cement", required: "20 bags", available: "28 bags", state: "ready" },
      { type: "Material", name: "Sand", required: "2.0 m³", available: "0.8 m³", state: "blocked" },
      { type: "Equipment", name: "Scaffolding", required: "1 set", available: "1 set", state: "ready" },
      { type: "Equipment", name: "Mixer", required: "1", available: "1", state: "ready" },
    ],
  },
  "WRK-000006": {
    name: "External Plaster",
    resources: [
      { type: "Material", name: "Cement", required: "24 bags", available: "28 bags", state: "ready" },
      { type: "Material", name: "Sand", required: "2.5 m³", available: "0.8 m³", state: "blocked" },
      { type: "Equipment", name: "Scaffolding", required: "2 sets", available: "1 set", state: "blocked" },
    ],
  },
  "WRK-000011": {
    name: "Floor Screed",
    resources: [
      { type: "Material", name: "Cement", required: "15 bags", available: "28 bags", state: "ready" },
      { type: "Material", name: "Sand", required: "1.5 m³", available: "0.8 m³", state: "watch" },
      { type: "Equipment", name: "Mixer", required: "1", available: "1", state: "ready" },
    ],
  },
  "WRK-000013": {
    name: "Porcelain Glazed Tile Flooring",
    resources: [
      { type: "Material", name: "Tiles", required: "85 m²", available: "0 m²", state: "blocked" },
      { type: "Material", name: "Tile adhesive", required: "12 bags", available: "0 bags", state: "blocked" },
      { type: "Equipment", name: "Tile cutter", required: "1", available: "1", state: "ready" },
    ],
  },
  "WRK-000016": {
    name: "Sal Wood Door/Window Frames",
    resources: [
      { type: "Material", name: "Sal timber frames", required: "8", available: "0", state: "blocked" },
      { type: "Equipment", name: "Carpenter tool set", required: "1 set", available: "1 set", state: "ready" },
    ],
  },
  "WRK-000009": {
    name: "Internal Emulsion Paint",
    resources: [
      { type: "Material", name: "Paint", required: "6 pails", available: "0 pails", state: "blocked" },
      { type: "Equipment", name: "Roller/brush sets", required: "2 sets", available: "2 sets", state: "ready" },
    ],
  },
};

let selectedDemoWorkId = demoSchedule.current.workId;
let scheduledRender = false;

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

function demoBanner() {
  return `<div class="site-ops-demo-banner"><strong>🧪 ${DEMO_NOTICE}</strong><span>Interface-only sample for ${escapeHTML(DEMO_PROJECT_CODE)} — ${escapeHTML(DEMO_PROJECT_NAME)}. These schedule, progress, equipment and stock values are not read from Drive, Discord, AppSheet, Apps Script or live site records.</span></div>`;
}

function activityButton(activity, prefix, meta) {
  return `<button class="site-ops-activity-button" type="button" data-demo-work="${escapeHTML(activity.workId)}">
    <span class="site-ops-step">${escapeHTML(prefix)}</span>
    <span class="site-ops-activity-copy"><strong>${escapeHTML(activity.name)}</strong><small>${escapeHTML(activity.workId)} · ${escapeHTML(meta)}</small></span>
    <span class="site-ops-open-resource" aria-hidden="true">›</span>
  </button>`;
}

function milestoneHTML(item) {
  const icon = item.status === "done" ? "✓" : item.status === "current" ? "●" : "○";
  return `<div class="site-ops-milestone ${escapeHTML(item.status)}"><span>${icon}</span><strong>${escapeHTML(item.name)}</strong></div>`;
}

function ganttHTML(item) {
  return `<div class="site-ops-gantt-row">
    <span class="site-ops-gantt-label">${escapeHTML(item.name)}</span>
    <span class="site-ops-gantt-track"><span class="site-ops-gantt-bar ${escapeHTML(item.status)}" style="--gantt-start:${item.start}%;--gantt-width:${item.width}%"></span></span>
  </div>`;
}

function renderSchedulePrototype() {
  const panel = document.getElementById("panel-works");
  if (!panel || panel.querySelector("[data-site-ops-schedule]")) return;

  const code = selectedProjectCode();
  const root = document.createElement("div");
  root.dataset.siteOpsSchedule = "true";
  root.className = "site-ops-prototype";

  if (code !== DEMO_PROJECT_CODE) {
    root.innerHTML = `<div class="site-ops-placeholder"><strong>🧪 CEO operations prototype</strong><span>The interactive Schedule &amp; Progress demo is currently configured only for <code>${DEMO_PROJECT_CODE}</code> — ${DEMO_PROJECT_NAME}. Existing public project information below remains unchanged.</span></div>`;
    panel.prepend(root);
    return;
  }

  const next = demoSchedule.next.map((item, index) => activityButton(item, String(index + 1), item.planned)).join("");
  const previous = demoSchedule.previous.map((item, index) => activityButton(item, "✓", `Completed ${item.finished}`)).join("");
  root.innerHTML = `${demoBanner()}
    <div class="site-ops-attention danger"><div><span class="site-ops-eyebrow">CEO attention</span><strong>🔴 ${escapeHTML(demoSchedule.attention.level)}</strong></div><p>${escapeHTML(demoSchedule.attention.reason)}</p></div>
    <div class="site-ops-kpi-grid">
      <div class="site-ops-kpi"><span>Overall progress</span><strong>${demoSchedule.overallProgress}%</strong><div class="site-ops-progress-track"><span style="width:${demoSchedule.overallProgress}%"></span></div></div>
      <div class="site-ops-kpi"><span>Current activity</span><strong>${escapeHTML(demoSchedule.current.name)}</strong><small>${demoSchedule.current.progress}% demo progress</small></div>
    </div>
    <section class="site-ops-section">
      <h3>▶ Current work</h3>
      ${activityButton(demoSchedule.current, "▶", `${demoSchedule.current.planned} · ${demoSchedule.current.progress}% complete`)}
    </section>
    <section class="site-ops-section">
      <h3>⏭ Next 5 works</h3>
      <div class="site-ops-activity-list">${next}</div>
    </section>
    <section class="site-ops-section">
      <h3>✅ Previous 5 completed</h3>
      <div class="site-ops-activity-list previous">${previous}</div>
    </section>
    <section class="site-ops-section">
      <h3>📍 Milestones</h3>
      <div class="site-ops-milestones">${demoSchedule.milestones.map(milestoneHTML).join("")}</div>
    </section>
    <section class="site-ops-section">
      <div class="site-ops-section-head"><h3>📊 Mini Gantt / look-ahead</h3><span>Demo horizon</span></div>
      <div class="site-ops-gantt">${demoSchedule.gantt.map(ganttHTML).join("")}</div>
    </section>`;

  panel.prepend(root);
  const count = document.getElementById("works-tab-count");
  if (count) count.textContent = "DEMO";

  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-demo-work]");
    if (!button) return;
    selectedDemoWorkId = button.dataset.demoWork;
    document.getElementById("tab-materials")?.click();
    renderResourcePrototype();
  });
}

function readinessLabel(state) {
  if (state === "ready") return ["✅ Ready", "ready"];
  if (state === "watch") return ["🟡 Short", "watch"];
  return ["🔴 Missing", "blocked"];
}

function renderResourcePrototype() {
  const panel = document.getElementById("panel-materials");
  if (!panel) return;

  const existing = panel.querySelector("[data-site-ops-resources]");
  const code = selectedProjectCode();
  if (code !== DEMO_PROJECT_CODE) {
    if (!existing) {
      const root = document.createElement("div");
      root.dataset.siteOpsResources = "true";
      root.className = "site-ops-prototype";
      root.innerHTML = `<div class="site-ops-placeholder"><strong>🧪 Resource readiness prototype</strong><span>Select <code>${DEMO_PROJECT_CODE}</code> to preview the synthetic work → materials/equipment relationship. Real stock remains protected by the existing public-inventory gate.</span></div>`;
      panel.append(root);
    }
    return;
  }

  const requirement = demoResources[selectedDemoWorkId] || demoResources[demoSchedule.current.workId];
  if (existing?.dataset.workId === selectedDemoWorkId) return;
  existing?.remove();

  const rows = requirement.resources.map((resource) => {
    const [label, className] = readinessLabel(resource.state);
    return `<div class="site-ops-resource-row">
      <span><small>${escapeHTML(resource.type)}</small><strong>${escapeHTML(resource.name)}</strong></span>
      <span><small>Required</small><strong>${escapeHTML(resource.required)}</strong></span>
      <span><small>Demo available</small><strong>${escapeHTML(resource.available)}</strong></span>
      <span class="site-ops-readiness ${className}">${label}</span>
    </div>`;
  }).join("");

  const blocked = requirement.resources.filter((item) => item.state !== "ready").length;
  const root = document.createElement("div");
  root.dataset.siteOpsResources = "true";
  root.dataset.workId = selectedDemoWorkId;
  root.className = "site-ops-prototype";
  root.innerHTML = `${demoBanner()}
    <section class="site-ops-section site-ops-resource-section">
      <div class="site-ops-section-head"><div><span class="site-ops-eyebrow">Selected work</span><h3>${escapeHTML(requirement.name)}</h3><small>${escapeHTML(selectedDemoWorkId)}</small></div><span class="site-ops-readiness ${blocked ? "blocked" : "ready"}">${blocked ? `🔴 ${blocked} issue${blocked > 1 ? "s" : ""}` : "✅ Ready"}</span></div>
      <div class="site-ops-resource-header"><span>Resource</span><span>Required</span><span>Available</span><span>Status</span></div>
      <div class="site-ops-resource-table">${rows}</div>
      <div class="site-ops-procurement-note"><strong>🟡 Procurement link — next phase</strong><span>This prototype detects a shortage visually but does not create purchase orders, update stock, or write private data.</span></div>
    </section>`;
  panel.append(root);

  const count = document.getElementById("materials-tab-count");
  if (count) count.textContent = "DEMO";
}

function ensurePrototype() {
  if (scheduledRender) return;
  scheduledRender = true;
  window.requestAnimationFrame(() => {
    scheduledRender = false;
    renderSchedulePrototype();
    renderResourcePrototype();
  });
}

function handleM01WorkSelected(event) {
  const workId = String(event.detail?.workId || "").trim();
  if (!workId || !demoResources[workId]) return;
  selectedDemoWorkId = workId;
  document.getElementById("tab-materials")?.click();
  renderResourcePrototype();
}

window.addEventListener("jp:m01-work-selected", handleM01WorkSelected);

function initializePrototype() {
  const targets = [
    document.getElementById("detail-code"),
    document.getElementById("panel-works"),
    document.getElementById("panel-materials"),
  ].filter(Boolean);

  const observer = new MutationObserver(ensurePrototype);
  targets.forEach((target) => observer.observe(target, { childList: true, subtree: true, characterData: true }));
  ensurePrototype();
}

initializePrototype();
