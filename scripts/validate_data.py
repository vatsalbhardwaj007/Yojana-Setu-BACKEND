#!/usr/bin/env python3
"""
validate_data.py — Validate scheme JSON files against M4 schemas.

Usage:
    python3 scripts/validate_data.py

Reads:
    data/scheme_schema.json
    data/rules_schema.json
    data/documents_schema.json
    data/tutorials_schema.json
    data/canonical_values.json
    data/schemes/*.json

Validates:
    1. Schema conformance for each scheme file
    2. Unique scheme_code across all files
    3. scheme_code matches filename
    4. Operator values are from canonical set
    5. Document type values are from canonical set
    6. scheme_type values are from canonical set
    7. status values are from canonical set

Exit code 0 = all valid, 1 = errors found.
"""

import json
import sys
import os
from pathlib import Path

import jsonschema

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMES_DIR = DATA_DIR / "schemes"

SCHEMA_FILES = {
    "scheme": DATA_DIR / "scheme_schema.json",
    "rules": DATA_DIR / "rules_schema.json",
    "documents": DATA_DIR / "documents_schema.json",
    "tutorials": DATA_DIR / "tutorials_schema.json",
}
CANONICAL_FILE = DATA_DIR / "canonical_values.json"


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_canonical_enums(scheme_data: dict, canonical: dict, errors: list, filename: str):
    """Check enum fields against canonical values."""
    # scheme_type
    st = scheme_data.get("scheme_type")
    if st and st not in canonical.get("scheme_types", []):
        errors.append(f"  [{filename}] scheme_type '{st}' not in canonical scheme_types")

    # status
    status = scheme_data.get("status")
    if status and status not in canonical.get("statuses", []):
        errors.append(f"  [{filename}] status '{status}' not in canonical statuses")

    # rules: operator
    for i, rule in enumerate(scheme_data.get("rules", [])):
        op = rule.get("operator")
        if op and op not in canonical.get("operators", []):
            errors.append(f"  [{filename}] rules[{i}].operator '{op}' not in canonical operators")

    # exclusion_rules: operator
    for i, rule in enumerate(scheme_data.get("exclusion_rules", [])):
        op = rule.get("operator")
        if op and op not in canonical.get("operators", []):
            errors.append(f"  [{filename}] exclusion_rules[{i}].operator '{op}' not in canonical operators")

    # documents: document_type
    for i, doc in enumerate(scheme_data.get("documents", [])):
        dt = doc.get("document_type")
        if dt and dt not in canonical.get("document_types", []):
            errors.append(f"  [{filename}] documents[{i}].document_type '{dt}' not in canonical document_types")


def validate_profile_fields(profile_fields: list, errors: list, filename: str):
    """Validate profile field types against canonical values."""
    valid_types = {"text", "number", "date", "boolean", "select"}
    for i, pf in enumerate(profile_fields):
        ft = pf.get("field_type")
        if ft and ft not in valid_types:
            errors.append(f"  [{filename}] profile_fields[{i}].field_type '{ft}' not valid")


def main():
    errors = []
    warnings = []

    # Load schemas
    schemas = {}
    for key, path in SCHEMA_FILES.items():
        if not path.exists():
            errors.append(f"Schema file missing: {path}")
        else:
            schemas[key] = load_json(path)

    if errors:
        print("FATAL: Schema files missing:")
        for e in errors:
            print(e)
        return 1

    # Load canonical values
    if not CANONICAL_FILE.exists():
        errors.append(f"Canonical values file missing: {CANONICAL_FILE}")
        print("FATAL: canonical_values.json not found")
        return 1
    canonical = load_json(CANONICAL_FILE)

    # Find scheme files
    if not SCHEMES_DIR.exists():
        SCHEMES_DIR.mkdir(parents=True, exist_ok=True)

    scheme_files = sorted(SCHEMES_DIR.glob("*.json"))

    if not scheme_files:
        warnings.append("No scheme files found in data/schemes/ — this is OK for M4 (no real data).")
        print("Validation: SCHEMAS OK, CANONICAL OK")
        for w in warnings:
            print(f"  WARNING: {w}")
        print("No scheme data to validate (empty directory).")
        return 0

    # Track scheme_codes for uniqueness
    scheme_codes = set()

    for sf in scheme_files:
        filename = sf.name
        try:
            data = load_json(sf)
        except json.JSONDecodeError as e:
            errors.append(f"  [{filename}] Invalid JSON: {e}")
            continue

        # Validate against scheme schema
        try:
            jsonschema.validate(data, schemas["scheme"])
        except jsonschema.ValidationError as e:
            errors.append(f"  [{filename}] Schema error: {e.message}")
            continue

        # Validate scheme_code matches filename
        expected_code = sf.stem  # filename without .json
        actual_code = data.get("scheme_code", "")
        if actual_code != expected_code:
            errors.append(
                f"  [{filename}] scheme_code '{actual_code}' does not match filename stem '{expected_code}'"
            )

        # Unique scheme_code
        if actual_code in scheme_codes:
            errors.append(f"  [{filename}] Duplicate scheme_code '{actual_code}'")
        scheme_codes.add(actual_code)

        # Validate canonical enums
        validate_canonical_enums(data, canonical, errors, filename)

        # Validate nested: rules
        for i, rule in enumerate(data.get("rules", [])):
            try:
                jsonschema.validate(rule, schemas["rules"])
            except jsonschema.ValidationError as e:
                errors.append(f"  [{filename}] rules[{i}] schema error: {e.message}")

        # Validate nested: exclusion_rules (same schema as rules)
        for i, rule in enumerate(data.get("exclusion_rules", [])):
            try:
                jsonschema.validate(rule, schemas["rules"])
            except jsonschema.ValidationError as e:
                errors.append(f"  [{filename}] exclusion_rules[{i}] schema error: {e.message}")

        # Validate nested: documents
        for i, doc in enumerate(data.get("documents", [])):
            try:
                jsonschema.validate(doc, schemas["documents"])
            except jsonschema.ValidationError as e:
                errors.append(f"  [{filename}] documents[{i}] schema error: {e.message}")

        # Validate nested: tutorial_steps
        for i, step in enumerate(data.get("tutorial_steps", [])):
            try:
                jsonschema.validate(step, schemas["tutorials"])
            except jsonschema.ValidationError as e:
                errors.append(f"  [{filename}] tutorial_steps[{i}] schema error: {e.message}")

        # Validate profile_fields
        validate_profile_fields(data.get("profile_fields", []), errors, filename)

        # Validate nested: verification
        for i, v in enumerate(data.get("verification", [])):
            vm = v.get("verification_method")
            if vm and vm not in canonical.get("verification_methods", []):
                errors.append(f"  [{filename}] verification[{i}].verification_method '{vm}' not valid")

    # Report
    print(f"Validated {len(scheme_files)} scheme file(s).")

    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    if errors:
        print(f"\n{len(errors)} error(s) found:")
        for e in errors:
            print(e)
        return 1

    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
