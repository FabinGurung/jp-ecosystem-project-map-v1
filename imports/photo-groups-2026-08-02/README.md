# Photo Group Project Data Import — 2026-08-02

## Purpose

This folder records the source data, cleaning decisions, review findings, and
migration evidence for project information originally organized as photo groups.

The source dataset contained 32 records identified as `GRP001` through `GRP032`.

## Important

Files inside this folder are staging and audit records.

They are not loaded directly by the public map application.

Canonical public application data remains in the normalized repository files,
including:

- `projects.csv`
- `organizations.csv`
- `project_parties.csv`
- `project_funding.csv`
- `project_work_items.csv`
- `project_material_inventory.csv`

## Confirmed decisions

- Existing project IDs must remain unchanged.
- `GRP014` is an alias/source record for `PRJ-000005` / `FBL-004`.
- `GRP016` matches `PRJ-000003` / `FBL-002`.
- `GRP020` matches `PRJ-000007` / `FBL-006`.
- `GRP021` matches `PRJ-000004` / `FBL-003`.
- Bhalam 200 m Road is one project with three road segments.
- Bhalam River Phase 1 and Phase 2 are separate projects.
- Bhalam Park Phase 1 and Phase 2 are separate projects.
- Firke Pool Road and Drain is one project with road and drain components.
- Bachi and Ama Foundation is a public `NOT_AWARDED` opportunity.
- Fishtail Builders Office is an organization location, not a construction project.
- Fishtail Builders Pvt Ltd is temporarily recorded as the main contractor for
  the proposed projects.
- Temporary contractor assignments must remain replaceable because the verified
  legal contractors may be entered later.
- Government projects are funded from their respective Pokhara ward budgets
  unless a later verified source says otherwise.
- Prithvi Mandi is classified as a government User Committee project.
- Existing residential projects are classified as private residential projects.

## Public-data decisions

The public map may show:

- project name
- coordinates
- project status
- ward number
- project sector
- implementation method
- contractor
- company role
- general work description

Contract amounts and material quantities must be individually configurable as
public or private.

## Coordinate warning

The supplied coordinates for the following records are currently identical:

- Bhalam Park Phase 1
- Bhalam Park Phase 2
- Bachi and Ama Foundation
- Fishtail Builders Office

The shared point is:

`28.2612297, 83.9939523`

This must remain flagged for verification, especially because the office source
group was associated with Ward 4 while the Bhalam records are associated with
Ward 20.

## Development workflow

All data integration work must be completed on:

`v1.2-project-data-integration`

Do not merge this branch directly into `main`.

The intended path is:

1. Prepare and validate the data integration.
2. Review the map and normalized relationships.
3. Merge into `v1.2-operational-map`.
4. Test the complete v1.2 candidate.
5. Merge into `main` only after final approval.
