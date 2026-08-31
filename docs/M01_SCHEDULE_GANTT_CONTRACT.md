# M01 — Schedule / Gantt Data Contract v1.0

Status: PREPARED MVP / PUBLIC-SAFE SYNTHETIC SAMPLE

## Purpose
M01 is the first independently testable JP Site Operations feature module. It provides a manually maintainable schedule/progress snapshot that the Morning Map can render without requiring Google Forms, AppSheet, Apps Script, Supabase, Slack, or Discord integration.

## Authority boundary
- This module is a display/input contract, not a replacement for project records in Drive.
- The committed sample is synthetic and public-safe.
- Real private quantities, contracts, supplier balances, private contacts, drawings, credentials, or restricted stock must not be committed to the public repository.
- UNKNOWN facts stay unknown; do not invent progress or dates.

## File
`assets/data/m01_schedule_gantt.json`

## Project fields
- `canonical_project_id` — canonical PRJ identifier.
- `company_project_code` — human-facing company code used by the map detail panel.
- `project_name`
- `overall_progress_percent` — manually supplied project-level progress for this snapshot.
- `update_date` — ISO date.
- `source_status` — e.g. SYNTHETIC, MANUAL_CONFIRMED, MANUAL_UNVERIFIED.

## Work fields
- `work_id`
- `work_name`
- `sequence`
- `planned_start` / `planned_finish` — ISO dates.
- `actual_finish` — optional ISO date.
- `status` — `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `ON_HOLD`, `BLOCKED`, or `NOT_APPLICABLE`.
- `progress_percent` — 0–100.
- `milestone`
- `note`

## Rendering rules
- Current work = first `IN_PROGRESS`; otherwise first `BLOCKED`/`ON_HOLD`; otherwise first `NOT_STARTED`.
- Next 5 = next `NOT_STARTED` rows by sequence.
- Previous 5 = latest `COMPLETED` rows by actual/planned finish date.
- Milestones are derived from work status.
- Gantt geometry is derived from planned dates at render time; stored pixel/percentage geometry is prohibited.

## Manual nightly operating pattern
1. User provides nightly facts/messages/screenshots to ChatGPT.
2. ChatGPT structures only confirmed/public-safe M01 values.
3. ChatGPT prepares a bounded Drive payload + manifest.
4. User runs the governed JP Colab publisher once.
5. ChatGPT independently reads back the GitHub commit before marking the module snapshot published.

The heavier Google operational data-plane architecture remains a frozen fallback and is restored only when the manual-friction threshold is met.

## M01 → Resources bridge

Schedule activity selection is exposed through the browser event `jp:m01-work-selected` with `detail.workId`. The existing synthetic Resources prototype listens for that event and opens the Resources tab for the selected work when a matching resource demo exists. This small event is the stable integration surface; M01 must not depend on legacy schedule DOM buttons being present.
