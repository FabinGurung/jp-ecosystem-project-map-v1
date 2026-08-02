#!/usr/bin/env python3
"""Validate the public JP Ecosystem v1.2 normalized CSV model.

The validator checks:
- configuration and required data-file mappings;
- CSV structure, required headers, duplicate IDs and spreadsheet errors;
- controlled values, booleans, dates, numbers and coordinates;
- primary-key and foreign-key relationships across canonical tables;
- optional legacy project codes for post-v1.1 projects;
- public-data hygiene and documented data-quality warnings;
- selected business rules that are already confirmed.

It deliberately does not infer missing engineering, financial, contractor or
inventory values.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SPREADSHEET_ERRORS = {
    "#REF!",
    "#VALUE!",
    "#DIV/0!",
    "#N/A",
    "#NAME?",
    "#NUM!",
    "#NULL!",
}
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
    "component_id": re.compile(r"^PCO-\d{6}$"),
    "project_source_link_id": re.compile(r"^PSL-\d{6}$"),
    "opportunity_id": re.compile(r"^OPP-\d{6}$"),
    "organization_location_id": re.compile(r"^OLOC-\d{6}$"),
    "publication_setting_id": re.compile(r"^PPS-\d{6}$"),
    "source_group_id": re.compile(r"^GRP\d{3}$"),
}

REQUIRED_HEADERS = {
    "projects": {
        "project_id",
        "company_project_code",
        "legacy_project_code",
        "project_name",
        "display_name",
        "location_ward_number",
        "project_sector",
        "project_category",
        "project_function",
        "government_level",
        "implementation_mechanism",
        "executing_company_id",
        "contractor_verification_status",
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
    "project_components": {
        "component_id",
        "project_id",
        "source_group_id",
        "component_type",
        "component_name",
        "sequence_no",
        "latitude",
        "longitude",
        "status",
        "is_public",
        "remarks",
    },
    "project_source_links": {
        "project_source_link_id",
        "source_group_id",
        "project_id",
        "source_alias",
        "link_type",
        "verification_status",
        "is_public",
        "remarks",
    },
    "project_opportunities": {
        "opportunity_id",
        "source_group_id",
        "opportunity_name",
        "location_ward_number",
        "project_sector",
        "funding_type",
        "status",
        "latitude",
        "longitude",
        "awarded_company_id",
        "is_public",
        "data_quality_status",
        "data_quality_issue",
        "remarks",
    },
    "organization_locations": {
        "organization_location_id",
        "organization_id",
        "source_group_id",
        "location_name",
        "location_type",
        "location_ward_number",
        "latitude",
        "longitude",
        "is_public",
        "data_quality_status",
        "data_quality_issue",
        "remarks",
    },
    "project_publication_settings": {
        "publication_setting_id",
        "project_id",
        "show_project_name",
        "show_coordinates",
        "show_status",
        "show_ward_number",
        "show_project_sector",
        "show_implementation_method",
        "show_legal_contractor",
        "show_executing_company_role",
        "show_general_work_summary",
        "contract_amount_visibility",
        "material_quantities_visibility",
        "remarks",
    },
}

EXPECTED_DATASETS = frozenset(REQUIRED_HEADERS)


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


def is_true(value: object) -> bool:
    return clean(value).lower() in TRUE_VALUES


def read_csv(
    path: Path, dataset_name: str, result: ValidationResult
) -> list[dict[str, str]]:
    if not path.exists():
        result.error(path.name, "required data file is missing")
        return []

    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        result.error(path.name, f"could not open UTF-8 CSV: {exc}")
        return []

    with handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if not headers:
            result.error(path.name, "header row is missing")
            return []

        duplicate_headers = sorted(
            header for header, count in Counter(headers).items() if count > 1
        )
        if duplicate_headers:
            result.error(path.name, f"duplicate headers: {duplicate_headers}")

        missing = sorted(REQUIRED_HEADERS[dataset_name] - set(headers))
        if missing:
            result.error(path.name, f"missing required columns: {missing}")

        forbidden = sorted(
            FORBIDDEN_PUBLIC_HEADERS & {header.lower() for header in headers}
        )
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
                        "store a blank value and document the issue instead",
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
                result.error(file_name, f"{field_name} is required", line_number)


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
                file_name, f"duplicate {field_name} {value!r}", line_number
            )
        seen.add(value)
    return seen


def validate_composite_unique(
    rows: Iterable[dict[str, str]],
    field_names: Sequence[str],
    file_name: str,
    result: ValidationResult,
) -> None:
    seen: set[tuple[str, ...]] = set()
    for line_number, row in enumerate(rows, start=2):
        values = tuple(clean(row.get(name)) for name in field_names)
        if any(not value for value in values):
            continue
        if values in seen:
            joined = ", ".join(
                f"{name}={value!r}" for name, value in zip(field_names, values)
            )
            result.error(file_name, f"duplicate relationship ({joined})", line_number)
        seen.add(values)


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


def validate_delimited_pattern(
    rows: Iterable[dict[str, str]],
    field_name: str,
    pattern_name: str,
    separator: str,
    file_name: str,
    result: ValidationResult,
) -> None:
    pattern = PATTERNS[pattern_name]
    for line_number, row in enumerate(rows, start=2):
        value = clean(row.get(field_name))
        if not value:
            continue
        parts = [part.strip() for part in value.split(separator)]
        invalid = [part for part in parts if not pattern.fullmatch(part)]
        if invalid:
            result.error(
                file_name,
                f"{field_name} contains invalid value(s): {invalid}",
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
                file_name, f"{field_name} must be TRUE or FALSE", line_number
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
    row: Mapping[str, str],
    field_name: str,
    file_name: str,
    line_number: int,
    result: ValidationResult,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    allow_blank: bool = True,
    integer: bool = False,
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
    if integer and not parsed.is_integer():
        result.error(file_name, f"{field_name} must be a whole number", line_number)
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


def validate_coordinates(
    rows: Iterable[dict[str, str]],
    file_name: str,
    result: ValidationResult,
    *,
    required: bool = True,
) -> None:
    for line_number, row in enumerate(rows, start=2):
        number(
            row,
            "latitude",
            file_name,
            line_number,
            result,
            minimum=-90,
            maximum=90,
            allow_blank=not required,
        )
        number(
            row,
            "longitude",
            file_name,
            line_number,
            result,
            minimum=-180,
            maximum=180,
            allow_blank=not required,
        )


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
        if "data_quality_issue" not in row:
            continue
        status = clean(row.get("data_quality_status"))
        issue = clean(row.get("data_quality_issue"))
        if status in {"WARNING", "ERROR"} and not issue:
            result.error(
                file_name,
                "data_quality_issue is required when data_quality_status is "
                f"{status}",
                line_number,
            )


def validate_config(config: dict[str, object], result: ValidationResult) -> bool:
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

    configured_files = config.get("data_files")
    if not isinstance(configured_files, dict):
        result.error("map-config.json", "data_files must be an object")
        return False

    missing_file_keys = sorted(EXPECTED_DATASETS - set(configured_files))
    if missing_file_keys:
        result.error(
            "map-config.json",
            f"data_files is missing keys: {missing_file_keys}",
        )
        return False

    controls = config.get("controlled_values")
    if not isinstance(controls, dict):
        result.error("map-config.json", "controlled_values must be an object")
        return False

    required_control_keys = {
        "project_sectors",
        "project_categories",
        "project_functions",
        "implementation_mechanisms",
        "government_levels",
        "organization_types",
        "party_entity_types",
        "party_roles",
        "funding_types",
        "work_statuses",
        "material_conditions",
        "component_types",
        "source_link_types",
        "opportunity_statuses",
        "organization_location_types",
        "publication_visibility_values",
        "data_quality_statuses",
        "verification_statuses",
    }
    missing_controls = sorted(required_control_keys - set(controls))
    if missing_controls:
        result.error(
            "map-config.json",
            f"controlled_values is missing keys: {missing_controls}",
        )
        return False

    for key in sorted(required_control_keys):
        values = controls.get(key)
        if not isinstance(values, list) or not values:
            result.error(
                "map-config.json",
                f"controlled_values.{key} must be a non-empty list",
            )
        elif len(values) != len(set(values)):
            result.error(
                "map-config.json",
                f"controlled_values.{key} contains duplicate values",
            )

    statuses = config.get("status_styles")
    if not isinstance(statuses, dict) or not statuses:
        result.error("map-config.json", "status_styles must be a non-empty object")

    return not result.errors


def validate_repository(root: Path) -> ValidationResult:
    result = ValidationResult()
    config_path = root / "map-config.json"
    if not config_path.exists():
        result.error("map-config.json", "configuration file is missing")
        return result

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        result.error("map-config.json", f"invalid JSON: {exc}")
        return result

    if not validate_config(config, result):
        return result

    configured_files = config["data_files"]
    assert isinstance(configured_files, dict)
    datasets = {
        name: read_csv(root / str(configured_files[name]), name, result)
        for name in sorted(EXPECTED_DATASETS)
    }

    controls = config["controlled_values"]
    assert isinstance(controls, dict)
    statuses = set(config.get("status_styles", {}))
    project_sectors = set(controls["project_sectors"])
    project_categories = set(controls["project_categories"])
    project_functions = set(controls["project_functions"])
    mechanisms = set(controls["implementation_mechanisms"])
    government_levels = set(controls["government_levels"])
    organization_types = set(controls["organization_types"])
    party_entity_types = set(controls["party_entity_types"])
    party_roles = set(controls["party_roles"])
    funding_types = set(controls["funding_types"])
    work_statuses = set(controls["work_statuses"])
    material_conditions = set(controls["material_conditions"])
    component_types = set(controls["component_types"])
    source_link_types = set(controls["source_link_types"])
    opportunity_statuses = set(controls["opportunity_statuses"])
    location_types = set(controls["organization_location_types"])
    visibility_values = set(controls["publication_visibility_values"])
    quality_statuses = set(controls["data_quality_statuses"])
    verification_statuses = set(controls["verification_statuses"])

    # Organizations
    organizations = datasets["organizations"]
    organization_file = str(configured_files["organizations"])
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
        organization_file,
        result,
    )
    organization_ids = validate_unique(
        organizations, "organization_id", organization_file, result
    )
    validate_unique(organizations, "organization_code", organization_file, result)
    validate_pattern(
        organizations, "organization_id", "organization_id", organization_file, result
    )
    validate_controlled(
        organizations,
        "organization_type",
        organization_types,
        organization_file,
        result,
    )
    validate_controlled(
        organizations,
        "government_level",
        government_levels,
        organization_file,
        result,
        allow_blank=True,
    )
    validate_controlled(
        organizations,
        "data_quality_status",
        quality_statuses,
        organization_file,
        result,
    )
    validate_boolean(organizations, "active", organization_file, result)
    validate_boolean(organizations, "is_public", organization_file, result)

    organization_by_id = {
        clean(row.get("organization_id")): row for row in organizations
    }
    for line_number, row in enumerate(organizations, start=2):
        organization_id = clean(row.get("organization_id"))
        parent_id = clean(row.get("parent_organization_id"))
        organization_type = clean(row.get("organization_type"))
        government_level = clean(row.get("government_level"))
        ward_number = number(
            row,
            "ward_number",
            organization_file,
            line_number,
            result,
            minimum=1,
            maximum=99,
            integer=True,
        )
        if parent_id and parent_id not in organization_ids:
            result.error(
                organization_file,
                f"parent_organization_id {parent_id!r} does not exist",
                line_number,
            )
        if parent_id == organization_id and parent_id:
            result.error(
                organization_file,
                "organization cannot be its own parent",
                line_number,
            )
        if organization_type == "WARD_OFFICE":
            if not parent_id:
                result.error(
                    organization_file,
                    "WARD_OFFICE requires parent_organization_id",
                    line_number,
                )
            if ward_number is None:
                result.error(
                    organization_file,
                    "WARD_OFFICE requires ward_number",
                    line_number,
                )
            if government_level != "LOCAL":
                result.error(
                    organization_file,
                    "WARD_OFFICE must use government_level LOCAL",
                    line_number,
                )
        if organization_type in {"MUNICIPALITY", "RURAL_MUNICIPALITY"}:
            if government_level != "LOCAL":
                result.error(
                    organization_file,
                    f"{organization_type} must use government_level LOCAL",
                    line_number,
                )

    # People may intentionally contain zero rows.
    people = datasets["people"]
    people_file = str(configured_files["people"])
    require_fields(
        people,
        {
            "person_id",
            "display_name",
            "active",
            "is_public",
            "data_quality_status",
        },
        people_file,
        result,
    )
    person_ids = validate_unique(people, "person_id", people_file, result)
    validate_pattern(people, "person_id", "person_id", people_file, result)
    validate_boolean(people, "active", people_file, result)
    validate_boolean(people, "is_public", people_file, result)
    validate_controlled(
        people, "data_quality_status", quality_statuses, people_file, result
    )

    # Projects
    projects = datasets["projects"]
    projects_file = str(configured_files["projects"])
    if not projects:
        result.error(projects_file, "must contain project rows")
    require_fields(
        projects,
        {
            "project_id",
            "company_project_code",
            "project_name",
            "display_name",
            "location_ward_number",
            "project_sector",
            "project_category",
            "project_function",
            "implementation_mechanism",
            "executing_company_id",
            "contractor_verification_status",
            "latitude",
            "longitude",
            "status",
            "last_updated",
            "is_public",
            "data_quality_status",
            "verification_status",
        },
        projects_file,
        result,
    )
    project_ids = validate_unique(projects, "project_id", projects_file, result)
    validate_unique(projects, "company_project_code", projects_file, result)
    validate_unique(projects, "legacy_project_code", projects_file, result)
    validate_pattern(projects, "project_id", "project_id", projects_file, result)
    validate_pattern(
        projects,
        "company_project_code",
        "company_project_code",
        projects_file,
        result,
    )
    # legacy_project_code is optional for projects created after the v1.1 migration.
    validate_pattern(
        projects,
        "legacy_project_code",
        "legacy_project_code",
        projects_file,
        result,
    )
    validate_delimited_pattern(
        projects,
        "source_group_ids",
        "source_group_id",
        "|",
        projects_file,
        result,
    )
    validate_controlled(projects, "status", statuses, projects_file, result)
    validate_controlled(
        projects, "project_sector", project_sectors, projects_file, result
    )
    validate_controlled(
        projects, "project_category", project_categories, projects_file, result
    )
    validate_controlled(
        projects, "project_function", project_functions, projects_file, result
    )
    validate_controlled(
        projects, "government_level", government_levels, projects_file, result,
        allow_blank=True,
    )
    validate_controlled(
        projects, "implementation_mechanism", mechanisms, projects_file, result
    )
    validate_controlled(
        projects,
        "contractor_verification_status",
        verification_statuses,
        projects_file,
        result,
    )
    validate_controlled(
        projects, "data_quality_status", quality_statuses, projects_file, result
    )
    validate_controlled(
        projects,
        "verification_status",
        verification_statuses,
        projects_file,
        result,
    )
    validate_boolean(projects, "is_public", projects_file, result)
    validate_dates(projects, projects_file, result)
    validate_coordinates(projects, projects_file, result, required=True)

    project_by_id = {clean(row.get("project_id")): row for row in projects}
    for line_number, row in enumerate(projects, start=2):
        ward_number = number(
            row,
            "location_ward_number",
            projects_file,
            line_number,
            result,
            minimum=1,
            maximum=99,
            allow_blank=False,
            integer=True,
        )
        del ward_number
        for field_name in (
            "physical_progress_percent",
            "financial_progress_percent",
        ):
            number(
                row,
                field_name,
                projects_file,
                line_number,
                result,
                minimum=0,
                maximum=100,
            )

        company_id = clean(row.get("executing_company_id"))
        company = organization_by_id.get(company_id)
        if not company:
            result.error(
                projects_file,
                f"executing_company_id {company_id!r} does not exist",
                line_number,
            )
        else:
            expected_prefix = f"{clean(company.get('organization_code'))}-"
            code = clean(row.get("company_project_code"))
            if code and not code.startswith(expected_prefix):
                result.error(
                    projects_file,
                    f"company_project_code {code!r} must start with "
                    f"{expected_prefix!r} for executing company {company_id}",
                    line_number,
                )

        sector = clean(row.get("project_sector"))
        mechanism = clean(row.get("implementation_mechanism"))
        government_level = clean(row.get("government_level"))
        if mechanism.startswith("GOVERNMENT_") and sector != "GOVERNMENT_PUBLIC":
            result.error(
                projects_file,
                "government implementation requires project_sector "
                "GOVERNMENT_PUBLIC",
                line_number,
            )
        if mechanism.startswith("PRIVATE_") and sector != "PRIVATE":
            result.error(
                projects_file,
                "private implementation requires project_sector PRIVATE",
                line_number,
            )
        if sector == "GOVERNMENT_PUBLIC" and not government_level:
            result.error(
                projects_file,
                "government project requires government_level",
                line_number,
            )
        if government_level and sector != "GOVERNMENT_PUBLIC":
            result.warning(
                projects_file,
                "government_level is populated while project_sector is not "
                "GOVERNMENT_PUBLIC",
                line_number,
            )
        if clean(row.get("status")) == "Completed":
            progress = clean(row.get("physical_progress_percent"))
            if progress and not math.isclose(float(progress), 100.0, abs_tol=0.01):
                result.warning(
                    projects_file,
                    "Completed project has physical_progress_percent other than 100",
                    line_number,
                )

    # Project parties
    project_parties = datasets["project_parties"]
    parties_file = str(configured_files["project_parties"])
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
        parties_file,
        result,
    )
    validate_unique(
        project_parties, "project_party_id", parties_file, result
    )
    validate_pattern(
        project_parties,
        "project_party_id",
        "project_party_id",
        parties_file,
        result,
    )
    validate_controlled(
        project_parties,
        "party_entity_type",
        party_entity_types,
        parties_file,
        result,
    )
    validate_controlled(
        project_parties, "role", party_roles, parties_file, result
    )
    validate_controlled(
        project_parties,
        "data_quality_status",
        quality_statuses,
        parties_file,
        result,
    )
    validate_boolean(project_parties, "is_primary", parties_file, result)
    validate_boolean(project_parties, "is_public", parties_file, result)
    validate_dates(project_parties, parties_file, result)

    primary_contractors: dict[str, list[str]] = {}
    for line_number, row in enumerate(project_parties, start=2):
        project_id = clean(row.get("project_id"))
        if project_id not in project_ids:
            result.error(
                parties_file,
                f"project_id {project_id!r} does not exist",
                line_number,
            )
        entity_type = clean(row.get("party_entity_type"))
        party_id = clean(row.get("party_id"))
        if entity_type == "ORGANIZATION" and party_id not in organization_ids:
            result.error(
                parties_file,
                f"organization party_id {party_id!r} does not exist",
                line_number,
            )
        if entity_type == "PERSON" and party_id not in person_ids:
            result.error(
                parties_file,
                f"person party_id {party_id!r} does not exist",
                line_number,
            )
        if clean(row.get("role")) == "CONTRACTOR" and is_true(
            row.get("is_primary")
        ):
            primary_contractors.setdefault(project_id, []).append(party_id)
            if (
                project_id in project_by_id
                and party_id
                != clean(project_by_id[project_id].get("executing_company_id"))
            ):
                result.warning(
                    parties_file,
                    "primary contractor differs from projects.executing_company_id; "
                    "confirm whether both roles are intended",
                    line_number,
                )

    for project_id in sorted(project_ids):
        contractors = primary_contractors.get(project_id, [])
        if not contractors:
            result.error(
                parties_file,
                f"{project_id} has no primary contractor relationship",
            )
        elif len(contractors) > 1:
            result.error(
                parties_file,
                f"{project_id} has multiple primary contractor relationships",
            )

    # Project funding
    funding = datasets["project_funding"]
    funding_file = str(configured_files["project_funding"])
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
        funding_file,
        result,
    )
    validate_unique(funding, "project_funding_id", funding_file, result)
    validate_pattern(
        funding,
        "project_funding_id",
        "project_funding_id",
        funding_file,
        result,
    )
    validate_controlled(funding, "funding_type", funding_types, funding_file, result)
    validate_controlled(
        funding, "data_quality_status", quality_statuses, funding_file, result
    )
    validate_boolean(funding, "is_public", funding_file, result)
    validate_dates(funding, funding_file, result)

    funded_project_ids: set[str] = set()
    for line_number, row in enumerate(funding, start=2):
        project_id = clean(row.get("project_id"))
        funding_party_id = clean(row.get("funding_party_id"))
        funded_project_ids.add(project_id)
        if project_id not in project_ids:
            result.error(
                funding_file,
                f"project_id {project_id!r} does not exist",
                line_number,
            )
        funder = organization_by_id.get(funding_party_id)
        if not funder:
            result.error(
                funding_file,
                f"funding_party_id {funding_party_id!r} does not exist in "
                "organizations.csv",
                line_number,
            )
        number(
            row,
            "approved_amount_npr",
            funding_file,
            line_number,
            result,
            minimum=0,
        )
        number(
            row,
            "contribution_percent",
            funding_file,
            line_number,
            result,
            minimum=0,
            maximum=100,
        )
        if clean(row.get("funding_type")) == "WARD_BUDGET" and funder:
            if clean(funder.get("organization_type")) != "WARD_OFFICE":
                result.error(
                    funding_file,
                    "WARD_BUDGET funding_party_id must reference a WARD_OFFICE",
                    line_number,
                )
            project = project_by_id.get(project_id)
            if project and clean(funder.get("ward_number")) != clean(
                project.get("location_ward_number")
            ):
                result.error(
                    funding_file,
                    "WARD_BUDGET funder ward_number must match the project's "
                    "location_ward_number",
                    line_number,
                )

    for project_id, project in sorted(project_by_id.items()):
        if (
            clean(project.get("project_sector")) == "GOVERNMENT_PUBLIC"
            and project_id not in funded_project_ids
        ):
            result.error(
                funding_file,
                f"{project_id} is a government project without a funding relationship",
            )

    # Work catalog
    work_catalog = datasets["work_catalog"]
    work_file = str(configured_files["work_catalog"])
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
        work_file,
        result,
    )
    work_ids = validate_unique(work_catalog, "work_id", work_file, result)
    validate_unique(work_catalog, "work_code", work_file, result)
    validate_pattern(work_catalog, "work_id", "work_id", work_file, result)
    validate_boolean(work_catalog, "active", work_file, result)
    validate_units(work_catalog, "default_unit", work_file, result)
    validate_controlled(
        work_catalog, "data_quality_status", quality_statuses, work_file, result
    )

    # Project work items
    work_items = datasets["project_work_items"]
    work_items_file = str(configured_files["project_work_items"])
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
        work_items_file,
        result,
    )
    validate_unique(work_items, "project_work_id", work_items_file, result)
    validate_pattern(
        work_items,
        "project_work_id",
        "project_work_id",
        work_items_file,
        result,
    )
    validate_pattern(
        work_items,
        "source_group_id",
        "source_group_id",
        work_items_file,
        result,
    )
    validate_controlled(
        work_items, "work_status", work_statuses, work_items_file, result
    )
    validate_controlled(
        work_items,
        "data_quality_status",
        quality_statuses,
        work_items_file,
        result,
    )
    validate_controlled(
        work_items,
        "verification_status",
        verification_statuses,
        work_items_file,
        result,
    )
    validate_boolean(work_items, "is_public", work_items_file, result)
    validate_units(work_items, "unit", work_items_file, result)
    validate_dates(work_items, work_items_file, result)
    validate_quality_issue(work_items, work_items_file, result)

    for line_number, row in enumerate(work_items, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                work_items_file,
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )
        if clean(row.get("work_id")) not in work_ids:
            result.error(
                work_items_file,
                f"work_id {clean(row.get('work_id'))!r} does not exist",
                line_number,
            )
        values = {
            field_name: number(
                row,
                field_name,
                work_items_file,
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
        if factor is not None and clean(
            row.get("factor_definition")
        ) != "TO_BE_CONFIRMED":
            result.error(
                work_items_file,
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
                work_items_file,
                "remaining_quantity must equal planned_quantity - "
                "completed_quantity",
                line_number,
            )
        if progress is not None:
            if planned is None or planned <= 0:
                result.error(
                    work_items_file,
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
                        work_items_file,
                        "progress_percent must equal completed_quantity / "
                        "planned_quantity × 100",
                        line_number,
                    )

    # Materials
    materials = datasets["materials_master"]
    materials_file = str(configured_files["materials_master"])
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
        materials_file,
        result,
    )
    material_ids = validate_unique(
        materials, "material_id", materials_file, result
    )
    validate_unique(materials, "material_code", materials_file, result)
    validate_pattern(materials, "material_id", "material_id", materials_file, result)
    validate_boolean(materials, "active", materials_file, result)
    validate_units(materials, "default_unit", materials_file, result)
    validate_controlled(
        materials, "data_quality_status", quality_statuses, materials_file, result
    )

    # Material inventory
    inventory = datasets["project_material_inventory"]
    inventory_file = str(configured_files["project_material_inventory"])
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
        inventory_file,
        result,
    )
    validate_unique(inventory, "inventory_id", inventory_file, result)
    validate_pattern(inventory, "inventory_id", "inventory_id", inventory_file, result)
    validate_controlled(
        inventory, "condition", material_conditions, inventory_file, result
    )
    validate_controlled(
        inventory, "data_quality_status", quality_statuses, inventory_file, result
    )
    validate_controlled(
        inventory,
        "verification_status",
        verification_statuses,
        inventory_file,
        result,
    )
    validate_boolean(inventory, "is_public", inventory_file, result)
    validate_units(inventory, "unit", inventory_file, result)
    validate_dates(inventory, inventory_file, result)
    validate_quality_issue(inventory, inventory_file, result)

    for line_number, row in enumerate(inventory, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                inventory_file,
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )
        if clean(row.get("material_id")) not in material_ids:
            result.error(
                inventory_file,
                f"material_id {clean(row.get('material_id'))!r} does not exist",
                line_number,
            )
        values = {
            field_name: number(
                row,
                field_name,
                inventory_file,
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
                inventory_file,
                "available_quantity differs from quantity_on_site - "
                "reserved_quantity; confirm the snapshot",
                line_number,
            )

    # Project components
    components = datasets["project_components"]
    components_file = str(configured_files["project_components"])
    require_fields(
        components,
        {
            "component_id",
            "project_id",
            "component_type",
            "component_name",
            "sequence_no",
            "latitude",
            "longitude",
            "status",
            "is_public",
        },
        components_file,
        result,
    )
    validate_unique(components, "component_id", components_file, result)
    validate_composite_unique(
        components, ("project_id", "sequence_no"), components_file, result
    )
    validate_pattern(
        components, "component_id", "component_id", components_file, result
    )
    validate_pattern(
        components, "source_group_id", "source_group_id", components_file, result
    )
    validate_controlled(
        components, "component_type", component_types, components_file, result
    )
    validate_controlled(components, "status", statuses, components_file, result)
    validate_boolean(components, "is_public", components_file, result)
    validate_coordinates(components, components_file, result, required=True)

    for line_number, row in enumerate(components, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                components_file,
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )
        number(
            row,
            "sequence_no",
            components_file,
            line_number,
            result,
            minimum=1,
            allow_blank=False,
            integer=True,
        )

    # Source links
    source_links = datasets["project_source_links"]
    source_links_file = str(configured_files["project_source_links"])
    require_fields(
        source_links,
        {
            "project_source_link_id",
            "source_group_id",
            "project_id",
            "source_alias",
            "link_type",
            "verification_status",
            "is_public",
        },
        source_links_file,
        result,
    )
    validate_unique(
        source_links, "project_source_link_id", source_links_file, result
    )
    validate_unique(source_links, "source_group_id", source_links_file, result)
    validate_pattern(
        source_links,
        "project_source_link_id",
        "project_source_link_id",
        source_links_file,
        result,
    )
    validate_pattern(
        source_links,
        "source_group_id",
        "source_group_id",
        source_links_file,
        result,
    )
    validate_controlled(
        source_links, "link_type", source_link_types, source_links_file, result
    )
    validate_controlled(
        source_links,
        "verification_status",
        verification_statuses,
        source_links_file,
        result,
    )
    validate_boolean(source_links, "is_public", source_links_file, result)
    for line_number, row in enumerate(source_links, start=2):
        if clean(row.get("project_id")) not in project_ids:
            result.error(
                source_links_file,
                f"project_id {clean(row.get('project_id'))!r} does not exist",
                line_number,
            )

    # Opportunities
    opportunities = datasets["project_opportunities"]
    opportunities_file = str(configured_files["project_opportunities"])
    require_fields(
        opportunities,
        {
            "opportunity_id",
            "source_group_id",
            "opportunity_name",
            "location_ward_number",
            "project_sector",
            "funding_type",
            "status",
            "latitude",
            "longitude",
            "is_public",
            "data_quality_status",
        },
        opportunities_file,
        result,
    )
    validate_unique(opportunities, "opportunity_id", opportunities_file, result)
    validate_unique(opportunities, "source_group_id", opportunities_file, result)
    validate_pattern(
        opportunities, "opportunity_id", "opportunity_id", opportunities_file, result
    )
    validate_pattern(
        opportunities,
        "source_group_id",
        "source_group_id",
        opportunities_file,
        result,
    )
    validate_controlled(
        opportunities,
        "project_sector",
        project_sectors,
        opportunities_file,
        result,
    )
    validate_controlled(
        opportunities, "funding_type", funding_types, opportunities_file, result
    )
    validate_controlled(
        opportunities, "status", opportunity_statuses, opportunities_file, result
    )
    validate_controlled(
        opportunities,
        "data_quality_status",
        quality_statuses,
        opportunities_file,
        result,
    )
    validate_boolean(opportunities, "is_public", opportunities_file, result)
    validate_coordinates(opportunities, opportunities_file, result, required=True)
    validate_quality_issue(opportunities, opportunities_file, result)
    for line_number, row in enumerate(opportunities, start=2):
        number(
            row,
            "location_ward_number",
            opportunities_file,
            line_number,
            result,
            minimum=1,
            maximum=99,
            allow_blank=False,
            integer=True,
        )
        awarded_company_id = clean(row.get("awarded_company_id"))
        status = clean(row.get("status"))
        if awarded_company_id and awarded_company_id not in organization_ids:
            result.error(
                opportunities_file,
                f"awarded_company_id {awarded_company_id!r} does not exist",
                line_number,
            )
        if status == "NOT_AWARDED" and awarded_company_id:
            result.error(
                opportunities_file,
                "NOT_AWARDED opportunity must not contain awarded_company_id",
                line_number,
            )
        if status == "AWARDED" and not awarded_company_id:
            result.error(
                opportunities_file,
                "AWARDED opportunity requires awarded_company_id",
                line_number,
            )

    # Organization locations
    locations = datasets["organization_locations"]
    locations_file = str(configured_files["organization_locations"])
    require_fields(
        locations,
        {
            "organization_location_id",
            "organization_id",
            "location_name",
            "location_type",
            "location_ward_number",
            "latitude",
            "longitude",
            "is_public",
            "data_quality_status",
        },
        locations_file,
        result,
    )
    validate_unique(
        locations, "organization_location_id", locations_file, result
    )
    validate_pattern(
        locations,
        "organization_location_id",
        "organization_location_id",
        locations_file,
        result,
    )
    validate_pattern(
        locations, "source_group_id", "source_group_id", locations_file, result
    )
    validate_controlled(
        locations, "location_type", location_types, locations_file, result
    )
    validate_controlled(
        locations,
        "data_quality_status",
        quality_statuses,
        locations_file,
        result,
    )
    validate_boolean(locations, "is_public", locations_file, result)
    validate_coordinates(locations, locations_file, result, required=True)
    validate_quality_issue(locations, locations_file, result)
    for line_number, row in enumerate(locations, start=2):
        organization_id = clean(row.get("organization_id"))
        if organization_id not in organization_ids:
            result.error(
                locations_file,
                f"organization_id {organization_id!r} does not exist",
                line_number,
            )
        number(
            row,
            "location_ward_number",
            locations_file,
            line_number,
            result,
            minimum=1,
            maximum=99,
            allow_blank=False,
            integer=True,
        )

    # Publication settings
    publication = datasets["project_publication_settings"]
    publication_file = str(configured_files["project_publication_settings"])
    boolean_fields = {
        "show_project_name",
        "show_coordinates",
        "show_status",
        "show_ward_number",
        "show_project_sector",
        "show_implementation_method",
        "show_legal_contractor",
        "show_executing_company_role",
        "show_general_work_summary",
    }
    require_fields(
        publication,
        {
            "publication_setting_id",
            "project_id",
            *boolean_fields,
            "contract_amount_visibility",
            "material_quantities_visibility",
        },
        publication_file,
        result,
    )
    validate_unique(
        publication, "publication_setting_id", publication_file, result
    )
    publication_project_ids = validate_unique(
        publication, "project_id", publication_file, result
    )
    validate_pattern(
        publication,
        "publication_setting_id",
        "publication_setting_id",
        publication_file,
        result,
    )
    for field_name in sorted(boolean_fields):
        validate_boolean(publication, field_name, publication_file, result)
    validate_controlled(
        publication,
        "contract_amount_visibility",
        visibility_values,
        publication_file,
        result,
    )
    validate_controlled(
        publication,
        "material_quantities_visibility",
        visibility_values,
        publication_file,
        result,
    )
    for line_number, row in enumerate(publication, start=2):
        project_id = clean(row.get("project_id"))
        if project_id not in project_ids:
            result.error(
                publication_file,
                f"project_id {project_id!r} does not exist",
                line_number,
            )

    missing_publication = sorted(project_ids - publication_project_ids)
    extra_publication = sorted(publication_project_ids - project_ids)
    if missing_publication:
        result.error(
            publication_file,
            "missing publication settings for project IDs: "
            f"{missing_publication}",
        )
    if extra_publication:
        result.error(
            publication_file,
            "publication settings reference unknown project IDs: "
            f"{extra_publication}",
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
