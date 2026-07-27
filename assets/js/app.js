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
  organizationById: new Map(),
  personById: new Map(),
  workById: new Map(),
  materialById: new Map(),
  filteredProjects: [],
  map: null,
  markerLayer: null,
  markerByProjectId: new Map(),
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
  company: document.getElementById("company-filter"),
  reset: document.getElementById("reset-button"),
  download: document.getElementById("download-button"),
  filterToggle: document.getElementById("filter-toggle"),
  listToggle: document.getElementById("list-toggle"),
  mapListButton: document.getElementById("map-list-button"),
  projectPane: document.getElementById("project-pane"),
  list: document.getElementById("project-list"),
  legend: document.getElementById("status-legend"),
  notice: document.getElementById("public-notice"),
  message: document.getElementById("map-message"),
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
  return (
    state.config?.human_labels?.[value] ||
    value
      .toLowerCase()
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ")
  );
}

function directionsURL(project) {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(
    `${project.latitude},${project.longitude}`
  )}`;
}

async function loadCSV(path, cacheBust) {
  const response = await fetch(`${path}?${cacheBust}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load ${path} (${response.status})`);
  }
  return parseCSV(await response.text());
}

function required(raw, field, rowNumber, fileName) {
  const value = String(raw[field] ?? "").trim();
  if (!value) {
    throw new Error(`${fileName} row ${rowNumber}: ${field} is blank`);
  }
  return value;
}

function normalizeProject(raw, index) {
  const rowNumber = index + 2;
  const latitude = Number(required(raw, "latitude", rowNumber, "projects.csv"));
  const longitude = Number(required(raw, "longitude", rowNumber, "projects.csv"));

  if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
    throw new Error(`projects.csv row ${rowNumber}: invalid latitude`);
  }
  if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    throw new Error(`projects.csv row ${rowNumber}: invalid longitude`);
  }

  const status = required(raw, "status", rowNumber, "projects.csv");
  if (!state.config.status_styles[status]) {
    throw new Error(`projects.csv row ${rowNumber}: unknown status "${status}"`);
  }

  return {
    ...raw,
    project_id: required(raw, "project_id", rowNumber, "projects.csv"),
    company_project_code: required(
      raw,
      "company_project_code",
      rowNumber,
      "projects.csv"
    ),
    legacy_project_code: required(
      raw,
      "legacy_project_code",
      rowNumber,
      "projects.csv"
    ),
    project_name: required(raw, "project_name", rowNumber, "projects.csv"),
    display_name:
      raw.display_name || raw.project_name.replaceAll("_", " "),
    executing_company_id: required(
      raw,
      "executing_company_id",
      rowNumber,
      "projects.csv"
    ),
    latitude,
    longitude,
    status,
    physical_progress_percent: parseOptionalNumber(
      raw.physical_progress_percent
    ),
    financial_progress_percent: parseOptionalNumber(
      raw.financial_progress_percent
    ),
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

function buildIndexes() {
  state.organizationById = new Map(
    state.organizations.map((organization) => [
      organization.organization_id,
      organization,
    ])
  );
  state.personById = new Map(
    state.people.map((person) => [person.person_id, person])
  );
  state.workById = new Map(
    state.workCatalog.map((work) => [work.work_id, work])
  );
  state.materialById = new Map(
    state.materialsMaster.map((material) => [
      material.material_id,
      material,
    ])
  );
}

function companyName(project) {
  return (
    state.organizationById.get(project.executing_company_id)
      ?.organization_name || "Company not entered"
  );
}

function fillFilters() {
  const statuses = [...new Set(state.projects.map((project) => project.status))]
    .sort(
      (left, right) =>
        state.config.status_styles[left].order -
        state.config.status_styles[right].order
    );

  statuses.forEach((status) => {
    const option = document.createElement("option");
    option.value = status;
    option.textContent = state.config.status_styles[status].label;
    elements.status.append(option);
  });

  const companies = [
    ...new Map(
      state.projects.map((project) => [
        project.executing_company_id,
        companyName(project),
      ])
    ).entries(),
  ].sort((left, right) => left[1].localeCompare(right[1]));

  companies.forEach(([organizationId, name]) => {
    const option = document.createElement("option");
    option.value = organizationId;
    option.textContent = name;
    elements.company.append(option);
  });
}

function renderLegend() {
  elements.legend.replaceChildren();
  Object.entries(state.config.status_styles)
    .sort(([, left], [, right]) => left.order - right.order)
    .forEach(([status, style]) => {
      if (!state.projects.some((project) => project.status === status)) return;
      const chip = document.createElement("span");
      chip.className = "status-chip";
      chip.innerHTML = `<span class="status-dot" style="background:${escapeHTML(
        style.color
      )}"></span>${escapeHTML(style.label)}`;
      elements.legend.append(chip);
    });
}

function projectMatchesFilters(project) {
  const query = elements.search.value.trim().toLowerCase();
  const selectedStatus = elements.status.value;
  const selectedCompany = elements.company.value;
  const parties = state.projectParties
    .filter((party) => party.project_id === project.project_id)
    .map((party) => party.party_id)
    .join(" ");

  const searchable = [
    project.project_id,
    project.company_project_code,
    project.legacy_project_code,
    project.project_name,
    project.display_name,
    project.status,
    project.project_sector,
    project.implementation_mechanism,
    companyName(project),
    project.latest_update,
    project.public_notes,
    parties,
  ]
    .join(" ")
    .toLowerCase();

  return (
    (!query || searchable.includes(query)) &&
    (!selectedStatus || project.status === selectedStatus) &&
    (!selectedCompany ||
      project.executing_company_id === selectedCompany)
  );
}

function renderProjectList() {
  elements.list.replaceChildren();
  elements.listCount.textContent = `${state.filteredProjects.length} shown`;

  if (!state.filteredProjects.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML =
      "<strong>No matching projects</strong>Change or reset the filters.";
    elements.list.append(empty);
    return;
  }

  state.filteredProjects.forEach((project) => {
    const style = state.config.status_styles[project.status];
    const item = document.createElement("button");
    item.type = "button";
    item.className = `project-item${
      state.activeProjectId === project.project_id ? " active" : ""
    }`;
    item.setAttribute(
      "aria-current",
      state.activeProjectId === project.project_id ? "true" : "false"
    );
    const progress =
      project.physical_progress_percent === null
        ? ""
        : ` · ${project.physical_progress_percent}% physical`;

    item.innerHTML = `
      <div class="project-item-head">
        <div>
          <div class="project-code">${escapeHTML(
            project.company_project_code
          )}</div>
          <div class="project-name">${escapeHTML(project.display_name)}</div>
        </div>
        <span class="badge">
          <span class="status-dot" style="background:${escapeHTML(
            style.color
          )}"></span>
          ${escapeHTML(style.label)}
        </span>
      </div>
      <div class="project-meta">
        ${escapeHTML(companyName(project))}${escapeHTML(progress)}
      </div>
    `;
    item.addEventListener("click", () => selectProject(project.project_id));
    elements.list.append(item);
  });
}

function popupHTML(project) {
  return `
    <div class="popup">
      <div class="popup-code">${escapeHTML(
        project.company_project_code
      )}</div>
      <h3>${escapeHTML(project.display_name)}</h3>
      <div class="popup-status">${escapeHTML(project.status)}</div>
      <div class="popup-actions">
        <button type="button" data-view-project="${escapeHTML(
          project.project_id
        )}">View Project</button>
        <a href="${directionsURL(
          project
        )}" target="_blank" rel="noopener">Directions</a>
      </div>
    </div>
  `;
}

function renderMapMarkers({ fitBounds = false } = {}) {
  state.markerLayer.clearLayers();
  state.markerByProjectId.clear();
  const bounds = [];

  state.filteredProjects.forEach((project) => {
    const style = state.config.status_styles[project.status];
    const marker = L.circleMarker([project.latitude, project.longitude], {
      radius: state.config.marker.radius,
      color: style.color,
      fillColor: style.color,
      fillOpacity: state.config.marker.fill_opacity,
      weight: state.config.marker.weight,
    })
      .bindTooltip(project.company_project_code, {
        permanent: true,
        direction: state.config.marker.tooltip_direction,
        offset: state.config.marker.tooltip_offset,
      })
      .bindPopup(popupHTML(project), { minWidth: 220, maxWidth: 280 })
      .addTo(state.markerLayer);

    marker.on("click", () =>
      selectProject(project.project_id, { pan: false, openPopup: false })
    );
    state.markerByProjectId.set(project.project_id, marker);
    bounds.push([project.latitude, project.longitude]);
  });

  if (fitBounds && bounds.length) {
    state.map.invalidateSize({ pan: false });
    state.map.fitBounds(bounds, {
      padding: [
        state.config.fit_bounds_padding,
        state.config.fit_bounds_padding,
      ],
    });
  }
}

function roleRows(project) {
  return state.projectParties
    .filter(
      (party) =>
        party.project_id === project.project_id &&
        parseBoolean(party.is_public)
    )
    .map((party) => {
      let name = "";
      if (party.party_entity_type === "ORGANIZATION") {
        name =
          state.organizationById.get(party.party_id)?.organization_name || "";
      } else if (party.party_entity_type === "PERSON") {
        name = state.personById.get(party.party_id)?.display_name || "";
      }
      return [humanLabel(party.role), name];
    })
    .filter(([, value]) => value);
}

function fundingRows(project) {
  return state.projectFunding
    .filter(
      (funding) =>
        funding.project_id === project.project_id &&
        parseBoolean(funding.is_public)
    )
    .map((funding) => {
      const funder =
        state.organizationById.get(funding.funding_party_id)
          ?.organization_name || "";
      const fundingType = humanLabel(funding.funding_type);
      const value = [funder, fundingType ? `(${fundingType})` : ""]
        .filter(Boolean)
        .join(" ");
      return ["Funding source", value];
    })
    .filter(([, value]) => value);
}

function detailGrid(rows) {
  const visibleRows = rows.filter(([, value]) => value !== null && value !== "");
  if (!visibleRows.length) return "";
  return `<dl class="detail-grid">${visibleRows
    .map(
      ([label, value]) =>
        `<dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value)}</dd>`
    )
    .join("")}</dl>`;
}

function progressBlock(label, value) {
  if (value === null || value === undefined) return "";
  const safeValue = Math.min(100, Math.max(0, Number(value)));
  return `
    <div class="progress-block">
      <div class="progress-head"><span>${escapeHTML(
        label
      )}</span><strong>${escapeHTML(safeValue)}%</strong></div>
      <div class="progress-track" role="progressbar" aria-label="${escapeHTML(
        label
      )}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${escapeHTML(
        safeValue
      )}">
        <div class="progress-fill" style="width:${safeValue}%"></div>
      </div>
    </div>
  `;
}

function renderOverview(project) {
  const identifiers = detailGrid([
    ["Global project ID", project.project_id],
    ["Company project code", project.company_project_code],
    ["Legacy code", project.legacy_project_code],
  ]);
  const classifications = detailGrid([
    ["Company", companyName(project)],
    ["Project sector", humanLabel(project.project_sector)],
    ["Government level", humanLabel(project.government_level)],
    [
      "Implementation",
      humanLabel(project.implementation_mechanism),
    ],
    ["Status", project.status],
  ]);
  const dates = detailGrid([
    ["Start date", prettyDate(project.start_date)],
    ["Target completion", prettyDate(project.target_completion_date)],
    ["Actual completion", prettyDate(project.actual_completion_date)],
    ["Last updated", prettyDate(project.last_updated)],
  ]);
  const updates = detailGrid([
    ["Latest update", project.latest_update],
    ["Public notes", project.public_notes],
  ]);
  const relationships = detailGrid([
    ...roleRows(project),
    ...fundingRows(project),
  ]);
  const physicalProgress = progressBlock(
    "Physical Progress",
    project.physical_progress_percent
  );
  const financialProgress =
    state.config.features.show_financial_progress
      ? progressBlock(
          "Financial Progress",
          project.financial_progress_percent
        )
      : "";
  const progress = physicalProgress || financialProgress;
  const projectDetailsLink = project.details_url
    ? `<a class="detail-link" href="${escapeHTML(
        project.details_url
      )}" target="_blank" rel="noopener">Project details</a>`
    : "";

  elements.overviewPanel.innerHTML = `
    ${
      progress
        ? `<div class="section-card"><h3>Progress</h3>${progress}</div>`
        : ""
    }
    <div class="section-card">
      <h3>Project identity</h3>
      ${identifiers}
    </div>
    <div class="section-card">
      <h3>Classification</h3>
      ${classifications}
    </div>
    ${
      relationships
        ? `<div class="section-card"><h3>Project parties</h3>${relationships}</div>`
        : ""
    }
    ${
      dates
        ? `<div class="section-card"><h3>Dates</h3>${dates}</div>`
        : ""
    }
    ${
      updates
        ? `<div class="section-card"><h3>Public update</h3>${updates}</div>`
        : ""
    }
    <div class="section-card">
      <h3>Open</h3>
      <div class="detail-actions">
        <a class="detail-link primary" href="${directionsURL(
          project
        )}" target="_blank" rel="noopener">Directions</a>
        ${projectDetailsLink}
      </div>
    </div>
  `;
}

function projectWorkItems(projectId) {
  return state.projectWorkItems.filter(
    (item) => item.project_id === projectId && item.is_public
  );
}

function projectMaterials(projectId) {
  return state.projectMaterialInventory.filter(
    (item) => item.project_id === projectId && item.is_public
  );
}

function workStatusBadge(status) {
  return `<span class="badge">${escapeHTML(humanLabel(status))}</span>`;
}

function quantityText(value, unit) {
  if (value === null || value === undefined) return "";
  return `${new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 3,
  }).format(value)}${unit ? ` ${unit}` : ""}`;
}

function renderWorks(project) {
  const items = projectWorkItems(project.project_id);
  elements.worksTabCount.textContent = String(items.length);

  if (!items.length) {
    elements.worksPanel.innerHTML = `
      <div class="empty-state">
        <strong>No project work items published</strong>
        The reusable work catalog is ready, but no source BOQ group has been
        assigned to this project because its project association is not yet verified.
      </div>
    `;
    return;
  }

  const counts = Object.fromEntries(
    state.config.controlled_values.work_statuses.map((status) => [
      status,
      items.filter((item) => item.work_status === status).length,
    ])
  );
  const completed = counts.COMPLETED || 0;
  const active = (counts.IN_PROGRESS || 0) + (counts.BLOCKED || 0);
  const remaining =
    (counts.NOT_STARTED || 0) +
    (counts.ON_HOLD || 0) +
    (counts.BLOCKED || 0);

  const filters = [
    ["", `All ${items.length}`],
    ...state.config.controlled_values.work_statuses
      .filter((status) => counts[status])
      .map((status) => [status, `${humanLabel(status)} ${counts[status]}`]),
  ];

  const filteredItems = state.activeWorkFilter
    ? items.filter((item) => item.work_status === state.activeWorkFilter)
    : items;

  elements.worksPanel.innerHTML = `
    <div class="summary-row">
      <div class="summary-box"><strong>${completed}</strong><span>completed</span></div>
      <div class="summary-box"><strong>${active}</strong><span>active / blocked</span></div>
      <div class="summary-box"><strong>${remaining}</strong><span>remaining</span></div>
    </div>
    <div class="work-filters" aria-label="Filter work items by status">
      ${filters
        .map(
          ([value, label]) =>
            `<button class="work-filter${
              state.activeWorkFilter === value ? " active" : ""
            }" type="button" data-work-filter="${escapeHTML(
              value
            )}">${escapeHTML(label)}</button>`
        )
        .join("")}
    </div>
    <div>
      ${filteredItems
        .map((item) => {
          const catalog = state.workById.get(item.work_id);
          const description =
            item.description_override ||
            catalog?.description ||
            "Work description not entered";
          const quantities = [
            item.planned_quantity !== null
              ? `Planned: ${quantityText(item.planned_quantity, item.unit)}`
              : "",
            item.completed_quantity !== null
              ? `Completed: ${quantityText(
                  item.completed_quantity,
                  item.unit
                )}`
              : "",
            item.remaining_quantity !== null
              ? `Remaining: ${quantityText(
                  item.remaining_quantity,
                  item.unit
                )}`
              : "",
          ]
            .filter(Boolean)
            .join(" · ");
          return `
            <article class="work-card">
              <div class="work-title-row">
                <div class="work-title">${escapeHTML(description)}</div>
                ${workStatusBadge(item.work_status)}
              </div>
              ${quantities ? `<div class="work-meta">${escapeHTML(quantities)}</div>` : ""}
              ${progressBlock("Work progress", item.progress_percent)}
              ${
                item.remarks
                  ? `<div class="work-remarks">${escapeHTML(item.remarks)}</div>`
                  : ""
              }
            </article>
          `;
        })
        .join("")}
    </div>
  `;

  elements.worksPanel
    .querySelectorAll("[data-work-filter]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        state.activeWorkFilter = button.dataset.workFilter;
        renderWorks(project);
      });
    });
}

function renderMaterials(project) {
  const items = projectMaterials(project.project_id);

  if (!state.config.features.show_inventory_quantities) {
    elements.materialsTabCount.textContent = "—";
    elements.materialsPanel.innerHTML = `
      <div class="empty-state">
        <strong>Public stock quantities are disabled</strong>
        The material-inventory structure is ready, but exact site stock remains
        internal unless publication is explicitly approved.
      </div>
    `;
    return;
  }

  elements.materialsTabCount.textContent = String(items.length);
  if (!items.length) {
    elements.materialsPanel.innerHTML = `
      <div class="empty-state">
        <strong>No approved public inventory snapshot</strong>
        No material quantity has been invented or inferred for this project.
      </div>
    `;
    return;
  }

  const dates = items.map((item) => item.as_of_date).filter(Boolean).sort();
  const asOf = dates.length ? prettyDate(dates.at(-1)) : "Not entered";
  elements.materialsPanel.innerHTML = `
    <div class="section-card">
      <h3>Inventory summary</h3>
      ${detailGrid([
        ["Materials recorded", String(items.length)],
        ["Latest inventory date", asOf],
      ])}
    </div>
    ${items
      .map((item) => {
        const material = state.materialById.get(item.material_id);
        const name = material?.material_name || "Material not found";
        const quantities = [
          item.quantity_on_site !== null
            ? `On site: ${quantityText(item.quantity_on_site, item.unit)}`
            : "",
          item.available_quantity !== null
            ? `Available: ${quantityText(item.available_quantity, item.unit)}`
            : "",
        ]
          .filter(Boolean)
          .join(" · ");
        return `
          <article class="material-card">
            <div class="material-title-row">
              <div class="material-title">${escapeHTML(name)}</div>
              ${
                item.condition
                  ? `<span class="badge">${escapeHTML(
                      humanLabel(item.condition)
                    )}</span>`
                  : ""
              }
            </div>
            ${quantities ? `<div class="material-meta">${escapeHTML(quantities)}</div>` : ""}
            ${
              item.storage_location
                ? `<div class="material-meta">Storage: ${escapeHTML(
                    item.storage_location
                  )}</div>`
                : ""
            }
            ${
              item.remarks
                ? `<div class="material-remarks">${escapeHTML(
                    item.remarks
                  )}</div>`
                : ""
            }
          </article>
        `;
      })
      .join("")}
  `;
}

function setActiveTab(tabName) {
  state.activeTab = tabName;
  const panels = {
    overview: elements.overviewPanel,
    works: elements.worksPanel,
    materials: elements.materialsPanel,
  };

  elements.tabs.forEach((tab) => {
    const active = tab.dataset.tab === tabName;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });

  Object.entries(panels).forEach(([name, panel]) => {
    const active = name === tabName;
    panel.hidden = !active;
    panel.classList.toggle("active", active);
  });
}

function renderProjectDetail(project) {
  const works = projectWorkItems(project.project_id);
  const materials = projectMaterials(project.project_id);
  elements.detailCode.textContent = project.company_project_code;
  elements.detailTitle.textContent = project.display_name;
  elements.detailSubtitle.textContent = `${project.project_id} · legacy ${project.legacy_project_code}`;
  elements.worksTabCount.textContent = String(works.length);
  elements.materialsTabCount.textContent =
    state.config.features.show_inventory_quantities
      ? String(materials.length)
      : "—";
  state.activeWorkFilter = "";
  renderOverview(project);
  renderWorks(project);
  renderMaterials(project);
  setActiveTab(state.activeTab);
}

function updateHash(projectId) {
  const nextHash = projectId ? `#project=${encodeURIComponent(projectId)}` : "";
  if (window.location.hash !== nextHash) {
    window.history.replaceState(null, "", nextHash || window.location.pathname);
  }
}

function selectProject(
  projectId,
  { pan = true, openPopup = true, updateLocation = true } = {}
) {
  const project = state.projects.find(
    (candidate) => candidate.project_id === projectId
  );
  if (!project) return;

  state.activeProjectId = projectId;
  state.activeTab = "overview";
  elements.workspace.classList.add("detail-open");
  elements.detailPanel.inert = false;
  renderProjectList();
  renderProjectDetail(project);

  const marker = state.markerByProjectId.get(projectId);
  if (pan && marker) {
    state.map.setView(
      [project.latitude, project.longitude],
      Math.max(state.map.getZoom(), 15),
      { animate: true }
    );
  }
  if (openPopup && marker) marker.openPopup();
  if (updateLocation) updateHash(projectId);
  refreshMapSoon();
}

function closeProjectDetail() {
  elements.workspace.classList.remove("detail-open");
  elements.detailPanel.inert = true;
  updateHash("");
  refreshMapSoon();
}

function applyFilters({ fitBounds = true } = {}) {
  state.filteredProjects = state.projects.filter(projectMatchesFilters);
  if (
    state.activeProjectId &&
    !state.filteredProjects.some(
      (project) => project.project_id === state.activeProjectId
    )
  ) {
    state.activeProjectId = null;
    closeProjectDetail();
  }
  renderProjectList();
  renderMapMarkers({ fitBounds });
  renderMetrics();
}

function renderMetrics() {
  elements.visibleCount.textContent = String(state.filteredProjects.length);
  elements.publicCount.textContent = String(state.projects.length);
  const dates = state.projects
    .map((project) => project.last_updated)
    .filter(Boolean)
    .sort();
  elements.updatedDate.textContent = dates.length
    ? prettyDate(dates.at(-1))
    : "—";
}

function downloadGeoJSON() {
  const includeFinancial =
    state.config.features.show_financial_progress === true;
  const featureCollection = {
    type: "FeatureCollection",
    name: "jp_ecosystem_public_projects",
    generated_from_app_version: state.config.app_version,
    data_schema_version: state.config.data_schema_version,
    features: state.filteredProjects.map((project) => {
      const properties = {
        project_id: project.project_id,
        company_project_code: project.company_project_code,
        legacy_project_code: project.legacy_project_code,
        project_name: project.project_name,
        display_name: project.display_name,
        project_sector: project.project_sector,
        government_level: project.government_level,
        implementation_mechanism: project.implementation_mechanism,
        executing_company: companyName(project),
        status: project.status,
        physical_progress_percent: project.physical_progress_percent,
        last_updated: project.last_updated,
        latest_update: project.latest_update,
        public_notes: project.public_notes,
      };
      if (includeFinancial) {
        properties.financial_progress_percent =
          project.financial_progress_percent;
      }
      return {
        type: "Feature",
        id: project.project_id,
        geometry: {
          type: "Point",
          coordinates: [project.longitude, project.latitude],
        },
        properties,
      };
    }),
  };

  const blob = new Blob([JSON.stringify(featureCollection, null, 2)], {
    type: "application/geo+json",
  });
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
  [0, 100, 320].forEach((delay) => {
    window.setTimeout(() => {
      state.map?.invalidateSize({ pan: false });
    }, delay);
  });
}

function initializeMap() {
  state.map = L.map("map", { zoomControl: true }).setView(
    state.config.default_center,
    state.config.default_zoom
  );
  L.tileLayer(state.config.tile_url, {
    maxZoom: state.config.maximum_zoom,
    attribution: state.config.tile_attribution,
  }).addTo(state.map);
  L.control.scale({ imperial: false }).addTo(state.map);
  state.markerLayer = L.layerGroup().addTo(state.map);

  state.map.on("popupopen", (event) => {
    const button = event.popup
      .getElement()
      ?.querySelector("[data-view-project]");
    if (button) {
      button.addEventListener("click", () =>
        selectProject(button.dataset.viewProject, {
          pan: false,
          openPopup: false,
        })
      );
    }
  });

  const mapElement = document.getElementById("map");
  if ("ResizeObserver" in window) {
    const resizeObserver = new ResizeObserver(refreshMapSoon);
    resizeObserver.observe(mapElement);
    if (mapElement.parentElement) {
      resizeObserver.observe(mapElement.parentElement);
    }
  }

  window.addEventListener("resize", refreshMapSoon, { passive: true });
  window.addEventListener(
    "orientationchange",
    () => window.setTimeout(refreshMapSoon, 250),
    { passive: true }
  );
  window.addEventListener(
    "pageshow",
    () => window.setTimeout(refreshMapSoon, 50),
    { passive: true }
  );
  refreshMapSoon();
}

function requestedProjectIdFromHash() {
  const match = window.location.hash.match(/^#project=([^&]+)$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function attachEvents() {
  elements.search.addEventListener("input", () => applyFilters());
  elements.status.addEventListener("change", () => applyFilters());
  elements.company.addEventListener("change", () => applyFilters());
  elements.reset.addEventListener("click", () => {
    elements.search.value = "";
    elements.status.value = "";
    elements.company.value = "";
    applyFilters();
  });
  elements.download.addEventListener("click", downloadGeoJSON);
  elements.detailClose.addEventListener("click", closeProjectDetail);

  elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveTab(tab.dataset.tab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const currentIndex = elements.tabs.indexOf(tab);
      const direction = event.key === "ArrowRight" ? 1 : -1;
      const nextIndex =
        (currentIndex + direction + elements.tabs.length) %
        elements.tabs.length;
      elements.tabs[nextIndex].focus();
      setActiveTab(elements.tabs[nextIndex].dataset.tab);
    });
  });

  elements.filterToggle.addEventListener("click", () => {
    const open = elements.appHeader.classList.toggle("filters-open");
    elements.filterToggle.setAttribute("aria-expanded", String(open));
    elements.filterToggle.textContent = open ? "Hide filters" : "Filters";
    refreshMapSoon();
  });

  const toggleProjectList = () => {
    const collapsed = elements.projectPane.classList.toggle("collapsed");
    elements.workspace.classList.toggle("list-collapsed", collapsed);
    elements.listToggle.setAttribute("aria-expanded", String(!collapsed));
    elements.listToggle.textContent = collapsed ? "Show list" : "Hide list";
    elements.mapListButton.textContent = collapsed ? "Show projects" : "Hide projects";
    refreshMapSoon();
  };
  elements.listToggle.addEventListener("click", toggleProjectList);
  elements.mapListButton.addEventListener("click", toggleProjectList);

  window.addEventListener("hashchange", () => {
    const projectId = requestedProjectIdFromHash();
    if (projectId && projectId !== state.activeProjectId) {
      selectProject(projectId, { updateLocation: false });
    }
  });
}

async function loadApplication() {
  try {
    clearMessage();
    const cacheBust = `v=${Date.now()}`;
    const configResponse = await fetch(`map-config.json?${cacheBust}`, {
      cache: "no-store",
    });
    if (!configResponse.ok) {
      throw new Error(`Could not load map-config.json (${configResponse.status})`);
    }
    state.config = await configResponse.json();
    const files = state.config.data_files;

    const [
      rawProjects,
      organizations,
      people,
      projectParties,
      projectFunding,
      workCatalog,
      rawProjectWorkItems,
      materialsMaster,
      rawInventory,
    ] = await Promise.all([
      loadCSV(files.projects, cacheBust),
      loadCSV(files.organizations, cacheBust),
      loadCSV(files.people, cacheBust),
      loadCSV(files.project_parties, cacheBust),
      loadCSV(files.project_funding, cacheBust),
      loadCSV(files.work_catalog, cacheBust),
      loadCSV(files.project_work_items, cacheBust),
      loadCSV(files.materials_master, cacheBust),
      loadCSV(files.project_material_inventory, cacheBust),
    ]);

    state.organizations = organizations.filter((row) =>
      parseBoolean(row.is_public, true)
    );
    state.people = people.filter((row) => parseBoolean(row.is_public));
    state.projectParties = projectParties;
    state.projectFunding = projectFunding;
    state.workCatalog = workCatalog;
    state.projectWorkItems = rawProjectWorkItems.map(normalizeWorkItem);
    state.materialsMaster = materialsMaster;
    state.projectMaterialInventory = rawInventory.map(normalizeInventory);
    buildIndexes();

    const accepted = [];
    const errors = [];
    const ids = new Set();
    rawProjects.forEach((rawProject, index) => {
      try {
        const project = normalizeProject(rawProject, index);
        if (!project.is_public) return;
        if (ids.has(project.project_id)) {
          throw new Error(
            `projects.csv row ${index + 2}: duplicate project_id "${
              project.project_id
            }"`
          );
        }
        ids.add(project.project_id);
        accepted.push(project);
      } catch (error) {
        errors.push(error.message);
      }
    });
    state.projects = accepted;
    state.filteredProjects = [...accepted];

    elements.siteTitle.textContent = state.config.site_title;
    elements.siteSubtitle.textContent = state.config.site_subtitle;
    elements.versionBadge.textContent = `v${state.config.app_version}`;
    elements.notice.textContent = state.config.public_notice;
    elements.notice.hidden = !state.config.features.show_public_notice;
    elements.download.hidden = !state.config.features.show_download_buttons;

    initializeMap();
    fillFilters();
    renderLegend();
    attachEvents();
    applyFilters({ fitBounds: true });

    if (errors.length) {
      showMessage(
        `${errors.length} project row(s) were skipped. First issue: ${errors[0]}`,
        "warning"
      );
    }

    const requestedProject = requestedProjectIdFromHash();
    if (requestedProject) {
      selectProject(requestedProject, {
        updateLocation: false,
        openPopup: false,
      });
    }
  } catch (error) {
    const localFileHint =
      window.location.protocol === "file:"
        ? " This data-driven site cannot run by double-clicking index.html. Use GitHub Pages or run python serve-local.py."
        : "";
    showMessage(
      `The map could not load its data. ${error.message}.${localFileHint}`,
      "error"
    );
    elements.siteSubtitle.textContent = "Data-loading error";
  }
}

loadApplication();
