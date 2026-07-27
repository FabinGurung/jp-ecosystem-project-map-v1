# Simple Data Entry Guide

This guide is for a site engineer, manager, or office staff member who does not
need to know relational-database terminology.

## First choose what you are updating

| I want to… | Edit this file |
|---|---|
| Add or update a mapped project | `projects.csv` |
| Add a company, ward office, committee, or supplier | `organizations.csv` |
| Say who is contractor/client/manager/etc. | `project_parties.csv` |
| Record a verified funding source | `project_funding.csv` |
| Add a reusable work description | `work_catalog.csv` |
| Assign and track work for one project | `project_work_items.csv` |
| Add a reusable material | `materials_master.csv` |
| Record one approved inventory snapshot | `project_material_inventory.csv` |

## The three project codes

For every existing project, do not change:

- `project_id` — system identity
- `company_project_code` — code shown on the map
- `legacy_project_code` — old P001-style identity

For a new project:

1. Choose the next unused global number.
2. Use the executing company code.
3. Use the next unused company sequence.
4. Use a legacy code only if the project already had one.

Do not reuse a deleted project’s code.

## If you do not know a value

Leave it blank.

Do not guess:

- private/government sector
- client
- government office
- ward
- funding body
- project manager
- site engineer
- dates
- progress
- BOQ quantities
- material stock

The validator warning is safer than a wrong fact.

## Government/User Committee entry

Use:

```text
project_sector = GOVERNMENT_PUBLIC
implementation_mechanism = GOVERNMENT_USER_COMMITTEE
```

Then:

1. Add the real committee to `organizations.csv`.
2. Use `organization_type=USER_COMMITTEE`.
3. Add a project-party relationship with role `IMPLEMENTING_BODY` or
   `USER_COMMITTEE`, according to the verified role.
4. Add the ward office separately as `ADMINISTRATIVE_BODY` if applicable.
5. Add funding separately in `project_funding.csv`.

Do not create a new mechanism called Samiti.

## Work entry

1. Search `work_catalog.csv` for the work.
2. If it exists, use its `work_id`.
3. If it does not exist, add one new master row first.
4. In `project_work_items.csv`, use the global `project_id`.
5. Preserve the source unit.
6. Enter planned and completed quantity only when verified.
7. Calculate:

   `remaining = planned - completed`

8. Calculate progress only when planned quantity is above zero:

   `progress = completed / planned × 100`

9. Use one controlled work status.
10. Keep rates and amounts blank in this public repository unless publication
    is explicitly approved.

## If Excel shows #REF!

Do not paste `#REF!` into the numeric CSV field.

Use:

```text
numeric value = blank
data_quality_status = ERROR
data_quality_issue = Source workbook contains #REF! in quantity
```

Also fill the source file, sheet, row, or reference when known.

## Material inventory entry

Only enter a snapshot that is approved for public release.

1. Find the material in `materials_master.csv`.
2. Use the global `project_id`.
3. Preserve the site unit.
4. Enter the as-of date.
5. Enter condition.
6. Enter storage location only if public disclosure is safe.
7. Remember that the CSV itself is downloadable.

## Final check

Run:

```bash
python scripts/validate_data.py
```

Fix all errors. Review warnings. A warning may be accepted when the source fact
is genuinely unknown.
