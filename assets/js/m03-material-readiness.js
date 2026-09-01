const M03_DATA_URL = "assets/data/m03_material_readiness.json";
const M03_NOTICE = "M03 MATERIAL QUANTITY / READINESS — UNKNOWN REMAINS UNKNOWN";

window.JP_M03_MATERIAL_READINESS_ACTIVE = true;

let m03Dataset = null;
let selectedM03WorkId = null;
let lastM03ProjectCode = null;
let m03RenderQueued = false;

function m03EscapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function m03SelectedProjectCode() {
  return document.getElementById("detail-code")?.textContent?.trim() || "";
}

function m03ProjectForCode(code) {
  return m03Dataset?.projects?.find((project) => project.company_project_code === code) || null;
}

function m03StatusMeta(status) {
  if (status === "READY") return ["✅ Ready", "ready"];
  if (status === "SHORT") return ["🟡 Short", "watch"];
  if (status === "MISSING") return ["🔴 Missing", "blocked"];
  if (status === "NOT_APPLICABLE") return ["— N/A", "ready"];
  return ["❔ Unknown", "watch"];
}

function m03Quantity(value, unit) {
  if (value === null || value === undefined || value === "" || !unit) return "UNKNOWN";
  return `${m03EscapeHTML(value)} ${m03EscapeHTML(unit)}`;
}

function m03WorkGroups(project) {
  const groups = [];
  const byId = new Map();
  for (const row of project.work_materials || []) {
    let group = byId.get(row.work_id);
    if (!group) {
      group = { work_id: row.work_id, work_name: row.work_name, materials: [] };
      byId.set(row.work_id, group);
      groups.push(group);
    }
    group.materials.push(row);
  }
  return groups;
}

function m03MaterialRow(row) {
  const [label, className] = m03StatusMeta(row.readiness_status);
  const materialId = row.material_id ? m03EscapeHTML(row.material_id) : "UNMAPPED";
  return `<div class="site-ops-resource-row" data-m03-material="${materialId}">
    <span><small>Material · ${materialId}</small><strong>${m03EscapeHTML(row.material_name)}</strong></span>
    <span><small>Required</small><strong>${m03Quantity(row.required_quantity, row.unit)}</strong></span>
    <span><small>Available</small><strong>${m03Quantity(row.available_quantity, row.unit)}</strong></span>
    <span class="site-ops-readiness ${className}">${label}</span>
    <span style="grid-column:1/-1"><small>${m03EscapeHTML(row.evidence_note)}</small></span>
  </div>`;
}

function m03WorkButton(group) {
  const statuses = group.materials.map((row) => row.readiness_status);
  const summary = statuses.includes("MISSING") ? "MISSING" : statuses.includes("SHORT") ? "SHORT" : statuses.includes("UNKNOWN") ? "UNKNOWN" : "READY";
  const [label, className] = m03StatusMeta(summary);
  const active = group.work_id === selectedM03WorkId ? " aria-current=\"true\"" : "";
  return `<button class="site-ops-activity-button" type="button" data-m03-work-select="${m03EscapeHTML(group.work_id)}"${active}>
    <span class="site-ops-step">${group.work_id === selectedM03WorkId ? "▶" : "○"}</span>
    <span class="site-ops-activity-copy"><strong>${m03EscapeHTML(group.work_name)}</strong><small>${m03EscapeHTML(group.work_id)} · ${group.materials.length} material record${group.materials.length === 1 ? "" : "s"}</small></span>
    <span class="site-ops-readiness ${className}">${label}</span>
  </button>`;
}

function renderM03() {
  const panel = document.getElementById("panel-materials");
  if (!panel) return;

  panel.querySelector('[data-site-ops-resources]')?.remove();
  panel.querySelector('[data-m03-material-readiness="true"]')?.remove();

  const code = m03SelectedProjectCode();
  const project = m03ProjectForCode(code);

  if (code !== lastM03ProjectCode) {
    selectedM03WorkId = null;
    lastM03ProjectCode = code;
  }

  const root = document.createElement("div");
  root.dataset.m03MaterialReadiness = "true";
  root.className = "site-ops-prototype";

  if (!project) {
    root.innerHTML = `<div class="site-ops-placeholder"><strong>📦 M03 material readiness</strong><span>No public-safe M03 material snapshot is registered for this project. Material quantities and readiness remain <strong>UNKNOWN</strong>; the interface will not infer stock from schedule, progress, payments, or old demo values.</span></div>`;
    panel.append(root);
    const count = document.getElementById("materials-tab-count");
    if (count) count.textContent = "M03";
    return;
  }

  const groups = m03WorkGroups(project);
  if (!selectedM03WorkId && groups.length) selectedM03WorkId = groups[0].work_id;
  const selectedGroup = groups.find((group) => group.work_id === selectedM03WorkId) || null;

  const datasetLabel = m03Dataset.dataset_status === "SYNTHETIC_UI_EVIDENCE_NOT_LIVE_INVENTORY"
    ? "🧪 SYNTHETIC UI EVIDENCE — NOT LIVE INVENTORY"
    : "📦 MATERIAL READINESS SNAPSHOT";

  let selectedHTML;
  if (!selectedGroup) {
    selectedHTML = `<div class="site-ops-placeholder"><strong>❔ Selected work has no M03 material record</strong><span>${m03EscapeHTML(selectedM03WorkId || "No work selected")} is not represented in this bounded M03 snapshot. Required quantity, available quantity and readiness remain UNKNOWN.</span></div>`;
  } else {
    const statuses = selectedGroup.materials.map((row) => row.readiness_status);
    const issueCount = statuses.filter((status) => ["SHORT", "MISSING", "UNKNOWN"].includes(status)).length;
    const summaryStatus = statuses.includes("MISSING") ? "MISSING" : statuses.includes("SHORT") ? "SHORT" : statuses.includes("UNKNOWN") ? "UNKNOWN" : "READY";
    const [summaryLabel, summaryClass] = m03StatusMeta(summaryStatus);
    selectedHTML = `<section class="site-ops-section site-ops-resource-section">
      <div class="site-ops-section-head"><div><span class="site-ops-eyebrow">Selected work</span><h3>${m03EscapeHTML(selectedGroup.work_name)}</h3><small>${m03EscapeHTML(selectedGroup.work_id)}</small></div><span class="site-ops-readiness ${summaryClass}">${summaryLabel}</span></div>
      <div class="site-ops-resource-header"><span>Material</span><span>Required</span><span>Available</span><span>Status</span></div>
      <div class="site-ops-resource-table">${selectedGroup.materials.map(m03MaterialRow).join("")}</div>
      <div class="site-ops-procurement-note"><strong>${issueCount ? `Material attention: ${issueCount} item${issueCount === 1 ? "" : "s"}` : "Material snapshot ready"}</strong><span>M03 is read-only. It does not create purchase orders, modify inventory, or infer missing quantities.</span></div>
    </section>`;
  }

  root.innerHTML = `<div class="site-ops-demo-banner"><strong>${datasetLabel}</strong><span>${m03EscapeHTML(M03_NOTICE)} · ${m03EscapeHTML(project.canonical_project_id)} · Snapshot ${m03EscapeHTML(project.update_date)} · Source ${m03EscapeHTML(project.source_status)}</span></div>
    <section class="site-ops-section">
      <div class="site-ops-section-head"><h3>📦 Work → material readiness</h3><span>${groups.length} work${groups.length === 1 ? "" : "s"}</span></div>
      <div class="site-ops-activity-list">${groups.map(m03WorkButton).join("")}</div>
    </section>
    ${selectedHTML}`;

  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-m03-work-select]");
    if (!button) return;
    selectedM03WorkId = button.dataset.m03WorkSelect;
    renderM03();
  });

  panel.append(root);
  const count = document.getElementById("materials-tab-count");
  if (count) count.textContent = "M03";
}

function queueM03Render() {
  if (m03RenderQueued) return;
  m03RenderQueued = true;
  window.requestAnimationFrame(() => {
    m03RenderQueued = false;
    renderM03();
  });
}

function handleM03WorkSelected(event) {
  const workId = String(event.detail?.workId || "").trim();
  if (!workId) return;
  selectedM03WorkId = workId;
  document.getElementById("tab-materials")?.click();
  queueM03Render();
}

window.addEventListener("jp:m01-work-selected", handleM03WorkSelected);

async function loadM03() {
  try {
    const response = await fetch(M03_DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`M03 data load failed: HTTP ${response.status}`);
    const payload = await response.json();
    if (payload?.module !== "M03_MATERIAL_QUANTITY_READINESS" || !Array.isArray(payload.projects)) {
      throw new Error("M03 data contract is invalid");
    }
    m03Dataset = payload;
  } catch (error) {
    console.error("M03 Material Readiness disabled:", error);
  } finally {
    queueM03Render();
  }
}

function initializeM03() {
  const detailCode = document.getElementById("detail-code");
  if (detailCode) {
    const observer = new MutationObserver(queueM03Render);
    observer.observe(detailCode, { childList: true, subtree: true, characterData: true });
  }
  loadM03();
}

initializeM03();
