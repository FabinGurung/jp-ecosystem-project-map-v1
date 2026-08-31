# M02 — Progress Report Data Contract v1.0

Status: PREPARED MVP / PUBLIC-SAFE SYNTHETIC SAMPLE

## Purpose
M02 records the physical-progress observation layer for JP Site Operations. It answers what work is completed, current, blocked/on hold, or not yet started, and carries an explicit evidence note/reference for every reported work item.

M02 is deliberately separate from M01 Schedule/Gantt. M01 is the plan/date/milestone authority for the Morning Map module layer; M02 is the observed/manual progress snapshot. Both join through stable `canonical_project_id`, `company_project_code`, and `work_id` values.

## Authority boundary
- This module is a bounded display/input contract, not a replacement for project records or private evidence in Drive.
- The committed sample is synthetic and public-safe.
- Evidence references in the public repository may point only to public-safe identifiers or sanitized references. Private Drive URLs/IDs, personal contacts, supplier balances, detailed BOQ rates, contracts, credentials, or restricted evidence must not be exposed.
- UNKNOWN facts remain unknown. Do not infer progress from dates, photos, schedule position, or payment records unless the evidence has been explicitly reviewed and classified.
- M02 does not change M01 dates or status automatically.

## File
`assets/data/m02_progress_report.json`

## Project fields
- `canonical_project_id` — canonical PRJ identifier.
- `company_project_code` — human-facing company code used by the map detail panel.
- `project_name`
- `update_date` — ISO date for the progress snapshot.
- `source_status` — e.g. `SYNTHETIC`, `MANUAL_CONFIRMED`, `MANUAL_UNVERIFIED`.
- `progress_updates` — bounded work-level progress observations.

## Required progress-update fields
- `work_id`
- `work_name`
- `progress_percent` — 0–100.
- `status` — `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `ON_HOLD`, `BLOCKED`, or `NOT_APPLICABLE`.
- `update_date` — ISO date for the observation.
- `evidence_note` — concise human-readable basis/limitation.
- `evidence_reference` — public-safe reference token or sanitized pointer. Use `UNKNOWN` if no safe reference exists.

This implements the live Modular MVP contract:
`project_id + work_id + progress_percent + status + update_date + evidence note/reference`.

## Rendering rules
- Current = `IN_PROGRESS`, `BLOCKED`, or `ON_HOLD` observations.
- Recently completed = latest `COMPLETED` observations by `update_date`, max five.
- Next/not started = `NOT_STARTED` observations in input order, max five.
- The progress bar renders only the stored `progress_percent`; no browser-side inference or solver is allowed.
- M02 observes only the selected project code (`detail-code`). It must not observe its own `panel-works` render target, preventing self-triggered mutation loops.

## M01 relationship
For the synthetic MVP sample, every M02 `work_id` must exist in the M01 Schedule/Gantt sample and retain the same `work_name`. This regression rule protects the shared-identifier contract while the modules remain separate.

Future real snapshots may contain work that is not scheduled yet, but such cases must be explicitly classified and reconciled rather than silently renamed or merged.

## Manual nightly operating pattern
1. User provides site update facts/messages/photos/direct instructions.
2. ChatGPT separates confirmed observations from unknown/unverified claims.
3. Private evidence remains in Drive; only a safe evidence note/reference enters the public M02 payload.
4. ChatGPT prepares the bounded Drive payload + manifest.
5. User runs the governed JP Colab publisher once.
6. ChatGPT independently verifies GitHub scope/bytes/CI/runtime before freezing the published checkpoint.
