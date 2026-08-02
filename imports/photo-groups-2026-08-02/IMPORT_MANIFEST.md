# Photo Group Data Import Manifest

## Import batch

- Import batch date: `2026-08-02`
- Development branch: `v1.2-project-data-integration`
- Parent development branch: `v1.2-operational-map`
- Stable release protected: `v1.1.0`
- Source groups: `GRP001` through `GRP032`

## Purpose

This manifest defines how the reviewed candidate files in this folder will be
migrated into the normalized application data.

Files ending in `_candidate` are review and migration inputs.

They are not loaded directly by the public map.

## Source and audit files

| File | Purpose | Loaded by public map |
|---|---|---|
| `README.md` | Import decisions and warnings | No |
| `source_groups_raw.csv` | Untouched original 32-row source dataset | No |
| `source_groups_resolved.csv` | Cleaned and classified source records | No |
| `IMPORT_MANIFEST.md` | Migration instructions and file mapping | No |

## Candidate-to-canonical mapping

| Candidate file | Intended canonical destination | Action |
|---|---|---|
| `projects_candidate.csv` | `projects.csv` | Replace after schema and validation updates |
| `organizations_candidate.csv` | `organizations.csv` | Append municipality and ward organizations |
| `project_parties_candidate.csv` | `project_parties.csv` | Append temporary contractor relationships |
| `project_funding_candidate.csv` | `project_funding.csv` | Append ward-budget funding relationships |
| `project_components_candidate.csv` | `project_components.csv` | Create new canonical table |
| `project_source_links_candidate.csv` | `project_source_links.csv` | Create new canonical table |
| `project_opportunities_candidate.csv` | `project_opportunities.csv` | Create new canonical table |
| `organization_locations_candidate.csv` | `organization_locations.csv` | Create new canonical table |
| `project_publication_settings_candidate.csv` | `project_publication_settings.csv` | Create new canonical table |

## Existing project protections

The following identifiers must not be changed:

- `PRJ-000001` through `PRJ-000007`
- `REB-001`
- `FBL-001` through `FBL-006`
- `P001` through `P007`

New project identifiers begin at:

- Global project ID: `PRJ-000008`
- Fishtail project code: `FBL-007`

New projects do not receive legacy `P` codes.

## Duplicate prevention

The following source groups link to existing projects and must not create new
project rows:

| Source group | Existing project |
|---|---|
| `GRP014` | `PRJ-000005` |
| `GRP016` | `PRJ-000003` |
| `GRP020` | `PRJ-000007` |
| `GRP021` | `PRJ-000004` |

## Project structures

### Firke Pool Road and Drain Works

One project:

`PRJ-000011`

Components:

- Road Works
- Drain Works

### Bhalam 200 m Road

One project:

`PRJ-000024`

Components:

- Segment 1
- Segment 2
- Segment 3

### Bhalam River Works

Separate projects:

- `PRJ-000025` — Phase 1
- `PRJ-000026` — Gabion Mesh Phase 2

### Bhalam Park

Separate projects:

- `PRJ-000027` — Phase 1
- `PRJ-000028` — Phase 2

## Special records

### Bachi and Ama Foundation

- Record type: Opportunity
- Status: `NOT_AWARDED`
- Destination: `project_opportunities.csv`
- Must not be inserted into `projects.csv`

### Fishtail Builders Office

- Record type: Organization location
- Destination: `organization_locations.csv`
- Must not be inserted into `projects.csv`

### Fabin Gurung Enterprise Portfolio

- Record type: Portfolio reference
- Not currently a construction project or registered organization record
- Remains in the staging dataset only

### Fabin Gurung

- Record type: Person reference
- Must not be inserted into `projects.csv`

## Temporary contractor rule

Fishtail Builders Pvt Ltd is currently assigned as the temporary main contractor
for the proposed projects.

These relationships are intentionally marked:

`data_quality_status = WARNING`

They must remain replaceable when verified legal-contractor information becomes
available.

## Coordinate warning

The following records currently share:

`28.2612297, 83.9939523`

- Bhalam Park Phase 1
- Bhalam Park Phase 2
- Bachi and Ama Foundation
- Fishtail Builders Office

The office and opportunity coordinates require later verification.

No coordinate should be silently changed or invented.

## Publication rules

Publicly approved project fields include:

- project name
- coordinates
- status
- ward number
- project sector
- implementation method
- contractor
- executing-company role
- general work summary

Contract amount visibility and material-quantity visibility remain individually
selectable.

## Required implementation order

1. Preserve all import and audit files.
2. Update the validator for the expanded schema.
3. Create the new canonical tables.
4. Append municipality and ward organizations.
5. Replace the canonical project dataset with the validated candidate dataset.
6. Append project-party and project-funding relationships.
7. Update `map-config.json`.
8. Update the frontend data loader.
9. Add marker shapes and project-function icons.
10. Add clustering for nearby or overlapping locations.
11. Test desktop and mobile layouts.
12. Review the data-integration branch.
13. Merge into `v1.2-operational-map` only after validation.
14. Do not merge into `main` until the full v1.2 release is approved.
