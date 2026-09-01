# M03 — Material Quantity / Readiness Data Contract v1.0

Status: PREPARED MVP / PUBLIC-SAFE SYNTHETIC UI EVIDENCE

## Purpose
M03 records material quantity/readiness for current and next work. It answers what material is known to be ready, short, missing, not applicable, or still unknown.

The governing rule is strict: **do not invent quantities; UNKNOWN remains UNKNOWN**.

M03 is separate from M01 Schedule/Gantt, M02 Progress Report, M04 Equipment/Resource Readiness, procurement, and private inventory/accounting authorities. Shared identifiers allow the modules to meet at the Morning Map without forcing them into one database.

## Authority boundary
- M03 is a bounded display/input contract, not the canonical inventory ledger.
- `project_material_inventory.csv` remains an existing repository table and is currently empty; M03 does not populate it with synthetic values.
- The committed MVP sample is explicitly synthetic/public-safe and reuses only already-existing Site Operations demo evidence.
- Schedule dates, work progress, supplier payments, purchase records, photos, or old demo labels must not be used to infer a live stock quantity.
- Equipment, tools, scaffolding, mixer and labor/resource readiness belong to M04 and are excluded from M03.
- Private supplier balances, BOQ rates, purchase orders, restricted stock, credentials, contacts, contracts, private Drive URLs/IDs, and non-public evidence must not enter the public repository.

## File
`assets/data/m03_material_readiness.json`

## Project fields
- `canonical_project_id`
- `company_project_code`
- `project_name`
- `update_date`
- `source_status`
- `work_materials`

## Material-readiness fields
- `work_id`
- `work_name`
- `material_id` — canonical material identifier when a defensible mapping exists; otherwise `null`.
- `material_name`
- `required_quantity` — numeric or `null`.
- `available_quantity` — numeric or `null`.
- `unit` — canonical comparable unit or `null`.
- `readiness_status`
- `evidence_note`
- `evidence_reference`

## Allowed readiness states
- `READY` — required and available quantities are known in a comparable unit, and available >= required.
- `SHORT` — required and available quantities are known in a comparable unit, and 0 < available < required.
- `MISSING` — required quantity is known and positive, available quantity is known as 0 in the same unit.
- `UNKNOWN` — any fact needed for a safe readiness decision is missing, unverified, unmapped, or unit-incompatible.
- `NOT_APPLICABLE` — the material is explicitly confirmed not applicable to the work.

The browser renders the stored readiness state. It does not calculate or invent a status from partial evidence.

## UNKNOWN rules
UNKNOWN is mandatory when any of these applies:
1. required quantity is not confirmed;
2. available quantity is not confirmed;
3. required and available units cannot be compared safely;
4. a canonical material mapping is unresolved and the quantity would depend on that mapping;
5. the evidence is insufficient to support a readiness classification.

Unknown numeric fields stay `null`. Do not replace `null` with 0. A zero is a factual quantity and may only be stored when the source explicitly supports zero.

## Synthetic MVP evidence
The initial sample reuses material-only rows that already existed in the legacy synthetic Site Operations prototype for `FBL-005`. Those values remain synthetic and are not live inventory.

Where the old prototype used an item/unit that cannot be reconciled safely with the current material master, M03 deliberately quarantines the numeric value and stores `UNKNOWN` instead. Examples include tile adhesive without a canonical material ID and Timber/Paint rows whose current master units are unresolved.

## Module relationships
M03 joins M01/M02 through:
`canonical_project_id + company_project_code + work_id`.

It joins the material master through `material_id` when available.

M01 emits the stable browser event:
`jp:m01-work-selected` with `detail.workId`.
M03 listens to that event and opens the Resources tab for the selected work. If the selected work has no M03 record, the UI explicitly renders UNKNOWN rather than falling back to another work.

The legacy synthetic material/equipment prototype is suppressed while M03 is active so the Resources tab has one material authority. M04 will later replace the equipment/resource portion separately.

## Manual operating pattern
1. User supplies confirmed material facts or a source that can be reviewed.
2. ChatGPT separates confirmed quantities from unknown/unverified claims.
3. Units/material IDs are reconciled only when defensible.
4. Private evidence stays in Drive; only public-safe notes/tokens enter a public M03 payload.
5. Unknowns remain `null` + `UNKNOWN`.
6. A bounded Drive payload and manifest are prepared.
7. The governed Colab publisher is run once by the user.
8. ChatGPT independently verifies GitHub scope/bytes/CI/runtime before freezing M03.
