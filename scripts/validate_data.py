#!/usr/bin/env python3
"""Validate the public JP Ecosystem v1.2 CSV model.

The validator checks structure, controlled values, primary keys, foreign keys,
coordinates, dates, numeric values, spreadsheet-error tokens, public-data
hygiene, and calculations that are explicitly defined. It deliberately does
not use Factor to calculate BOQ amounts because that business rule is still
TO_BE_CONFIRMED.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable


SPREADSHEET_ERRORS = {"#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?", "#NUM!"}
TRUE_VALUES = {"true", "1", "yes", "y"}
FALSE_VALUES = {"false", "0", "no", "n"}
DATE_FIELDS = {
    "start_date",
    "target_completion_date",
    "actual_completion_date",
    "last_updated",
    "planned_start",
    "planned_finish",
    "actual_start",
    "actual_finish",
    "funding_date",
    "as_of_date",
    "imported_at",
    "end_date",
}
ALLOWED_UNITS = {"cum", "sqm", "rm", "kg", "bag", "no", "L/S"}
FORBIDDEN_PUBLIC_HEADERS = {
    "phone",
    "phone_number",
    "mobile",
    "mobile_number",
    "email",
    "email_address",
    "citizenship_number",
    "bank_account",
    "bank_account_number",
    "password",
    "api_key",
    "secret",
    "access_token",
}

PATTERNS = {
    "project_id": re.compile(r"^PRJ-\d{6}$"),
    "company_project_code": re.compile(r"^[A-Z0-9]{2,10}-\d{3,6}$"),
    "legacy_project_code": re.compile(r"^P\d{3,6}$"),
    "organization_id": re.compile(r"^ORG-\d{6}$"),
    "person_id": re.compile(r"^PER-\d{6}$"),
    "project_party_id": re.compile(r"^PPA-\d{6}$"),
    "project_funding_id": re.compile(r"^PFD-\d{6}$"),
    "work_id": re.compile(r"^WRK-\d{6}$"),
    "project_work_id": re.compile(r"^PWI-\d{6}$"),
    "material_id": re.compile(r"^MAT-\d{6}$"),
    "inventory_id": re.compile(r"^PMI-\d{6}$"),
}

REQUIRED_HEADERS = {
    "projects": {
        "project_id",
        "company_project_code",
        "legacy_project_code",
        "project_name",
        "display_name",
        "project_sector",
        "government_level",
        "implementation_mechanism",
        "executing_company_id",
        "latitude",
        "longitude",
        "status",
        "physical_progress_percent",
        "financial_progress_percent",
        "start_date",
        "target_completion_date",
        "actual_completion_date",
        "last_updated",
        "latest_update",
        "photo_url",
        "details_url",
        "public_notes",
        "is_public",
        "data_quality_status",
        "source_reference",
        "verification_status",
    },
    "organizations": {
        "organization_id",
        "organization_code",
        "organization_name",
        "organization_type",
        "parent_organization_id",
        "government_level",
        "ward_number",
        "municipality_name",
        "district",
        "province",
        "registration_number",
        "active",
        "notes",
        "is_public",
        "data_quality_status",
        "source_reference",
    },
    "people": {
        "person_id",
        "person_code",
        "display_name",
        "active",
        "notes",
        "is_public",
        "data_quality_status",
        "source_reference",
    },
    "project_parties": {
        "project_party_id",
        "project_id",
        "party_entity_type",
        "party_id",
        "role",
        "is_primary",
        "start_date",
        "end_date",
        "remarks",
        "is_public",
        "data_quality_status",
        "source_reference",
    },
    "project_funding": {
        "project_funding_id",
        "project_id",
        "funding_party_id",
        "funding_type",
        "approved_amount_npr",
        "contribution_percent",
        "funding_date",
        "remarks",
        "is_public",
        "data_quality_status",
        "source_reference",
    },
    "work_catalog": {
        "work_id",
        "work_code",
        "description",
        "category",
        "subcategory",
        "default_unit",
        "active",
        "notes",
        "data_quality_status",
        "source_reference",
    },
    "project_work_items": {
        "project_work_id",
        "project_id",
        "work_id",
        "source_group_id",
        "source_sn",
        "description_override",
        "unit",
        "no",
        "planned_quantity",
        "completed_quantity",
        "remaining_quantity",
        "rate_npr",
        "amount_npr",
        "factor",
        "factor_definition",
        "remarks",
        "work_status",
        "progress_percent",
        "planned_start",
        "planned_finish",
        "actual_start",
        "actual_finish",
        "last_updated",
        "is_public",
        "data_quality_status",
        "data_quality_issue",
        "source_reference",
        "verification_status",
    },
    "materials_master": {
        "material_id",
        "material_code",
        "material_name",
        "material_category",
        "subcategory",
        "default_unit",
        "active",
        "notes",
        "data_quality_status",
        "source_reference",
    },
    "project_material_inventory": {
        "inventory_id",
        "project_id",
        "material_id",
        "quantity_on_site",
        "reserved_quantity",
        "available_quantity",
        "unit",
        "storage_location",
        "condition",
        "as_of_date",
        "last_updated",
        "remarks",
        "is_public",
        "data_quality_status",
        "data_quality_issue",
        "source_reference",
        "verification_status",
    },
}


@dataclass(frozen=True)
class Issue:
    level: str
    file_name: str
    line_number: int | None
    message: str

    def __str__(self) -> str:
        location = self.file_name
        if self.line_number is not None:
            location += f":{self.line_number}"
        return f"{self.level}: {location}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "ERROR"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "WARNING"]

    def error(
        self, file_name: str, message: str, line_number: int | None = None
    ) -> None:
        self.issues.append(Issue("ERROR", file_name, line_number, message))

    def warning(
        self, file_name: str, message: str, line_number: int | None = None
    ) -> None:
        self.issues.append(Issue("WARNING", file_name, line_number, message))


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv(
    path: Path, dataset_name: str, result: ValidationResult
) -> list[dict[str, str]]:
    if not path.exists():
        result.error(path.name, "required data file is missing")
        return []

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if not headers:
            result.error(path.name, "header row is missing")
            return []
        if len(headers) != len(set(headers)):
            duplicates = sorted(
                {header for header in headers if headers.count(header) > 1}
            )
            result.error(path.name, f"duplicate headers: {duplicates}")
        missing = sorted(REQUIRED_HEADERS[dataset_name] - set(headers))
        if missing:
            result.error(path.name, f"missing required columns: {missing}")
        forbidden = sorted(FORBIDDEN_PUBLIC_HEADERS & {h.lower() for h in headers})
        if forbidden:
            result.error(
                path.name,
                "public data file contains sensitive-contact/secret columns: "
                f"{forbidden}",
            )

        rows = list(reader)
        for line_number, row in enumerate(rows, start=2):
            extra_values = row.get(None)
            if extra_values:
                result.error(
                    path.name,
                    f"row contains {len(extra_values)} more value(s) than headers",
                    line_number,
                )
            for field_name, value in row.items():
                if field_name is None:
                    continue
                if clean(value).upper() in SPREADSHEET_ERRORS:
                    result.error(
                        path.name,
                        f"{field_name} contains spreadsheet error {clean(value)!r}; "
                        "store a blank numeric value and document the issue instead",
                        line_number,
                    )

    result.row_counts[dataset_name] = len(rows)
    return rows


def require_fields(
    rows: Iterable[dict[str, str]],
    fields: Iterable[str],
    file_name: str,
    result: ValidationResult,
) -> None:
    for line_number, row in enumerate(rows, start=2):
        for field_name in fields:
            if not clean(row.get(field_name)):
                result.error(
                    file_name, f"{field_name} is required", line_number
                )


def validate_unique(
    rows: Iterable[dict[str, str]],
    field_name: str,
    file_name: str,
    result: ValidationResult,
) -> set[str]:
    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        value = clean(row.get(field_name))
        if not value:
            continue
        if value in seen:
            result.error(
                file_name,
                f"duplicate {field_name} {value!r}",
                line_number,
            )
        seen.add(value)
    return seen


def validate_pattern(
    rows: Iterable[dict[str, str]],
    field_name: str,
    pattern_name: str,
    file_name: str,
    result: ValidationResult,
) -> None:
    pattern = PATTERNS[pattern_name]
    for line_number, row in enumerate(rows, start=2):
        value = clean(row.get(field_name))
        if value and not pattern.fullmatch(value):
            result.error(
                file_name,
                f"{field_name} has invalid format {value!r}",
                line_number,
            )


def validate_boolean(
    rows: Iterable[dict[str, str]],
    field_name: str,
    file_name: str,
    result: ValidationResult,
) -> None:
    allowed = TRUE_VALUES | FALSE_VALUES
    for line_number, row in enumerate(rows, start=2):
        value = clean(row.get(field_name)).lower()
        if value and value not in allowed:
            result.error(
                file_name,
                f"{field_name} must be TRUE or FALSE",
                line_number,
            )


def validate_controlled(
    rows: Iterable[dict[str, str]],
    field_name: str,
    allowed: set[str],
    file_name: str,
    result: ValidationResult,
    *,
    allow_blank: bool = False,
) -> None:
    for line_number, row in enumerate(rows, start=2):
        value = clean(row.get(field_name))
        if not value and allow_blank:
            continue
        if value not in allowed:
            result.error(
                file_name,
                f"{field_name} {value!r} is not an allowed value",
                line_number,
            )


def number(
    row: dict[str, str],
    field_name: str,
    file_name: str,
    line_number: int,
    result: ValidationResult,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    allow_blank: bool = True,
) -> float | None:
    value = clean(row.get(field_name))
    if not value:
        if not allow_blank:
            result.error(file_name, f"{field_name} is required", line_number)
        return None
    try:
        parsed = float(value)
    except ValueError:
        result.error(
            file_name, f"{field_name} must be a plain numeric value", line_number
        )
        return None
    if not math.isfinite(parsed):
        result.error(file_name, f"{field_name} must be finite", line_number)
        return None
    if minimum is not None and parsed < minimum:
        result.error(
            file_name,
            f"{field_name} must be at least {minimum:g}",
            line_number,
        )
    if maximum is not None and parsed > maximum:
        result.error(
            file_name,
            f"{field_name} must be at most {maximum:g}",
            line_number,
        )
    return parsed


def validate_dates(
    rows: Iterable[dict[str, str]],
    file_name: str,
    result: ValidationResult,
) -> None:
    for line_number, row in enumerate(rows, start=2):
        for field_name in DATE_FIELDS & set(row):
            value = clean(row.get(field_name))
            if not value:
                continue
            try:
                date.fromisoformat(value)
            except ValueError:
                result.error(
                    file_name,
                    f"{field_name} must use YYYY-MM-DD",
                    line_number,
                )


def validate_units(
    rows: Iterable[dict[str, str]],
    field_name: str,
    file_name: str,
    result: ValidationResult,
) -> None:
    for line_number, row in enumerate(rows, start=2):
        value = clean(row.get(field_name))
        if value and value not in ALLOWED_UNITS:
            result.error(
                file_name,
                f"{field_name} {value!r} is not currently supported; "
                f"allowed values are {sorted(ALLOWED_UNITS)}",
                line_number,
            )


def validate_quality_issue(
    rows: Iterable[dict[str, str]],
    file_name: str,
    result: ValidationResult,
) -> None:
    for line_number, row in enumerate(rows, start=2):
        if clean(row.get("data_quality_status")) == "ERROR" and not clean(
            row.get("data_quality_issue")
        ):
            result.error(
                file_name,
                "data_quality_issue is required when data_quality_status is ERROR",
                line_number,
            )


def validate_repository(root: Path) -> ValidationResult:
    result = ValidationResult()
    config_path = root / "map-config.json"
    if not config_path.exists():
        result.error("map-config.json", "configuration file is missing")
        return result

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        result.error("map-config.json", f"invalid JSON: {exc}")
        return result

    if config.get("app_version") not in {"1.2.0-dev", "1.2.0"}:
        result.error(
            "map-config.json",
            "v1.2 package must use app_version 1.2.0-dev or 1.2.0",
        )
    if config.get("data_schema_version") != "2.0.0":
        result.error(
            "map-config.json",
            "normalized primary-key migration requires data_schema_version 2.0.0",
        )

    expected_files = {
        "projects",
        "organizations",
        "people",
        "project_parties",
        "project_funding",
        "work_catalog",
        "project_work_items",
        "materials_master",
        "project_material_inventory",
    }
    configured_files = config.get("data_files", {})
    missing_file_keys = sorted(expected_files - set(configured_files))
    if missing_file_keys:
        result.error(
            "map-config.json",
            f"data_files is missing keys: {missing_file_keys}",
        )
        return result

    datasets = {
        name: read_csv(root / configured_files[name], name, result)
        for name in sorted(expected_files)
    }

    controls = config.get("controlled_values", {})
    statuses = set(config.get("status_styles", {}))
    project_sectors = set(controls.get("project_sectors", []))
    mechanisms = set(controls.get("implementation_mechanisms", []))
    government_levels = set(controls.get("government_levels", []))
    organization_types = set(controls.get("organization_types", []))
    party_entity_types = set(controls.get("party_entity_types", []))
    party_roles = set(controls.get("party_roles", []))
    funding_types = set(controls.get("funding_types", []))
    work_statuses = set(controls.get("work_statuses", []))
    material_conditions = set(controls.get("material_conditions", []))
    quality_statuses = set(controls.get("data_quality_statuses", []))
    verification_statuses = set(controls.get("verification_statuses", []))

    # Organizations
    organizations = datasets["organizations"]
    require_fields(
        organizations,
        {
            "organization_id",
            "organization_code",
            "organization_name",
            "organization_type",
            "active",
            "is_public",
            "data_quality_status",
        },
        configured_files["organizations"],
        result,
    )
    organization_ids = validate_unique(
        organizations,
        "organization_id",
        configured_files["organizations"],
        result,
    )
    validate_unique(
        organizations,
        "organization_code",
        configured_files["organizations"],
        result,
    )
    validate_pattern(
        organizations,
        "organization_id",
        "organization_id",
        configured_files["organizations"],
        result,
    )
    validate_controlled(
        organizations,
        "organization_type",
        organization_types,
        configured_files["organizations"],
        result,
    )
    validate_controlled(
        organizations,
        "government_level",
        government_levels,
        configured_files["organizations"],
        result,
        allow_blank=True,
    )
    validate_controlled(
        organizations,
        "data_quality_status",
        quality_statuses,
        configured_files["organizations"],
        result,
    )
    validate_boolean(
        organizations, "active", configured_files["organizations"], result
    )
    validate_boolean(
        organizations, "is_public", configured_files["organizations"], result
    )
    for line_number, row in enumerate(organizations, start=2):
        parent_id = clean(row.get("parent_organization_id"))
        if parent_id and parent_id not in organization_ids:
            result.error(
                configured_files["organizations"],
                f"parent_organization_id {parent_id!r} does not exist",
                line_number,
            )
        if parent_id and parent_id == clean(row.get("organization_id")):
            result.error(
                configured_files["organizations"],
                "organization cannot be its own parent",
                line_number,
            )
        number(
            row,
            "ward_number",
            configured_files["organizations"],
            line_number,
            result,
            minimum=1,
            maximum=99,
        )

    # People are intentionally allowed to contain zero rows.
    people = datasets["people"]
    require_fields(
        people,
        {
            "person_id",
            "display_name",
            "active",
            "is_public",
            "data_quality_status",
        },
        configured_files["people"],
        result,
    )
    person_ids = validate_unique(
        people, "person_id", configured_files["people"], result
    )
    validate_pattern(
        people,
        "person_id",
        "person_id",
        configured_files["people"],
        result,
    )
    validate_boolean(people, "active", configured_files["people"], result)
    validate_boolean(people, "is_public", configured_files["people"], result)
    validate_controlled(
        people,
        "data_quality_status",
        quality_statuses,
        configured_files["people"],
        result,
    )

    # Projects
    projects = datasets["projects"]
    if not projects:
        result.error(configured_files["projects"], "must contain project rows")
    require_fields(
        projects,
        {
            "project_id",
            "company_project_code",
            "legacy_project_code",
            "project_name",
            "display_name",
            "executing_company_id",
            "latitude",
            "longitude",
            "status",
            "last_updated",
            "is_public",
            "data_quality_status",
            "verification_status",
        },
        configured_files["projects"],
        result,
    )
    project_ids = validate_unique(
        projects, "project_id", configured_files["projects"], result
    )
    validate_unique(
        projects,
        "company_project_code",
        configured_files["projects"],
        result,
    )
    validate_unique(
        projects,
        "legacy_project_code",
        configured_files["projects"],
        result,
    )
    for field_name in (
        "project_id",
        "company_project_code",
        "legacy_project_code",
    ):
        validate_pattern(
            projects,
            field_name,
            field_name,
            configured_files["projects"],
            result,
        )
    validate_controlled(
        projects,
        "status",
        statuses,
        configured_files["projects"],
        result,
    )
    validate_controlled(
        projects,
        "project_sector",
        project_sectors,
        configured_files["projects"],
        result,
        allow_blank=True,
    )
    validate_controlled(
        projects,
        "government_level",
        government_levels,
        configured_files["projects"],
        result,
        allow_blank=True,
    )
    validate_controlled(
        projects,
        "implementation_mechanism",
        mechanisms,
        configured_files["projects"],
        result,
        allow_blank=True,
    )
    validate_controlled(
        projects,
        "data_quality_status",
        quality_statuses,
        configured_files["projects"],
        result,
    )
    validate_controlled(
        projects,
        "verification_status",
        verification_statuses,
        configured_files["projects"],
        result,
    )
    validate_boolean(projects, "is_public", configured_files["projects"], result)
    validate_dates(projects, configured_files["projects"], result)

    organization_by_id = {
        clean(row.get("organization_id")): row for row in organizations
    }
    for line_number, row in enumerate(projects, start=2):
        latitude = number(
            row,
            "latitude",
            configured_files["projects"],
            line_number,
            result,
            minimum=-90,
            maximum=90,
            allow_blank=False,
        )
        longitude = number(
            row,
            "longitude",
            configured_files["projects"],
            line_number,
            result,
            minimum=-180,
            maximum=180,
            allow_blank=False,
        )
        del latitude, longitude
        for field_name in (
            "physical_progress_percent",
            "financial_progress_percent",
        ):
            number(
                row,
                field_name,
                configured_files["projects"],
                line_number,
                result,
                minimum=0,
                maximum=100,
            )

        company_id = clean(row.get("executing_company_id"))
        company = organization_by_id.get(company_id)
        if company_id and not company:
            result.error(
                configured_files["projects"],
                f"executing_company_id {company_id!r} does not exist",
                line_number,
            )
        elif company:
            expected_prefix = f"{clean(company.get('organization_code'))}-"
            code = clean(row.get("company_project_code"))
            if code and not code.startswith(expected_prefix):
                result.error(
                    configured_files["projects"],
                    f"company_project_code {code!r} must start with "
                    f"{expected_prefix!r} for executing company {company_id}",
                    line_number,
                )

        sector = clean(row.get("project_sector"))
        mechanism = clean(row.get("implementation_mechanism"))
        government_level = clean(row.get("government_level"))
        if not sector:
            result.warning(
                configured_files["projects"],
                "project_sector is not entered; left blank instead of inventing it",
                line_number,
            )
        if not mechanism:
            result.warning(
                configured_files["projects"],
                "implementation_mechanism is not entered; left blank instead of inventing it",
                line_number,
            )
        if mechanism.startswith("GOVERNMENT_") and sector != "GOVERNMENT_PUBLIC":
            result.error(
                configured_files["projects"],
                "government implementation requires project_sector "
                "GOVERNMENT_PUBLIC",
                line_number,
            )
        if government_level and sector != "GOVERNMENT_PUBLIC":
            result.warning(
                configured_files["projects"],
                "government_level is populated while project_sector is not "
                "GOVERNMENT_PUBLIC",
                line_number,
            )

    # Project-party relationships
    project_parties = datasets["project_parties"]
    require_fields(
        project_parties,
        {
            "project_party_id",
            "project_id",
            "party_entity_type",
            "party_id",
            "role",
            "is_primary",
            "is_public",
            "data_quality_status",
        },
        configured_files["project_parties"],
        result,
    )
    validate_unique(
        project_parties,
        "project_party_id",
        configured_files["project_parties"],
        result,
    )
    validate_pattern(
        project_parties,
        "project_party_id",
        "project_party_id",
        configured_files["project_parties"],
        result,
    )
    validate_controlled(
        project_parties,
        "party_entity_type",
        party_entity_types,
        configured_files["project_parties"],
        result,
    )
    validate_controlled(
        project_parties,
        "role",
        party_roles,
        configured_files["project_parties"],
        result,
    )
    validate_controlled(
        project_parties,
        "data_quality_status",
        quality_statuses,
        configured_files["project_parties"],
        result,
    )
    validate_boolean(
        project_parties,
        "is_primary",
        configured_files["project_parties"],
        result,
    )
    validate_boolean(
        project_parties,
        "is_public",
        configured_files["project_parties"],
        result,
    )
    validate_dates(project_parties, configured_files["project_parties"], result)
    project_by_id = {clean(row.get("project_id")): row for row in projects}
    for line_number, row in enumerate(project_parties, start=2):
        project_id = clean(row.get("project_id"))
        if project_id not in project_ids:
            result.error(
                configured_files["project_parties"],
                f"project_id {project_id!r} does not exist",
                line_number,
            )
        entity_type = clean(row.get("party_entity_type"))
        party_id = clean(row.get("party_id"))
        if entity_type == "ORGANIZATION" and party_id not in organization_ids:
            result.error(
                configured_files["project_parties"],
                f"organization party_id {party_id!r} does not exist",
                line_number,
            )
        if entity_type == "PERSON" and party_id not in person_ids:
            result.error(
                configured_files["project_parties"],
                f"person party_id {party_id!r} does not exist",
                line_number,
            )
        if (
            clean(row.get("role")) == "CONTRACTOR"
            and clean(row.get("is_primary")).lower() in TRUE_VALUES
            and project_id in project_by_id
            and party_id != clean(project_by_id[project_id].get("executing_company_id"))
        ):
            result.warning(
                configured_files["project_parties"],
                "primary contractor differs from projects.executing_company_id; "
                "confirm whether both roles are intended",
                line_number,
            )

    # Funding
    funding = datasets["project_funding"]
    require_fields(
        funding,
        {
            "project_funding_id",
            "project_id",
            "funding_party_id",
            "funding_type",
            "is_public",
            "data_quality_status",
        },
        configured_files["project_funding"],
        result,
    )
    validate_unique(
        funding,
        "project_funding_id",
        configured_files["project_funding"],
        result,
    )
    validate_pattern(
        funding,
        "project_funding_id",
        "project_funding_id",
        configured_files["project_funding"],
        result,
    )
    validate_controlled(
        funding,
        "funding_type",
        funding_types,
        configured_files["project_funding"],
        result,
    )
    validate_controlled(
        funding,
        "data_quality_status",
        quality_statuses,
        configured_files["project_funding"],
        result,
    )
    validate_boolean(
        funding, "is_public", configured_files["project_funding"], result
    )
    validate_dates(funding, configured_files["project_funding"], result)
    for line_number, row in enumerate(funding, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                configured_files["project_funding"],
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )
        if clean(row.get("funding_party_id")) not in organization_ids:
            result.error(
                configured_files["project_funding"],
                f"funding_party_id {clean(row.get('funding_party_id'))!r} "
                "does not exist in organizations.csv",
                line_number,
            )
        number(
            row,
            "approved_amount_npr",
            configured_files["project_funding"],
            line_number,
            result,
            minimum=0,
        )
        number(
            row,
            "contribution_percent",
            configured_files["project_funding"],
            line_number,
            result,
            minimum=0,
            maximum=100,
        )

    # Work catalog
    work_catalog = datasets["work_catalog"]
    require_fields(
        work_catalog,
        {
            "work_id",
            "work_code",
            "description",
            "category",
            "active",
            "data_quality_status",
        },
        configured_files["work_catalog"],
        result,
    )
    work_ids = validate_unique(
        work_catalog, "work_id", configured_files["work_catalog"], result
    )
    validate_unique(
        work_catalog, "work_code", configured_files["work_catalog"], result
    )
    validate_pattern(
        work_catalog,
        "work_id",
        "work_id",
        configured_files["work_catalog"],
        result,
    )
    validate_boolean(
        work_catalog, "active", configured_files["work_catalog"], result
    )
    validate_units(
        work_catalog,
        "default_unit",
        configured_files["work_catalog"],
        result,
    )
    validate_controlled(
        work_catalog,
        "data_quality_status",
        quality_statuses,
        configured_files["work_catalog"],
        result,
    )

    # Project work items
    work_items = datasets["project_work_items"]
    require_fields(
        work_items,
        {
            "project_work_id",
            "project_id",
            "work_id",
            "work_status",
            "is_public",
            "data_quality_status",
            "verification_status",
        },
        configured_files["project_work_items"],
        result,
    )
    validate_unique(
        work_items,
        "project_work_id",
        configured_files["project_work_items"],
        result,
    )
    validate_pattern(
        work_items,
        "project_work_id",
        "project_work_id",
        configured_files["project_work_items"],
        result,
    )
    validate_controlled(
        work_items,
        "work_status",
        work_statuses,
        configured_files["project_work_items"],
        result,
    )
    validate_controlled(
        work_items,
        "data_quality_status",
        quality_statuses,
        configured_files["project_work_items"],
        result,
    )
    validate_controlled(
        work_items,
        "verification_status",
        verification_statuses,
        configured_files["project_work_items"],
        result,
    )
    validate_boolean(
        work_items, "is_public", configured_files["project_work_items"], result
    )
    validate_units(
        work_items, "unit", configured_files["project_work_items"], result
    )
    validate_dates(work_items, configured_files["project_work_items"], result)
    validate_quality_issue(
        work_items, configured_files["project_work_items"], result
    )
    for line_number, row in enumerate(work_items, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                configured_files["project_work_items"],
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )
        if clean(row.get("work_id")) not in work_ids:
            result.error(
                configured_files["project_work_items"],
                f"work_id {clean(row.get('work_id'))!r} does not exist",
                line_number,
            )

        values = {
            field_name: number(
                row,
                field_name,
                configured_files["project_work_items"],
                line_number,
                result,
                minimum=0,
                maximum=100 if field_name == "progress_percent" else None,
            )
            for field_name in (
                "no",
                "planned_quantity",
                "completed_quantity",
                "remaining_quantity",
                "rate_npr",
                "amount_npr",
                "factor",
                "progress_percent",
            )
        }
        planned = values["planned_quantity"]
        completed = values["completed_quantity"]
        remaining = values["remaining_quantity"]
        progress = values["progress_percent"]
        factor = values["factor"]
        if factor is not None and clean(row.get("factor_definition")) != "TO_BE_CONFIRMED":
            result.error(
                configured_files["project_work_items"],
                "a preserved Factor must use factor_definition TO_BE_CONFIRMED "
                "until its business meaning is verified",
                line_number,
            )
        if (
            planned is not None
            and completed is not None
            and remaining is not None
            and not math.isclose(
                remaining, planned - completed, rel_tol=1e-9, abs_tol=1e-6
            )
        ):
            result.error(
                configured_files["project_work_items"],
                "remaining_quantity must equal planned_quantity - "
                "completed_quantity",
                line_number,
            )
        if progress is not None:
            if planned is None or planned <= 0:
                result.error(
                    configured_files["project_work_items"],
                    "progress_percent cannot be calculated without a positive "
                    "planned_quantity",
                    line_number,
                )
            elif completed is not None:
                expected = completed / planned * 100
                if not math.isclose(
                    progress, expected, rel_tol=1e-6, abs_tol=0.01
                ):
                    result.error(
                        configured_files["project_work_items"],
                        "progress_percent must equal completed_quantity / "
                        "planned_quantity × 100",
                        line_number,
                    )

    # Material master
    materials = datasets["materials_master"]
    require_fields(
        materials,
        {
            "material_id",
            "material_code",
            "material_name",
            "material_category",
            "default_unit",
            "active",
            "data_quality_status",
        },
        configured_files["materials_master"],
        result,
    )
    material_ids = validate_unique(
        materials,
        "material_id",
        configured_files["materials_master"],
        result,
    )
    validate_unique(
        materials,
        "material_code",
        configured_files["materials_master"],
        result,
    )
    validate_pattern(
        materials,
        "material_id",
        "material_id",
        configured_files["materials_master"],
        result,
    )
    validate_boolean(
        materials, "active", configured_files["materials_master"], result
    )
    validate_units(
        materials,
        "default_unit",
        configured_files["materials_master"],
        result,
    )
    validate_controlled(
        materials,
        "data_quality_status",
        quality_statuses,
        configured_files["materials_master"],
        result,
    )

    # Material inventory snapshots
    inventory = datasets["project_material_inventory"]
    require_fields(
        inventory,
        {
            "inventory_id",
            "project_id",
            "material_id",
            "quantity_on_site",
            "unit",
            "condition",
            "as_of_date",
            "last_updated",
            "is_public",
            "data_quality_status",
            "verification_status",
        },
        configured_files["project_material_inventory"],
        result,
    )
    validate_unique(
        inventory,
        "inventory_id",
        configured_files["project_material_inventory"],
        result,
    )
    validate_pattern(
        inventory,
        "inventory_id",
        "inventory_id",
        configured_files["project_material_inventory"],
        result,
    )
    validate_controlled(
        inventory,
        "condition",
        material_conditions,
        configured_files["project_material_inventory"],
        result,
    )
    validate_controlled(
        inventory,
        "data_quality_status",
        quality_statuses,
        configured_files["project_material_inventory"],
        result,
    )
    validate_controlled(
        inventory,
        "verification_status",
        verification_statuses,
        configured_files["project_material_inventory"],
        result,
    )
    validate_boolean(
        inventory,
        "is_public",
        configured_files["project_material_inventory"],
        result,
    )
    validate_units(
        inventory,
        "unit",
        configured_files["project_material_inventory"],
        result,
    )
    validate_dates(
        inventory, configured_files["project_material_inventory"], result
    )
    validate_quality_issue(
        inventory, configured_files["project_material_inventory"], result
    )
    for line_number, row in enumerate(inventory, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                configured_files["project_material_inventory"],
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )
        if clean(row.get("material_id")) not in material_ids:
            result.error(
                configured_files["project_material_inventory"],
                f"material_id {clean(row.get('material_id'))!r} does not exist",
                line_number,
            )
        values = {
            field_name: number(
                row,
                field_name,
                configured_files["project_material_inventory"],
                line_number,
                result,
                minimum=0,
            )
            for field_name in (
                "quantity_on_site",
                "reserved_quantity",
                "available_quantity",
            )
        }
        on_site = values["quantity_on_site"]
        reserved = values["reserved_quantity"]
        available = values["available_quantity"]
        if (
            on_site is not None
            and reserved is not None
            and available is not None
            and not math.isclose(
                available, on_site - reserved, rel_tol=1e-9, abs_tol=1e-6
            )
        ):
            result.warning(
                configured_files["project_material_inventory"],
                "available_quantity differs from quantity_on_site - "
                "reserved_quantity; confirm the snapshot",
                line_number,
            )

    return result


def print_result(result: ValidationResult) -> None:
    for issue in result.issues:
        print(issue)
    print()
    print("Validated datasets:")
    for name, count in sorted(result.row_counts.items()):
        print(f"  {name}: {count} row(s)")
    print(
        f"\nResult: {len(result.errors)} error(s), "
        f"{len(result.warnings)} warning(s)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of scripts/)",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return a failing exit code when warnings exist",
    )
    args = parser.parse_args(argv)
    result = validate_repository(args.root.resolve())
    print_result(result)
    if result.errors or (args.strict_warnings and result.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
