# v1.2 Data Dictionary

## Reading this document

Datatype concepts are designed for eventual PostgreSQL/Supabase migration:

- `text` — string
- `uuid-like text` — controlled human-readable stable ID
- `numeric` — plain number with no lakh commas stored in the value
- `date` — `YYYY-MM-DD`
- `boolean` — `TRUE` or `FALSE`
- `enum text` — controlled value from `map-config.json`

Privacy classes:

- `PUBLIC_OK` — normally acceptable in the public repository when verified
- `INTERNAL_BY_DEFAULT` — publish only after an explicit decision
- `SENSITIVE` — keep outside this public repository

`is_public=FALSE` is a display control, not a security control.

## 1. organizations.csv

Purpose: reusable companies, contractors, government bodies, municipalities,
wards, committees, consultants, suppliers, institutions, and NGOs.

Primary key: `organization_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| organization_id | uuid-like text | Yes | `ORG-000001` pattern | PUBLIC_OK |
| organization_code | text | Yes | Unique stable code | PUBLIC_OK |
| organization_name | text | Yes | Real verified name | PUBLIC_OK when approved |
| organization_type | enum text | Yes | `organization_types` | PUBLIC_OK |
| parent_organization_id | uuid-like text | No | FK → organizations.organization_id | PUBLIC_OK |
| government_level | enum text | No | `government_levels` | PUBLIC_OK |
| ward_number | numeric integer | No | 1–99 validation range | PUBLIC_OK |
| municipality_name | text | No | Verified administrative name | PUBLIC_OK |
| district | text | No | Verified name | PUBLIC_OK |
| province | text | No | Verified name | PUBLIC_OK |
| registration_number | text | No | Do not publish by default | SENSITIVE |
| active | boolean | Yes | TRUE/FALSE | PUBLIC_OK |
| notes | text | No | Public-safe note only | INTERNAL_BY_DEFAULT |
| is_public | boolean | Yes | UI display control | PUBLIC_OK |
| data_quality_status | enum text | Yes | quality status | PUBLIC_OK |
| source_reference | text | No | Traceability | INTERNAL_BY_DEFAULT |

Current example:

```csv
ORG-000001,FBL,Fishtail Builders Pvt Ltd,PRIVATE_COMPANY
```

## 2. people.csv

Purpose: reusable individuals when the real identity and public inclusion are
verified. The current file has no data rows.

Primary key: `person_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| person_id | uuid-like text | Yes for a row | `PER-000001` pattern | INTERNAL_BY_DEFAULT |
| person_code | text | No | Unique internal/public code if needed | INTERNAL_BY_DEFAULT |
| display_name | text | Yes for a row | Verified, publication-approved name | INTERNAL_BY_DEFAULT |
| active | boolean | Yes for a row | TRUE/FALSE | INTERNAL_BY_DEFAULT |
| notes | text | No | Never put private contacts here | INTERNAL_BY_DEFAULT |
| is_public | boolean | Yes for a row | UI display control | INTERNAL_BY_DEFAULT |
| data_quality_status | enum text | Yes for a row | quality status | INTERNAL_BY_DEFAULT |
| source_reference | text | No | Traceability | INTERNAL_BY_DEFAULT |

Phone, email, citizenship, bank, and other private fields are deliberately not
part of the public file.

## 3. projects.csv

Purpose: one row per mapped project.

Primary key: `project_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| project_id | uuid-like text | Yes | `PRJ-000001`; immutable | PUBLIC_OK |
| company_project_code | text | Yes | Unique; company-code prefix | PUBLIC_OK |
| legacy_project_code | text | Yes for migrated rows | Unique `P001` pattern | PUBLIC_OK |
| project_name | text | Yes | Machine/source name | PUBLIC_OK when approved |
| display_name | text | Yes | Human-facing name | PUBLIC_OK when approved |
| project_sector | enum text | No until verified | PRIVATE/GOVERNMENT_PUBLIC/OTHER | PUBLIC_OK |
| government_level | enum text | No | FEDERAL/PROVINCIAL/LOCAL/OTHER | PUBLIC_OK |
| implementation_mechanism | enum text | No until verified | controlled mechanisms | PUBLIC_OK |
| executing_company_id | uuid-like text | Yes | FK → organizations | PUBLIC_OK |
| latitude | numeric | Yes | −90 to 90 | PUBLIC_OK when approved |
| longitude | numeric | Yes | −180 to 180 | PUBLIC_OK when approved |
| status | enum text | Yes | key in `status_styles` | PUBLIC_OK |
| physical_progress_percent | numeric | No | 0–100 | PUBLIC_OK when approved |
| financial_progress_percent | numeric | No | 0–100 | INTERNAL_BY_DEFAULT |
| start_date | date | No | YYYY-MM-DD | PUBLIC_OK when approved |
| target_completion_date | date | No | YYYY-MM-DD | PUBLIC_OK when approved |
| actual_completion_date | date | No | YYYY-MM-DD | PUBLIC_OK when approved |
| last_updated | date | Yes | YYYY-MM-DD | PUBLIC_OK |
| latest_update | text | No | General approved update | PUBLIC_OK |
| photo_url | text URL | No | Public photo only | PUBLIC_OK |
| details_url | text URL | No | Public page/document only | PUBLIC_OK |
| public_notes | text | No | Public-safe note only | PUBLIC_OK |
| is_public | boolean | Yes | UI display control | PUBLIC_OK |
| data_quality_status | enum text | Yes | VALID/WARNING/ERROR/etc. | PUBLIC_OK |
| source_file | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_sheet | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_row | numeric integer | No | Provenance | INTERNAL_BY_DEFAULT |
| source_reference | text | No | Provenance description | INTERNAL_BY_DEFAULT |
| imported_at | date | No | Import date | INTERNAL_BY_DEFAULT |
| verified_by | text | No | Do not expose staff identity automatically | INTERNAL_BY_DEFAULT |
| verification_status | enum text | Yes | UNVERIFIED/VERIFIED | PUBLIC_OK |

Current example:

```csv
PRJ-000001,REB-001,P001,14_bishal_paija,14 Bishal Paija
```

## 4. project_parties.csv

Purpose: normalized project roles for organizations or people.

Primary key: `project_party_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| project_party_id | uuid-like text | Yes | `PPA-000001` | PUBLIC_OK |
| project_id | uuid-like text | Yes | FK → projects | PUBLIC_OK |
| party_entity_type | enum text | Yes | ORGANIZATION/PERSON | PUBLIC_OK |
| party_id | uuid-like text | Yes | FK → matching party master | Depends on party |
| role | enum text | Yes | controlled party role | PUBLIC_OK when approved |
| is_primary | boolean | Yes | TRUE/FALSE | PUBLIC_OK |
| start_date | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| end_date | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| remarks | text | No | Public-safe text only | INTERNAL_BY_DEFAULT |
| is_public | boolean | Yes | UI display control | PUBLIC_OK |
| data_quality_status | enum text | Yes | quality status | PUBLIC_OK |
| source_reference | text | No | Traceability | INTERNAL_BY_DEFAULT |

Current example:

```csv
PPA-000001,PRJ-000001,ORGANIZATION,ORG-000002,CONTRACTOR,TRUE
```

## 5. project_funding.csv

Purpose: record funding separately from how the project is implemented. The
current file has no data rows.

Primary key: `project_funding_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| project_funding_id | uuid-like text | Yes for a row | `PFD-000001` | INTERNAL_BY_DEFAULT |
| project_id | uuid-like text | Yes for a row | FK → projects | PUBLIC_OK |
| funding_party_id | uuid-like text | Yes for a row | FK → organizations | PUBLIC_OK when approved |
| funding_type | enum text | Yes for a row | controlled funding type | PUBLIC_OK when approved |
| approved_amount_npr | numeric | No | Plain number, no lakh commas | SENSITIVE |
| contribution_percent | numeric | No | 0–100 | INTERNAL_BY_DEFAULT |
| funding_date | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| remarks | text | No | Public-safe text only | INTERNAL_BY_DEFAULT |
| is_public | boolean | Yes for a row | UI display control | PUBLIC_OK |
| data_quality_status | enum text | Yes for a row | quality status | PUBLIC_OK |
| source_file | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_sheet | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_row | numeric integer | No | Provenance | INTERNAL_BY_DEFAULT |
| source_reference | text | No | Provenance | INTERNAL_BY_DEFAULT |

Illustrative only, not a current row:

```csv
PFD-009901,PRJ-009901,ORG-009901,LOCAL_GOVERNMENT,,,2026-07-26
```

## 6. work_catalog.csv

Purpose: one reusable master definition per construction work.

Primary key: `work_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| work_id | uuid-like text | Yes | `WRK-000001` | PUBLIC_OK |
| work_code | text | Yes | Unique reusable code | PUBLIC_OK |
| description | text | Yes | Master work description | PUBLIC_OK |
| category | text | Yes | Human category | PUBLIC_OK |
| subcategory | text | No | Human subcategory | PUBLIC_OK |
| default_unit | enum text | No | Controlled construction unit | PUBLIC_OK |
| active | boolean | Yes | TRUE/FALSE | PUBLIC_OK |
| notes | text | No | Definition/confirmation note | PUBLIC_OK |
| data_quality_status | enum text | Yes | quality status | PUBLIC_OK |
| source_reference | text | No | Traceability | INTERNAL_BY_DEFAULT |

Example:

```csv
WRK-000003,MAS-BRICK,Brick Masonry in Cement Mortar,Masonry,Brickwork,cum
```

## 7. project_work_items.csv

Purpose: project-specific BOQ and execution tracking. The current file has no
data rows because the source BOQ-to-project association is unknown.

Primary key: `project_work_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| project_work_id | uuid-like text | Yes for a row | `PWI-000001` | INTERNAL_BY_DEFAULT |
| project_id | uuid-like text | Yes for a row | FK → projects | PUBLIC_OK |
| work_id | uuid-like text | Yes for a row | FK → work_catalog | PUBLIC_OK |
| source_group_id | text | No | Original BOQ group | INTERNAL_BY_DEFAULT |
| source_sn | text | No | Original BOQ SN | INTERNAL_BY_DEFAULT |
| description_override | text | No | Project-specific override | PUBLIC_OK when approved |
| unit | enum text | No | Preserve source unit | PUBLIC_OK |
| no | numeric | No | Source No concept | INTERNAL_BY_DEFAULT |
| planned_quantity | numeric | No | Non-negative | INTERNAL_BY_DEFAULT |
| completed_quantity | numeric | No | Non-negative | INTERNAL_BY_DEFAULT |
| remaining_quantity | numeric | No | planned − completed | INTERNAL_BY_DEFAULT |
| rate_npr | numeric | No | Plain numeric NPR | SENSITIVE |
| amount_npr | numeric | No | Plain numeric NPR | SENSITIVE |
| factor | numeric | No | Preserve source only | INTERNAL_BY_DEFAULT |
| factor_definition | text | Required if factor exists | `TO_BE_CONFIRMED` | INTERNAL_BY_DEFAULT |
| remarks | text | No | Public-safe text only | INTERNAL_BY_DEFAULT |
| work_status | enum text | Yes for a row | controlled work status | PUBLIC_OK |
| progress_percent | numeric | No | completed/planned × 100 | PUBLIC_OK when approved |
| planned_start | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| planned_finish | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| actual_start | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| actual_finish | date | No | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| last_updated | date | No | YYYY-MM-DD | PUBLIC_OK |
| is_public | boolean | Yes for a row | UI display control | PUBLIC_OK |
| data_quality_status | enum text | Yes for a row | quality status | PUBLIC_OK |
| data_quality_issue | text | Required when status ERROR | Traceable explanation | INTERNAL_BY_DEFAULT |
| source_file | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_sheet | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_row | numeric integer | No | Provenance | INTERNAL_BY_DEFAULT |
| source_reference | text | No | Provenance | INTERNAL_BY_DEFAULT |
| imported_at | date | No | Import date | INTERNAL_BY_DEFAULT |
| verified_by | text | No | Verifier | INTERNAL_BY_DEFAULT |
| verification_status | enum text | Yes for a row | UNVERIFIED/VERIFIED | PUBLIC_OK |

Illustrative broken-source treatment:

```text
planned_quantity = blank
data_quality_status = ERROR
data_quality_issue = "Source workbook contains #REF! in quantity"
```

## 8. materials_master.csv

Purpose: reusable material definitions.

Primary key: `material_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| material_id | uuid-like text | Yes | `MAT-000001` | PUBLIC_OK |
| material_code | text | Yes | Unique reusable code | PUBLIC_OK |
| material_name | text | Yes | Master name | PUBLIC_OK |
| material_category | text | Yes | Human category | PUBLIC_OK |
| subcategory | text | No | Human subcategory | PUBLIC_OK |
| default_unit | enum text | Yes | Controlled construction unit | PUBLIC_OK |
| active | boolean | Yes | TRUE/FALSE | PUBLIC_OK |
| notes | text | No | Definition/confirmation note | PUBLIC_OK |
| data_quality_status | enum text | Yes | quality status | PUBLIC_OK |
| source_reference | text | No | Traceability | INTERNAL_BY_DEFAULT |

Example:

```csv
MAT-000001,CEMENT,Cement,Concrete Material,Binder,bag
```

## 9. project_material_inventory.csv

Purpose: project-specific material inventory snapshots. The current file has no
data rows.

Primary key: `inventory_id`

| Field | Type | Required | FK / controlled rule | Privacy |
|---|---|---:|---|---|
| inventory_id | uuid-like text | Yes for a row | `PMI-000001` | INTERNAL_BY_DEFAULT |
| project_id | uuid-like text | Yes for a row | FK → projects | PUBLIC_OK |
| material_id | uuid-like text | Yes for a row | FK → materials_master | PUBLIC_OK |
| quantity_on_site | numeric | Yes for a row | Non-negative | SENSITIVE |
| reserved_quantity | numeric | No | Non-negative | SENSITIVE |
| available_quantity | numeric | No | Snapshot availability | SENSITIVE |
| unit | enum text | Yes for a row | Preserve source unit | INTERNAL_BY_DEFAULT |
| storage_location | text | No | Site location | SENSITIVE |
| condition | enum text | Yes for a row | controlled material condition | INTERNAL_BY_DEFAULT |
| as_of_date | date | Yes for a row | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| last_updated | date | Yes for a row | YYYY-MM-DD | INTERNAL_BY_DEFAULT |
| remarks | text | No | Internal/public-safe note | INTERNAL_BY_DEFAULT |
| is_public | boolean | Yes for a row | UI display control | PUBLIC_OK |
| data_quality_status | enum text | Yes for a row | quality status | PUBLIC_OK |
| data_quality_issue | text | Required when status ERROR | Explanation | INTERNAL_BY_DEFAULT |
| source_file | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_sheet | text | No | Provenance | INTERNAL_BY_DEFAULT |
| source_row | numeric integer | No | Provenance | INTERNAL_BY_DEFAULT |
| source_reference | text | No | Provenance | INTERNAL_BY_DEFAULT |
| imported_at | date | No | Import date | INTERNAL_BY_DEFAULT |
| verified_by | text | No | Verifier | INTERNAL_BY_DEFAULT |
| verification_status | enum text | Yes for a row | UNVERIFIED/VERIFIED | PUBLIC_OK |

Illustrative only, not a current row:

```csv
PMI-009901,PRJ-009901,MAT-000001,125,20,105,bag,Store A,GOOD,2026-07-26
```

## Controlled values

The authoritative arrays live in `map-config.json`.

### Project sector

```text
PRIVATE
GOVERNMENT_PUBLIC
OTHER
```

### Implementation mechanism

```text
PRIVATE_DIRECT
PRIVATE_CONTRACT
GOVERNMENT_CONTRACTOR_CONTRACT
GOVERNMENT_USER_COMMITTEE
OTHER
```

### Work status

```text
NOT_STARTED
IN_PROGRESS
COMPLETED
ON_HOLD
BLOCKED
NOT_APPLICABLE
```

### Current unit set

```text
cum
sqm
rm
kg
bag
no
L/S
```

Do not silently convert a source unit. Add a reviewed unit to the controlled
set only when genuinely required.
