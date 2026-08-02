import { parseBoolean, parseCSV, parseOptionalNumber } from "./csv.js";

const state = {
  config: null,
  projects: [],
  organizations: [],
  people: [],
  projectParties: [],
  projectFunding: [],
  workCatalog: [],
  projectWorkItems: [],
  materialsMaster: [],
  projectMaterialInventory: [],
  projectComponents: [],
  projectSourceLinks: [],
  projectOpportunities: [],
  organizationLocations: [],
  publicationSettings: [],
  organizationById: new Map(),
  personById: new Map(),
  workById: new Map(),
  materialById: new Map(),
  componentsByProjectId: new Map(),
  aliasesByProjectId: new Map(),
  publicationByProjectId: new Map(),
  filteredProjects: [],
  map: null,
  projectLayer: null,
  componentLayer: null,
  supplementalLayer: null,
  markerByProjectId: new Map(),
  displayPositionByKey: new Map(),
  activeProjectId: null,
  activeTab: "overview",
  activeWorkFilter: "",
};

const elements = {
  appHeader: document.getElementById("app-header"),
  workspace: document.getElementById("workspace"),
  siteTitle: document.getElementById("site-title"),
  siteSubtitle: document.getElementById("site-subtitle"),
  versionBadge: document.getElementById("version-badge"),
  visibleCount: document.getElementById("visible-count"),
  publicCount: document.getElementById("public-count"),
  updatedDate: document.getElementById("updated-date"),
  listCount: document.getElementById("list-count"),
  search: document.getElementById("search-input"),
  status: document.getElementById("status-filter"),
  sector: document.getElementById("sector-filter"),
  function: document.getElementById("function-filter"),
  company: document.getElementById("company-filter"),
  reset: document.getElementById("reset-button"),
  download: document.getElementById("download-button"),
  filterToggle: document.getElementById("filter-toggle"),
  listToggle: document.getElementById("list-toggle"),
  mapListButton: document.getElementById("map-list-button"),
  projectPane: document.getElementById("project-pane"),
  list: document.getElementById("project-list"),
  legend: document.getElementById("status-legend"),
  functionLegend: document.getElementById("function-legend"),
  notice: document.getElementById("public-notice"),
  message: document.getElementById("map-message"),
  layerProjects: document.getElementById("layer-projects"),
  layerOpportunities: document.getElementById("layer-opportunities"),
  layerLocations: document.getElementById("layer-locations"),
  detailPanel: document.getElementById("detail-panel"),
  detailClose: document.getElementById("detail-close"),
  detailCode: document.getElementById("detail-code"),
  detailTitle: document.getElementById("detail-title"),
  detailSubtitle: document.getElementById("detail-subtitle"),
  worksTabCount: document.getElementById("works-tab-count"),
  materialsTabCount: document.getElementById("materials-tab-count"),
  overviewPanel: document.getElementById("panel-overview"),
  worksPanel: document.getElementById("panel-works"),
  materialsPanel: document.getElementById("panel-materials"),
  tabs: [...document.querySelectorAll(".detail-tab")],
};

const FALLBACK_FUNCTION_STYLES = {
  RESIDENTIAL: { label: "Residential", shape: "square", symbol: "⌂" },
  COMMERCIAL: { label: "Commercial", shape: "diamond", symbol: "▦" },
  SPORTS: { label: "Sports", shape: "circle", symbol: "●" },
  LANDSCAPING: { label: "Landscaping", shape: "circle", symbol: "✦" },
  DRAINAGE: { label: "Drainage", shape: "triangle", symbol: "↓" },
  ROAD_DRAINAGE: { label: "Road and Drainage", shape: "hexagon", symbol: "⇄" },
  ROAD: { label: "Road", shape: "pill", symbol: "↔" },
  PUBLIC_BUILDING: { label: "Public Building", shape: "square", symbol: "▣" },
  RELIGIOUS: { label: "Religious", shape: "triangle", symbol: "△" },
  PAVING: { label: "Paving", shape: "diamond", symbol: "▦" },
  AIRPORT: { label: "Airport", shape: "hexagon", symbol: "✈" },
  PUBLIC_SANITATION: { label: "Public Sanitation", shape: "circle", symbol: "+" },
  RIVER_PROTECTION: { label: "River Protection", shape: "hexagon", symbol: "≋" },
  PARK: { label: "Park", shape: "circle", symbol: "♣" },
  OTHER: { label: "Other", shape: "circle", symbol: "•" },
};

function escapeHTML(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showMessage(message, type = "error") {
  elements.message.textContent = message;
  elements.message.className = `map-message ${type}`;
}

function clearMessage() {
  elements.message.textContent = "";
  elements.message.className = "map-message";
}

function prettyDate(value) {
  if (!value) return "";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

function humanLabel(value) {
  if (!value) return "";
  return state.config?.human_labels?.[value] || String(value)
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function directionsURL(item) {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(
    `${item.latitude},${item.longitude}`
  )}`;
}

async function loadCSV(path, cacheBust) {
  const response = await fetch(`${path}?${cacheBust}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`);
  return parseCSV(await response.text());
}

function required(raw, field, rowNumber, fileName) {
  const value = String(raw[field] ?? "").trim();
  if (!value) throw new Error(`${fileName} row ${rowNumber}: ${field} is blank`);
  return value;
}

function validCoordinate(raw, field, rowNumber, fileName, min, max) {
  const value = Number(required(raw, field, rowNumber, fileName));
  if (!Number.isFinite(value) || value < min || value > max) {
    throw new Error(`${fileName} row ${rowNumber}: invalid ${field}`);
  }
  return value;
}

function normalizeProject(raw, index) {
  const rowNumber = index + 2;
  const status = required(raw, "status", rowNumber, "projects.csv");
  if (!state.config.status_styles[status]) {
    throw new Error(`projects.csv row ${rowNumber}: unknown status "${status}"`);
  }
  return {
    ...raw,
    project_id: required(raw, "project_id", rowNumber, "projects.csv"),
    company_project_code: required(raw, "company_project_code", rowNumber, "projects.csv"),
    legacy_project_code: String(raw.legacy_project_code ?? "").trim(),
    project_name: required(raw, "project_name", rowNumber, "projects.csv"),
    display_name: raw.display_name || raw.project_name.replaceAll("_", " "),
    project_sector: required(raw, "project_sector", rowNumber, "projects.csv"),
    project_category: required(raw, "project_category", rowNumber, "projects.csv"),
    project_function: required(raw, "project_function", rowNumber, "projects.csv"),
    executing_company_id: required(raw, "executing_company_id", rowNumber, "projects.csv"),
    latitude: validCoordinate(raw, "latitude", rowNumber, "projects.csv", -90, 90),
    longitude: validCoordinate(raw, "longitude", rowNumber, "projects.csv", -180, 180),
    status,
    location_ward_number: String(raw.location_ward_number ?? "").trim(),
    physical_progress_percent: parseOptionalNumber(raw.physical_progress_percent),
    financial_progress_percent: parseOptionalNumber(raw.financial_progress_percent),
    is_public: parseBoolean(raw.is_public),
  };
}

function normalizeWorkItem(raw) {
  return {
    ...raw,
    planned_quantity: parseOptionalNumber(raw.planned_quantity),
    completed_quantity: parseOptionalNumber(raw.completed_quantity),
    remaining_quantity: parseOptionalNumber(raw.remaining_quantity),
    rate_npr: parseOptionalNumber(raw.rate_npr),
    amount_npr: parseOptionalNumber(raw.amount_npr),
    factor: parseOptionalNumber(raw.factor),
    progress_percent: parseOptionalNumber(raw.progress_percent),
    is_public: parseBoolean(raw.is_public),
  };
}

function normalizeInventory(raw) {
  return {
    ...raw,
    quantity_on_site: parseOptionalNumber(raw.quantity_on_site),
    reserved_quantity: parseOptionalNumber(raw.reserved_quantity),
    available_quantity: parseOptionalNumber(raw.available_quantity),
    is_public: parseBoolean(raw.is_public),
  };
}

function normalizeComponent(raw) {
  return {
    ...raw,
    sequence_no: parseOptionalNumber(raw.sequence_no),
    latitude: parseOptionalNumber(raw.latitude),
    longitude: parseOptionalNumber(raw.longitude),
    is_public: parseBoolean(raw.is_public),
  };
}

function normalizeOpportunity(raw) {
  return {
    ...raw,
    latitude: parseOptionalNumber(raw.latitude),
    longitude: parseOptionalNumber(raw.longitude),
    is_public: parseBoolean(raw.is_public),
  };
}

function normalizeOrganizationLocation(raw) {
  return {
    ...raw,
    latitude: parseOptionalNumber(raw.latitude),
    longitude: parseOptionalNumber(raw.longitude),
    is_public: parseBoolean(raw.is_public),
  };
}

function normalizePublicationSetting(raw) {
  const booleanFields = [
    "show_project_name", "show_coordinates", "show_status", "show_ward_number",
    "show_project_sector", "show_implementation_method", "show_legal_contractor",
    "show_executing_company_role", "show_general_work_summary",
  ];
  const normalized = { ...raw };
  booleanFields.forEach((field) => { normalized[field] = parseBoolean(raw[field], true); });
  return normalized;
}

function groupBy(rows, field) {
  const output = new Map();
  rows.forEach((row) => {
    const key = row[field];
    if (!output.has(key)) output.set(key, []);
    output.get(key).push(row);
  });
  return output;
}

function buildIndexes() {
  state.organizationById = new Map(state.organizations.map((row) => [row.organization_id, row]));
  state.personById = new Map(state.people.map((row) => [row.person_id, row]));
  state.workById = new Map(state.workCatalog.map((row) => [row.work_id, row]));
  state.materialById = new Map(state.materialsMaster.map((row) => [row.material_id, row]));
  state.componentsByProjectId = groupBy(state.projectComponents, "project_id");
  state.aliasesByProjectId = groupBy(state.projectSourceLinks, "project_id");
  state.publicationByProjectId = new Map(
    state.publicationSettings.map((row) => [row.project_id, row])
  );
}

function companyName(project) {
  return state.organizationById.get(project.executing_company_id)?.organization_name || "Company not entered";
}

function publication(project) {
  return state.publicationByProjectId.get(project.project_id) || {};
}

function canShow(project, field, fallback = true) {
  const value = publication(project)[field];
  return typeof value === "boolean" ? value : fallback;
}

function functionStyle(projectFunction) {
  return state.config.function_styles?.[projectFunction] || FALLBACK_FUNCTION_STYLES[projectFunction] || FALLBACK_FUNCTION_STYLES.OTHER;
}

function appendOptions(select, values, labeler = humanLabel) {
  [...values].sort((a, b) => labeler(a).localeCompare(labeler(b))).forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labeler(value);
    select.append(option);
  });
}

function fillFilters() {
  appendOptions(elements.status, new Set(state.projects.map((p) => p.status)), (value) => state.config.status_styles[value]?.label || value);
  appendOptions(elements.sector, new Set(state.projects.map((p) => p.project_sector)));
  appendOptions(elements.function, new Set(state.projects.map((p) => p.project_function)));
  const companies = new Map(state.projects.map((p) => [p.executing_company_id, companyName(p)]));
  [...companies.entries()].sort((a, b) => a[1].localeCompare(b[1])).forEach(([id, name]) => {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = name;
    elements.company.append(option);
  });
}

function renderLegend() {
  elements.legend.replaceChildren();
  Object.entries(state.config.status_styles)
    .sort(([, a], [, b]) => a.order - b.order)
    .forEach(([status, style]) => {
      if (!state.projects.some((p) => p.status === status)) return;
      const chip = document.createElement("span");
      chip.className = "status-chip";
      chip.innerHTML = `<span class="status-dot" style="background:${escapeHTML(style.color)}"></span>${escapeHTML(style.label)}`;
      elements.legend.append(chip);
    });

  elements.functionLegend.replaceChildren();
  [...new Set(state.projects.map((p) => p.project_function))]
    .sort((a, b) => humanLabel(a).localeCompare(humanLabel(b)))
    .forEach((projectFunction) => {
      const style = functionStyle(projectFunction);
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "function-chip";
      chip.dataset.function = projectFunction;
      chip.innerHTML = `<span class="mini-marker marker-shape-${escapeHTML(style.shape)}"><span>${escapeHTML(style.symbol)}</span></span>${escapeHTML(style.label || humanLabel(projectFunction))}`;
      chip.addEventListener("click", () => {
        elements.function.value = elements.function.value === projectFunction ? "" : projectFunction;
        applyFilters();
      });
      elements.functionLegend.append(chip);
    });
}

function projectAliases(projectId) {
  return (state.aliasesByProjectId.get(projectId) || []).map((row) => row.source_alias).filter(Boolean);
}

function projectMatchesFilters(project) {
  const query = elements.search.value.trim().toLowerCase();
  const parties = state.projectParties.filter((p) => p.project_id === project.project_id).map((p) => p.party_id).join(" ");
  const components = (state.componentsByProjectId.get(project.project_id) || []).map((c) => c.component_name).join(" ");
  const searchable = [
    project.project_id, project.company_project_code, project.legacy_project_code,
    project.project_name, project.display_name, project.status, project.project_sector,
    project.project_category, project.project_function, project.implementation_mechanism,
    project.location_ward_number ? `ward ${project.location_ward_number}` : "",
    companyName(project), project.latest_update, project.public_notes, parties,
    projectAliases(project.project_id).join(" "), components,
  ].join(" ").toLowerCase();

  return (!query || searchable.includes(query))
    && (!elements.status.value || project.status === elements.status.value)
    && (!elements.sector.value || project.project_sector === elements.sector.value)
    && (!elements.function.value || project.project_function === elements.function.value)
    && (!elements.company.value || project.executing_company_id === elements.company.value);
}

function qualityBadge(project) {
  if (project.data_quality_status !== "WARNING" && project.contractor_verification_status !== "UNVERIFIED") return "";
  return `<span class="quality-flag" title="This record contains provisional or unverified information">Review</span>`;
}

function renderProjectList() {
  elements.list.replaceChildren();
  elements.listCount.textContent = `${state.filteredProjects.length} shown`;
  if (!state.filteredProjects.length) {
    elements.list.innerHTML = `<div class="empty-state"><strong>No matching projects</strong>Change or reset the filters.</div>`;
    return;
  }

  state.filteredProjects.forEach((project) => {
    const style = state.config.status_styles[project.status];
    const item = document.createElement("button");
    item.type = "button";
    item.className = `project-item${state.activeProjectId === project.project_id ? " active" : ""}`;
    item.setAttribute("aria-current", state.activeProjectId === project.project_id ? "true" : "false");
    const progress = project.physical_progress_percent === null ? "" : ` · ${project.physical_progress_percent}% physical`;
    const ward = project.location_ward_number ? `Ward ${project.location_ward_number} · ` : "";
    item.innerHTML = `
      <div class="project-item-head">
        <div>
          <div class="project-code">${escapeHTML(project.company_project_code)} ${qualityBadge(project)}</div>
          <div class="project-name">${escapeHTML(project.display_name)}</div>
        </div>
        <span class="badge"><span class="status-dot" style="background:${escapeHTML(style.color)}"></span>${escapeHTML(style.label)}</span>
      </div>
      <div class="project-meta">${escapeHTML(ward + humanLabel(project.project_function))}</div>
      <div class="project-meta">${escapeHTML(companyName(project) + progress)}</div>`;
    item.addEventListener("click", () => selectProject(project.project_id));
    elements.list.append(item);
  });
}

function projectMarkerIcon(project) {
  const statusStyle = state.config.status_styles[project.status];
  const style = functionStyle(project.project_function);
  return L.divIcon({
    className: "jp-div-icon",
    html: `<div class="function-marker marker-shape-${escapeHTML(style.shape)}" style="--marker-color:${escapeHTML(statusStyle.color)}" title="${escapeHTML(style.label)}"><span>${escapeHTML(style.symbol)}</span></div>`,
    iconSize: [30, 30], iconAnchor: [15, 15], popupAnchor: [0, -16], tooltipAnchor: [0, -16],
  });
}

function projectPopupHTML(project) {
  const ward = project.location_ward_number ? `Ward ${escapeHTML(project.location_ward_number)} · ` : "";
  return `<div class="popup">
    <div class="popup-code">${escapeHTML(project.company_project_code)}</div>
    <h3>${escapeHTML(project.display_name)}</h3>
    <div class="popup-status">${ward}${escapeHTML(humanLabel(project.project_function))} · ${escapeHTML(project.status)}</div>
    <div class="popup-actions">
      <button type="button" data-view-project="${escapeHTML(project.project_id)}">View Project</button>
      ${canShow(project, "show_coordinates") ? `<a href="${directionsURL(project)}" target="_blank" rel="noopener">Directions</a>` : ""}
    </div></div>`;
}

function pointKey(latitude, longitude) {
  return `${Number(latitude).toFixed(7)},${Number(longitude).toFixed(7)}`;
}

function offsetCoordinate(latitude, longitude, index, count, radiusMeters) {
  if (count <= 1) return [latitude, longitude];
  const angle = (-Math.PI / 2) + (2 * Math.PI * index) / count;
  const radius = radiusMeters * (count > 4 ? 1.25 : 1);
  const latOffset = (radius * Math.sin(angle)) / 111320;
  const lonScale = Math.max(0.2, Math.cos(latitude * Math.PI / 180));
  const lonOffset = (radius * Math.cos(angle)) / (111320 * lonScale);
  return [latitude + latOffset, longitude + lonOffset];
}

function prepareDisplayPositions() {
  const points = [];
  if (elements.layerProjects.checked) {
    state.filteredProjects.forEach((p) => points.push({ key: `project:${p.project_id}`, latitude: p.latitude, longitude: p.longitude }));
  }
  if (elements.layerOpportunities.checked) {
    state.projectOpportunities.filter((o) => o.is_public && o.latitude !== null && o.longitude !== null)
      .forEach((o) => points.push({ key: `opportunity:${o.opportunity_id}`, latitude: o.latitude, longitude: o.longitude }));
  }
  if (elements.layerLocations.checked) {
    state.organizationLocations.filter((o) => o.is_public && o.latitude !== null && o.longitude !== null)
      .forEach((o) => points.push({ key: `location:${o.organization_location_id}`, latitude: o.latitude, longitude: o.longitude }));
  }
  const groups = new Map();
  points.forEach((point) => {
    const groupKey = pointKey(point.latitude, point.longitude);
    if (!groups.has(groupKey)) groups.set(groupKey, []);
    groups.get(groupKey).push(point);
  });
  state.displayPositionByKey.clear();
  const radius = state.config.marker.overlap_spread_meters || 12;
  groups.forEach((group) => group.forEach((point, index) => {
    state.displayPositionByKey.set(point.key, offsetCoordinate(point.latitude, point.longitude, index, group.length, radius));
  }));
}

function supplementalPopup(title, rows, warning, directions) {
  return `<div class="popup supplemental-popup"><h3>${escapeHTML(title)}</h3>
    ${rows.map(([label, value]) => value ? `<div class="popup-row"><strong>${escapeHTML(label)}:</strong> ${escapeHTML(value)}</div>` : "").join("")}
    ${warning ? `<div class="popup-warning">${escapeHTML(warning)}</div>` : ""}
    ${directions ? `<div class="popup-actions"><a href="${directions}" target="_blank" rel="noopener">Directions</a></div>` : ""}
  </div>`;
}

function renderSupplementalMarkers(bounds) {
  state.supplementalLayer.clearLayers();
  if (elements.layerOpportunities.checked) {
    state.projectOpportunities.filter((row) => row.is_public && row.latitude !== null && row.longitude !== null).forEach((row) => {
      const position = state.displayPositionByKey.get(`opportunity:${row.opportunity_id}`) || [row.latitude, row.longitude];
      const marker = L.marker(position, {
        icon: L.divIcon({ className: "jp-div-icon", html: `<div class="supplemental-marker opportunity-marker"><span>?</span></div>`, iconSize: [30, 30], iconAnchor: [15, 15] }),
      }).bindPopup(supplementalPopup(row.opportunity_name, [
        ["Type", "Opportunity"], ["Status", humanLabel(row.status)], ["Ward", row.location_ward_number],
      ], row.data_quality_issue, directionsURL(row))).addTo(state.supplementalLayer);
      bounds.push(position);
    });
  }
  if (elements.layerLocations.checked) {
    state.organizationLocations.filter((row) => row.is_public && row.latitude !== null && row.longitude !== null).forEach((row) => {
      const organization = state.organizationById.get(row.organization_id);
      const position = state.displayPositionByKey.get(`location:${row.organization_location_id}`) || [row.latitude, row.longitude];
      L.marker(position, {
        icon: L.divIcon({ className: "jp-div-icon", html: `<div class="supplemental-marker office-marker"><span>O</span></div>`, iconSize: [30, 30], iconAnchor: [15, 15] }),
      }).bindPopup(supplementalPopup(row.location_name, [
        ["Organization", organization?.organization_name || ""], ["Type", humanLabel(row.location_type)], ["Ward", row.location_ward_number],
      ], row.data_quality_issue, directionsURL(row))).addTo(state.supplementalLayer);
      bounds.push(position);
    });
  }
}

function updateProjectTooltips() {
  const show = state.map && state.map.getZoom() >= (state.config.marker.label_min_zoom || 14);
  state.markerByProjectId.forEach((marker) => show ? marker.openTooltip() : marker.closeTooltip());
}

function renderMapMarkers({ fitBounds = false } = {}) {
  state.projectLayer.clearLayers();
  state.componentLayer.clearLayers();
  state.supplementalLayer.clearLayers();
  state.markerByProjectId.clear();
  prepareDisplayPositions();
  const bounds = [];

  if (elements.layerProjects.checked) {
    state.filteredProjects.forEach((project) => {
      const position = state.displayPositionByKey.get(`project:${project.project_id}`) || [project.latitude, project.longitude];
      const marker = L.marker(position, { icon: projectMarkerIcon(project), keyboard: true })
        .bindTooltip(project.company_project_code, { permanent: false, direction: "top", opacity: 0.95 })
        .bindPopup(projectPopupHTML(project), { minWidth: 240, maxWidth: 310 })
        .addTo(state.projectLayer);
      marker.on("click", () => selectProject(project.project_id, { pan: false, openPopup: false }));
      state.markerByProjectId.set(project.project_id, marker);
      bounds.push(position);
    });
  }
  renderSupplementalMarkers(bounds);
  if (state.activeProjectId) renderSelectedComponents(state.activeProjectId);
  if (fitBounds && bounds.length) {
    state.map.invalidateSize({ pan: false });
    state.map.fitBounds(bounds, { padding: [state.config.fit_bounds_padding, state.config.fit_bounds_padding], maxZoom: 15 });
  }
  window.setTimeout(updateProjectTooltips, 50);
}

function roleRows(project) {
  const settings = publication(project);
  return state.projectParties
    .filter((party) => party.project_id === project.project_id && parseBoolean(party.is_public))
    .filter((party) => party.role !== "CONTRACTOR" || settings.show_legal_contractor !== false)
    .map((party) => {
      let name = "";
      if (party.party_entity_type === "ORGANIZATION") name = state.organizationById.get(party.party_id)?.organization_name || "";
      if (party.party_entity_type === "PERSON") name = state.personById.get(party.party_id)?.display_name || "";
      const suffix = party.data_quality_status === "WARNING" ? " — provisional" : "";
      return [humanLabel(party.role), name ? `${name}${suffix}` : ""];
    }).filter(([, value]) => value);
}

function fundingRows(project) {
  return state.projectFunding
    .filter((row) => row.project_id === project.project_id && parseBoolean(row.is_public))
    .map((row) => {
      const funder = state.organizationById.get(row.funding_party_id)?.organization_name || "";
      return ["Funding source", [funder, humanLabel(row.funding_type) ? `(${humanLabel(row.funding_type)})` : ""].filter(Boolean).join(" ")];
    }).filter(([, value]) => value);
}

function detailGrid(rows) {
  const visible = rows.filter(([, value]) => value !== null && value !== undefined && value !== "");
  if (!visible.length) return "";
  return `<dl class="detail-grid">${visible.map(([label, value]) => `<dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value)}</dd>`).join("")}</dl>`;
}

function progressBlock(label, value) {
  if (value === null || value === undefined) return "";
  const safeValue = Math.min(100, Math.max(0, Number(value)));
  return `<div class="progress-block"><div class="progress-head"><span>${escapeHTML(label)}</span><strong>${escapeHTML(safeValue)}%</strong></div>
    <div class="progress-track" role="progressbar" aria-label="${escapeHTML(label)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${escapeHTML(safeValue)}"><div class="progress-fill" style="width:${safeValue}%"></div></div></div>`;
}

function componentCard(project) {
  if (!canShow(project, "show_general_work_summary")) return "";
  const components = (state.componentsByProjectId.get(project.project_id) || []).filter((c) => c.is_public);
  if (!components.length) return "";
  return `<div class="section-card"><h3>Project components</h3><div class="component-list">${components
    .sort((a, b) => (a.sequence_no || 0) - (b.sequence_no || 0))
    .map((component) => `<div class="component-row"><span class="component-sequence">${escapeHTML(component.sequence_no || "•")}</span><div><strong>${escapeHTML(component.component_name)}</strong><small>${escapeHTML(humanLabel(component.component_type))}${component.status ? ` · ${escapeHTML(component.status)}` : ""}</small></div></div>`).join("")}</div></div>`;
}

function renderOverview(project) {
  const aliases = projectAliases(project.project_id);
  const identifiers = detailGrid([
    ["Global project ID", project.project_id],
    ["Company project code", project.company_project_code],
    ["Legacy code", project.legacy_project_code],
    ["Source aliases", aliases.join(", ")],
  ]);
  const classifications = detailGrid([
    ["Company", canShow(project, "show_executing_company_role") ? companyName(project) : ""],
    ["Ward", canShow(project, "show_ward_number") && project.location_ward_number ? `Ward ${project.location_ward_number}` : ""],
    ["Project sector", canShow(project, "show_project_sector") ? humanLabel(project.project_sector) : ""],
    ["Category", humanLabel(project.project_category)],
    ["Function", humanLabel(project.project_function)],
    ["Government level", humanLabel(project.government_level)],
    ["Implementation", canShow(project, "show_implementation_method") ? humanLabel(project.implementation_mechanism) : ""],
    ["Status", canShow(project, "show_status") ? project.status : ""],
  ]);
  const dates = detailGrid([
    ["Start date", prettyDate(project.start_date)], ["Target completion", prettyDate(project.target_completion_date)],
    ["Actual completion", prettyDate(project.actual_completion_date)], ["Last updated", prettyDate(project.last_updated)],
  ]);
  const coordinates = canShow(project, "show_coordinates") ? `${project.latitude.toFixed(7)}, ${project.longitude.toFixed(7)}` : "";
  const updates = detailGrid([["Latest update", project.latest_update], ["Public notes", project.public_notes], ["Coordinates", coordinates]]);
  const relationships = detailGrid([...roleRows(project), ...fundingRows(project)]);
  const quality = detailGrid([
    ["Data quality", humanLabel(project.data_quality_status)],
    ["Contractor verification", humanLabel(project.contractor_verification_status)],
    ["Record verification", humanLabel(project.verification_status)],
    ["Source group", project.source_group_ids],
  ]);
  const physicalProgress = progressBlock("Physical Progress", project.physical_progress_percent);
  const financialProgress = state.config.features.show_financial_progress ? progressBlock("Financial Progress", project.financial_progress_percent) : "";
  const projectDetailsLink = project.details_url ? `<a class="detail-link" href="${escapeHTML(project.details_url)}" target="_blank" rel="noopener">Project details</a>` : "";
  const directionsLink = canShow(project, "show_coordinates") ? `<a class="detail-link primary" href="${directionsURL(project)}" target="_blank" rel="noopener">Directions</a>` : "";

  elements.overviewPanel.innerHTML = `
    ${(physicalProgress || financialProgress) ? `<div class="section-card"><h3>Progress</h3>${physicalProgress}${financialProgress}</div>` : ""}
    <div class="section-card"><h3>Project identity</h3>${identifiers}</div>
    <div class="section-card"><h3>Classification</h3>${classifications}</div>
    ${relationships ? `<div class="section-card"><h3>Project parties and funding</h3>${relationships}</div>` : ""}
    ${componentCard(project)}
    ${dates ? `<div class="section-card"><h3>Dates</h3>${dates}</div>` : ""}
    ${updates ? `<div class="section-card"><h3>Public information</h3>${updates}</div>` : ""}
    ${(project.data_quality_status === "WARNING" || project.contractor_verification_status === "UNVERIFIED") ? `<div class="section-card quality-card"><h3>Verification status</h3>${quality}<p>Provisional information is shown transparently and should be replaced when verified records become available.</p></div>` : ""}
    ${(directionsLink || projectDetailsLink) ? `<div class="section-card"><h3>Open</h3><div class="detail-actions">${directionsLink}${projectDetailsLink}</div></div>` : ""}`;
}

function projectWorkItems(projectId) {
  return state.projectWorkItems.filter((item) => item.project_id === projectId && item.is_public);
}

function projectMaterials(projectId) {
  return state.projectMaterialInventory.filter((item) => item.project_id === projectId && item.is_public);
}

function quantityText(value, unit) {
  if (value === null || value === undefined) return "";
  return `${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 3 }).format(value)}${unit ? ` ${unit}` : ""}`;
}

function renderWorks(project) {
  const items = projectWorkItems(project.project_id);
  const components = (state.componentsByProjectId.get(project.project_id) || []).filter((c) => c.is_public);
  elements.worksTabCount.textContent = String(items.length + components.length);
  if (!items.length) {
    elements.worksPanel.innerHTML = `${components.length ? componentCard(project) : ""}<div class="empty-state"><strong>No detailed work items published</strong>${components.length ? "Project components are shown above. Detailed BOQ work items have not yet been linked." : "The normalized work structure is ready, but no verified public work item is linked to this project."}</div>`;
    return;
  }

  const statuses = state.config.controlled_values.work_statuses;
  const counts = Object.fromEntries(statuses.map((status) => [status, items.filter((item) => item.work_status === status).length]));
  const filters = [["", `All ${items.length}`], ...statuses.filter((status) => counts[status]).map((status) => [status, `${humanLabel(status)} ${counts[status]}`])];
  const filtered = state.activeWorkFilter ? items.filter((item) => item.work_status === state.activeWorkFilter) : items;
  elements.worksPanel.innerHTML = `${components.length ? componentCard(project) : ""}
    <div class="summary-row"><div class="summary-box"><strong>${counts.COMPLETED || 0}</strong><span>completed</span></div><div class="summary-box"><strong>${counts.IN_PROGRESS || 0}</strong><span>in progress</span></div><div class="summary-box"><strong>${(counts.NOT_STARTED || 0) + (counts.BLOCKED || 0) + (counts.ON_HOLD || 0)}</strong><span>remaining</span></div></div>
    <div class="work-filters">${filters.map(([value, label]) => `<button class="work-filter${state.activeWorkFilter === value ? " active" : ""}" type="button" data-work-filter="${escapeHTML(value)}">${escapeHTML(label)}</button>`).join("")}</div>
    ${filtered.map((item) => {
      const catalog = state.workById.get(item.work_id);
      const description = item.description_override || catalog?.description || "Work description not entered";
      const quantities = [
        item.planned_quantity !== null ? `Planned: ${quantityText(item.planned_quantity, item.unit)}` : "",
        item.completed_quantity !== null ? `Completed: ${quantityText(item.completed_quantity, item.unit)}` : "",
        item.remaining_quantity !== null ? `Remaining: ${quantityText(item.remaining_quantity, item.unit)}` : "",
      ].filter(Boolean).join(" · ");
      return `<article class="work-card"><div class="work-title-row"><div class="work-title">${escapeHTML(description)}</div><span class="badge">${escapeHTML(humanLabel(item.work_status))}</span></div>${quantities ? `<div class="work-meta">${escapeHTML(quantities)}</div>` : ""}${progressBlock("Work progress", item.progress_percent)}${item.remarks ? `<div class="work-remarks">${escapeHTML(item.remarks)}</div>` : ""}</article>`;
    }).join("")}`;
  elements.worksPanel.querySelectorAll("[data-work-filter]").forEach((button) => button.addEventListener("click", () => {
    state.activeWorkFilter = button.dataset.workFilter;
    renderWorks(project);
  }));
}

function materialQuantitiesAllowed(project) {
  const visibility = publication(project).material_quantities_visibility || "PRIVATE";
  return state.config.features.show_inventory_quantities === true && visibility === "PUBLIC";
}

function renderMaterials(project) {
  const items = projectMaterials(project.project_id);
  if (!materialQuantitiesAllowed(project)) {
    elements.materialsTabCount.textContent = "—";
    elements.materialsPanel.innerHTML = `<div class="empty-state"><strong>Public material quantities are not enabled</strong>The data model supports inventory, but exact stock remains private until this project is explicitly set to PUBLIC.</div>`;
    return;
  }
  elements.materialsTabCount.textContent = String(items.length);
  if (!items.length) {
    elements.materialsPanel.innerHTML = `<div class="empty-state"><strong>No approved public inventory snapshot</strong>No material quantity has been invented or inferred for this project.</div>`;
    return;
  }
  const dates = items.map((item) => item.as_of_date).filter(Boolean).sort();
  elements.materialsPanel.innerHTML = `<div class="section-card"><h3>Inventory summary</h3>${detailGrid([["Materials recorded", String(items.length)], ["Latest inventory date", dates.length ? prettyDate(dates.at(-1)) : "Not entered"]])}</div>
    ${items.map((item) => {
      const material = state.materialById.get(item.material_id);
      const quantities = [item.quantity_on_site !== null ? `On site: ${quantityText(item.quantity_on_site, item.unit)}` : "", item.available_quantity !== null ? `Available: ${quantityText(item.available_quantity, item.unit)}` : ""].filter(Boolean).join(" · ");
      return `<article class="material-card"><div class="material-title-row"><div class="material-title">${escapeHTML(material?.material_name || "Material not found")}</div>${item.condition ? `<span class="badge">${escapeHTML(humanLabel(item.condition))}</span>` : ""}</div>${quantities ? `<div class="material-meta">${escapeHTML(quantities)}</div>` : ""}${item.storage_location ? `<div class="material-meta">Storage: ${escapeHTML(item.storage_location)}</div>` : ""}${item.remarks ? `<div class="material-remarks">${escapeHTML(item.remarks)}</div>` : ""}</article>`;
    }).join("")}`;
}

function setActiveTab(tabName) {
  state.activeTab = tabName;
  const panels = { overview: elements.overviewPanel, works: elements.worksPanel, materials: elements.materialsPanel };
  elements.tabs.forEach((tab) => {
    const active = tab.dataset.tab === tabName;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  Object.entries(panels).forEach(([name, panel]) => {
    panel.hidden = name !== tabName;
    panel.classList.toggle("active", name === tabName);
  });
}

function renderSelectedComponents(projectId) {
  state.componentLayer.clearLayers();
  if (!elements.layerProjects.checked || state.config.features.show_project_components === false) return;
  const components = (state.componentsByProjectId.get(projectId) || []).filter((c) => c.is_public && c.latitude !== null && c.longitude !== null);
  const positions = components.map((component, index) => offsetCoordinate(component.latitude, component.longitude, index, components.length, 7));
  components.forEach((component, index) => {
    L.circleMarker(positions[index], { radius: 6, color: "#172033", weight: 2, fillColor: "#ffffff", fillOpacity: 0.95, dashArray: "3 2" })
      .bindTooltip(component.component_name, { direction: "top" })
      .bindPopup(`<div class="popup"><div class="popup-code">${escapeHTML(humanLabel(component.component_type))}</div><h3>${escapeHTML(component.component_name)}</h3><div class="popup-status">${escapeHTML(component.status || "")}</div></div>`)
      .addTo(state.componentLayer);
  });
}

function renderProjectDetail(project) {
  const works = projectWorkItems(project.project_id);
  const components = (state.componentsByProjectId.get(project.project_id) || []).filter((c) => c.is_public);
  const materials = projectMaterials(project.project_id);
  elements.detailCode.textContent = project.company_project_code;
  elements.detailTitle.textContent = canShow(project, "show_project_name") ? project.display_name : project.company_project_code;
  elements.detailSubtitle.textContent = [project.project_id, project.legacy_project_code ? `legacy ${project.legacy_project_code}` : "new normalized record"].join(" · ");
  elements.worksTabCount.textContent = String(works.length + components.length);
  elements.materialsTabCount.textContent = materialQuantitiesAllowed(project) ? String(materials.length) : "—";
  state.activeWorkFilter = "";
  renderOverview(project);
  renderWorks(project);
  renderMaterials(project);
  renderSelectedComponents(project.project_id);
  setActiveTab(state.activeTab);
}

function updateHash(projectId) {
  const nextHash = projectId ? `#project=${encodeURIComponent(projectId)}` : "";
  if (window.location.hash !== nextHash) window.history.replaceState(null, "", nextHash || window.location.pathname);
}

function selectProject(projectId, { pan = true, openPopup = true, updateLocation = true } = {}) {
  const project = state.projects.find((candidate) => candidate.project_id === projectId);
  if (!project) return;
  state.activeProjectId = projectId;
  state.activeTab = "overview";
  elements.workspace.classList.add("detail-open");
  elements.detailPanel.inert = false;
  renderProjectList();
  renderProjectDetail(project);
  const marker = state.markerByProjectId.get(projectId);
  if (pan) {
    const position = marker?.getLatLng() || L.latLng(project.latitude, project.longitude);
    state.map.setView(position, Math.max(state.map.getZoom(), 15), { animate: true });
  }
  if (openPopup && marker) marker.openPopup();
  if (updateLocation) updateHash(projectId);
  refreshMapSoon();
}

function closeProjectDetail() {
  elements.workspace.classList.remove("detail-open");
  elements.detailPanel.inert = true;
  state.componentLayer?.clearLayers();
  updateHash("");
  refreshMapSoon();
}

function applyFilters({ fitBounds = true } = {}) {
  state.filteredProjects = state.projects.filter(projectMatchesFilters);
  if (state.activeProjectId && !state.filteredProjects.some((p) => p.project_id === state.activeProjectId)) {
    state.activeProjectId = null;
    closeProjectDetail();
  }
  renderProjectList();
  renderMapMarkers({ fitBounds });
  renderMetrics();
  elements.functionLegend.querySelectorAll(".function-chip").forEach((chip) => chip.classList.toggle("active", chip.dataset.function === elements.function.value));
}

function renderMetrics() {
  elements.visibleCount.textContent = String(state.filteredProjects.length);
  elements.publicCount.textContent = String(state.projects.length);
  const dates = state.projects.map((p) => p.last_updated).filter(Boolean).sort();
  elements.updatedDate.textContent = dates.length ? prettyDate(dates.at(-1)) : "—";
}

function downloadGeoJSON() {
  const includeFinancial = state.config.features.show_financial_progress === true;
  const featureCollection = {
    type: "FeatureCollection",
    name: "jp_ecosystem_public_projects",
    generated_from_app_version: state.config.app_version,
    data_schema_version: state.config.data_schema_version,
    features: state.filteredProjects.map((project) => {
      const settings = publication(project);
      const properties = {
        project_id: project.project_id,
        company_project_code: project.company_project_code,
        legacy_project_code: project.legacy_project_code || null,
        project_name: settings.show_project_name === false ? null : project.project_name,
        display_name: settings.show_project_name === false ? null : project.display_name,
        location_ward_number: settings.show_ward_number === false ? null : project.location_ward_number,
        project_sector: settings.show_project_sector === false ? null : project.project_sector,
        project_category: project.project_category,
        project_function: project.project_function,
        implementation_mechanism: settings.show_implementation_method === false ? null : project.implementation_mechanism,
        executing_company: settings.show_executing_company_role === false ? null : companyName(project),
        status: settings.show_status === false ? null : project.status,
        physical_progress_percent: project.physical_progress_percent,
        last_updated: project.last_updated,
        latest_update: project.latest_update,
        public_notes: project.public_notes,
      };
      if (includeFinancial) properties.financial_progress_percent = project.financial_progress_percent;
      return {
        type: "Feature", id: project.project_id,
        geometry: settings.show_coordinates === false ? null : { type: "Point", coordinates: [project.longitude, project.latitude] },
        properties,
      };
    }),
  };
  const blob = new Blob([JSON.stringify(featureCollection, null, 2)], { type: "application/geo+json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "jp-ecosystem-public-projects-v1.2.geojson";
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function refreshMapSoon() {
  [0, 100, 320].forEach((delay) => window.setTimeout(() => state.map?.invalidateSize({ pan: false }), delay));
}

function initializeMap() {
  state.map = L.map("map", { zoomControl: true }).setView(state.config.default_center, state.config.default_zoom);
  L.tileLayer(state.config.tile_url, { maxZoom: state.config.maximum_zoom, attribution: state.config.tile_attribution }).addTo(state.map);
  L.control.scale({ imperial: false }).addTo(state.map);
  state.projectLayer = L.layerGroup().addTo(state.map);
  state.componentLayer = L.layerGroup().addTo(state.map);
  state.supplementalLayer = L.layerGroup().addTo(state.map);
  state.map.on("popupopen", (event) => {
    const button = event.popup.getElement()?.querySelector("[data-view-project]");
    if (button) button.addEventListener("click", () => selectProject(button.dataset.viewProject, { pan: false, openPopup: false }));
  });
  state.map.on("zoomend", updateProjectTooltips);
  const mapElement = document.getElementById("map");
  if ("ResizeObserver" in window) {
    const observer = new ResizeObserver(refreshMapSoon);
    observer.observe(mapElement);
    if (mapElement.parentElement) observer.observe(mapElement.parentElement);
  }
  window.addEventListener("resize", refreshMapSoon, { passive: true });
  window.addEventListener("orientationchange", () => window.setTimeout(refreshMapSoon, 250), { passive: true });
  window.addEventListener("pageshow", () => window.setTimeout(refreshMapSoon, 50), { passive: true });
  refreshMapSoon();
}

function requestedProjectIdFromHash() {
  const match = window.location.hash.match(/^#project=([^&]+)$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function attachEvents() {
  [elements.search, elements.status, elements.sector, elements.function, elements.company].forEach((element) => {
    element.addEventListener(element === elements.search ? "input" : "change", () => applyFilters());
  });
  elements.reset.addEventListener("click", () => {
    elements.search.value = ""; elements.status.value = ""; elements.sector.value = ""; elements.function.value = ""; elements.company.value = "";
    applyFilters();
  });
  [elements.layerProjects, elements.layerOpportunities, elements.layerLocations].forEach((element) => element.addEventListener("change", () => renderMapMarkers({ fitBounds: false })));
  elements.download.addEventListener("click", downloadGeoJSON);
  elements.detailClose.addEventListener("click", closeProjectDetail);
  elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveTab(tab.dataset.tab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const index = elements.tabs.indexOf(tab);
      const next = (index + (event.key === "ArrowRight" ? 1 : -1) + elements.tabs.length) % elements.tabs.length;
      elements.tabs[next].focus();
      setActiveTab(elements.tabs[next].dataset.tab);
    });
  });
  elements.filterToggle.addEventListener("click", () => {
    const open = elements.appHeader.classList.toggle("filters-open");
    elements.filterToggle.setAttribute("aria-expanded", String(open));
    elements.filterToggle.textContent = open ? "Hide filters" : "Filters";
    refreshMapSoon();
  });
  const toggleList = () => {
    const collapsed = elements.projectPane.classList.toggle("collapsed");
    elements.workspace.classList.toggle("list-collapsed", collapsed);
    elements.listToggle.setAttribute("aria-expanded", String(!collapsed));
    elements.listToggle.textContent = collapsed ? "Show list" : "Hide list";
    elements.mapListButton.textContent = collapsed ? "Show projects" : "Hide projects";
    refreshMapSoon();
  };
  elements.listToggle.addEventListener("click", toggleList);
  elements.mapListButton.addEventListener("click", toggleList);
  window.addEventListener("hashchange", () => {
    const projectId = requestedProjectIdFromHash();
    if (projectId && projectId !== state.activeProjectId) selectProject(projectId, { updateLocation: false });
  });
  window.addEventListener("keydown", (event) => { if (event.key === "Escape" && state.activeProjectId) closeProjectDetail(); });
}

async function loadApplication() {
  try {
    clearMessage();
    const cacheBust = `v=${Date.now()}`;
    const configResponse = await fetch(`map-config.json?${cacheBust}`, { cache: "no-store" });
    if (!configResponse.ok) throw new Error(`Could not load map-config.json (${configResponse.status})`);
    state.config = await configResponse.json();
    const files = state.config.data_files;
    const [rawProjects, organizations, people, projectParties, projectFunding, workCatalog, rawWorkItems, materialsMaster, rawInventory, rawComponents, sourceLinks, rawOpportunities, rawLocations, rawPublication] = await Promise.all([
      loadCSV(files.projects, cacheBust), loadCSV(files.organizations, cacheBust), loadCSV(files.people, cacheBust),
      loadCSV(files.project_parties, cacheBust), loadCSV(files.project_funding, cacheBust), loadCSV(files.work_catalog, cacheBust),
      loadCSV(files.project_work_items, cacheBust), loadCSV(files.materials_master, cacheBust), loadCSV(files.project_material_inventory, cacheBust),
      loadCSV(files.project_components, cacheBust), loadCSV(files.project_source_links, cacheBust), loadCSV(files.project_opportunities, cacheBust),
      loadCSV(files.organization_locations, cacheBust), loadCSV(files.project_publication_settings, cacheBust),
    ]);

    state.organizations = organizations.filter((row) => parseBoolean(row.is_public, true));
    state.people = people.filter((row) => parseBoolean(row.is_public));
    state.projectParties = projectParties;
    state.projectFunding = projectFunding;
    state.workCatalog = workCatalog;
    state.projectWorkItems = rawWorkItems.map(normalizeWorkItem);
    state.materialsMaster = materialsMaster;
    state.projectMaterialInventory = rawInventory.map(normalizeInventory);
    state.projectComponents = rawComponents.map(normalizeComponent);
    state.projectSourceLinks = sourceLinks.filter((row) => parseBoolean(row.is_public));
    state.projectOpportunities = rawOpportunities.map(normalizeOpportunity);
    state.organizationLocations = rawLocations.map(normalizeOrganizationLocation);
    state.publicationSettings = rawPublication.map(normalizePublicationSetting);
    buildIndexes();

    const accepted = [];
    const errors = [];
    const ids = new Set();
    rawProjects.forEach((raw, index) => {
      try {
        const project = normalizeProject(raw, index);
        if (!project.is_public) return;
        if (ids.has(project.project_id)) throw new Error(`projects.csv row ${index + 2}: duplicate project_id "${project.project_id}"`);
        ids.add(project.project_id);
        accepted.push(project);
      } catch (error) { errors.push(error.message); }
    });
    state.projects = accepted;
    state.filteredProjects = [...accepted];

    elements.siteTitle.textContent = state.config.site_title;
    elements.siteSubtitle.textContent = state.config.site_subtitle;
    elements.versionBadge.textContent = `v${state.config.app_version}`;
    elements.notice.textContent = state.config.public_notice;
    elements.notice.hidden = !state.config.features.show_public_notice;
    elements.download.hidden = !state.config.features.show_download_buttons;
    elements.layerOpportunities.checked = state.config.features.show_opportunities !== false;
    elements.layerLocations.checked = state.config.features.show_organization_locations !== false;

    initializeMap();
    fillFilters();
    renderLegend();
    attachEvents();
    applyFilters({ fitBounds: true });
    if (errors.length) showMessage(`${errors.length} project row(s) were skipped. First issue: ${errors[0]}`, "warning");
    const requested = requestedProjectIdFromHash();
    if (requested) selectProject(requested, { updateLocation: false, openPopup: false });
  } catch (error) {
    const hint = window.location.protocol === "file:" ? " This data-driven site cannot run by double-clicking index.html. Use GitHub Pages or run a local HTTP server." : "";
    showMessage(`The map could not load its data. ${error.message}.${hint}`, "error");
    elements.siteSubtitle.textContent = "Data-loading error";
  }
}

loadApplication();
