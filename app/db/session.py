"""Database connection and lifecycle management for local relational engine and Supabase."""

import json
import logging
import sqlite3
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# M4 deterministic UUID namespace
M4_UUID_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d")


def deterministic_uuid(seed: str) -> str:
    """Generate a deterministic UUIDv5 matching M4 canonical generation."""
    return str(uuid.uuid5(M4_UUID_NAMESPACE, seed))


# Six canonical table definitions matching M4 schema
CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schemes (
    id TEXT PRIMARY KEY,
    scheme_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    ministry TEXT NOT NULL,
    department TEXT NOT NULL,
    scheme_type TEXT NOT NULL CHECK (scheme_type IN (
        'subsidy', 'insurance', 'pension', 'benefit',
        'loan_guarantee', 'scholarship', 'employment',
        'healthcare', 'housing', 'other'
    )),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    aliases TEXT DEFAULT '[]',
    target_groups TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    benefits TEXT DEFAULT '[]',
    official_url TEXT,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    last_verified_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_schemes_scheme_type ON schemes (scheme_type);
CREATE INDEX IF NOT EXISTS idx_schemes_status ON schemes (status);
CREATE INDEX IF NOT EXISTS idx_schemes_ministry ON schemes (ministry);

CREATE TABLE IF NOT EXISTS scheme_rules (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    rule_group TEXT NOT NULL,
    field TEXT NOT NULL,
    operator TEXT NOT NULL CHECK (operator IN (
        '=', '!=', '>=', '<=', '>', '<',
        'in', 'not_in', 'exists', 'between'
    )),
    value TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_purpose TEXT NOT NULL DEFAULT 'eligibility' CHECK (rule_purpose IN ('eligibility', 'exclusion')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scheme_rules_scheme_id ON scheme_rules (scheme_id);
CREATE INDEX IF NOT EXISTS idx_scheme_rules_rule_group ON scheme_rules (rule_group);
CREATE INDEX IF NOT EXISTS idx_scheme_rules_field ON scheme_rules (field);

CREATE TABLE IF NOT EXISTS scheme_documents (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL CHECK (document_type IN (
        'identity_proof', 'address_proof', 'income_proof',
        'category_certificate', 'age_proof', 'land_record',
        'bank_details', 'photograph', 'declaration', 'other'
    )),
    document_name TEXT NOT NULL,
    is_mandatory INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scheme_documents_scheme_id ON scheme_documents (scheme_id);
CREATE INDEX IF NOT EXISTS idx_scheme_documents_document_type ON scheme_documents (document_type);

CREATE TABLE IF NOT EXISTS tutorial_steps (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL CHECK (step_number >= 1),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    tips TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (scheme_id, step_number)
);

CREATE INDEX IF NOT EXISTS idx_tutorial_steps_scheme_id ON tutorial_steps (scheme_id);

CREATE TABLE IF NOT EXISTS scheme_verification (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    verification_method TEXT NOT NULL CHECK (verification_method IN ('online', 'offline', 'both')),
    verification_url TEXT,
    helpline_number TEXT,
    last_verified_at TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scheme_verification_scheme_id ON scheme_verification (scheme_id);

CREATE TABLE IF NOT EXISTS scheme_profile_fields (
    id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK (field_type IN ('text', 'number', 'date', 'boolean', 'select')),
    is_required INTEGER NOT NULL DEFAULT 1,
    allowed_values TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (scheme_id, field_name)
);

CREATE INDEX IF NOT EXISTS idx_scheme_profile_fields_scheme_id ON scheme_profile_fields (scheme_id);

CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    profile_data TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db_path(custom_path: str | None = None) -> str:
    """Resolve database path."""
    if custom_path:
        return custom_path
    db_file = Path(settings.SQLITE_DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    return str(db_file)


@contextmanager
def get_db_connection(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a contextual database connection with row factory and foreign keys enabled."""
    target_path = get_db_path(db_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | None = None, seed_if_empty: bool = True) -> None:
    """Initialize the 6 canonical tables and optionally seed M4 schemes."""
    with get_db_connection(db_path) as conn:
        conn.executescript(CREATE_TABLES_SQL)

        if seed_if_empty:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM schemes")
            count = cursor.fetchone()[0]
            if count == 0:
                seed_canonical_schemes(conn)


def seed_canonical_schemes(conn: sqlite3.Connection) -> int:
    """Seed all 15 canonical schemes from data/schemes/*.json into the database."""
    schemes_dir = settings.SCHEMES_DIR
    if not schemes_dir.exists():
        logger.warning("Schemes directory not found at: %s", schemes_dir)
        return 0

    scheme_files = sorted(schemes_dir.glob("*.json"))
    seeded_count = 0

    for file_path in scheme_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        scheme_code = data["scheme_code"]
        scheme_id = deterministic_uuid(f"scheme:{scheme_code}")

        # Insert scheme parent record
        conn.execute(
            """
            INSERT OR REPLACE INTO schemes (
                id, scheme_code, name, description, ministry, department,
                scheme_type, status, aliases, target_groups, tags, benefits,
                official_url, effective_from, effective_to, last_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scheme_id,
                scheme_code,
                data.get("name", ""),
                data.get("description", ""),
                data.get("ministry", ""),
                data.get("department", ""),
                data.get("scheme_type", "other"),
                data.get("status", "active"),
                json.dumps(data.get("aliases", []), ensure_ascii=False),
                json.dumps(data.get("target_groups", []), ensure_ascii=False),
                json.dumps(data.get("tags", []), ensure_ascii=False),
                json.dumps(data.get("benefits", []), ensure_ascii=False),
                data.get("official_url"),
                data.get("effective_from"),
                data.get("effective_to"),
                data.get("last_verified_at"),
            ),
        )

        # Insert eligibility rules
        for rule in data.get("rules", []):
            rule_id = deterministic_uuid(
                f"{scheme_code}:rule:{rule.get('field', '')}:{rule.get('operator', '')}:{rule.get('rule_group', '')}"
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO scheme_rules (
                    id, scheme_id, rule_group, field, operator, value, description, rule_purpose
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'eligibility')
                """,
                (
                    rule_id,
                    scheme_id,
                    rule.get("rule_group", ""),
                    rule.get("field", ""),
                    rule.get("operator", "="),
                    json.dumps(rule.get("value"), ensure_ascii=False),
                    rule.get("description", ""),
                ),
            )

        # Insert exclusion rules
        for rule in data.get("exclusion_rules", []):
            rule_id = deterministic_uuid(
                f"{scheme_code}:exclusion:{rule.get('field', '')}:{rule.get('operator', '')}:{rule.get('rule_group', '')}"
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO scheme_rules (
                    id, scheme_id, rule_group, field, operator, value, description, rule_purpose
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'exclusion')
                """,
                (
                    rule_id,
                    scheme_id,
                    rule.get("rule_group", ""),
                    rule.get("field", ""),
                    rule.get("operator", "="),
                    json.dumps(rule.get("value"), ensure_ascii=False),
                    rule.get("description", ""),
                ),
            )

        # Insert documents
        for doc in data.get("documents", []):
            doc_id = deterministic_uuid(
                f"{scheme_code}:doc:{doc.get('document_type', '')}:{doc.get('document_name', '')}"
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO scheme_documents (
                    id, scheme_id, document_type, document_name, is_mandatory, description
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    scheme_id,
                    doc.get("document_type", "other"),
                    doc.get("document_name", ""),
                    1 if doc.get("is_mandatory", True) else 0,
                    doc.get("description"),
                ),
            )

        # Insert tutorial steps
        for step in data.get("tutorial_steps", []):
            step_id = deterministic_uuid(f"{scheme_code}:step:{step.get('step_number', 0)}")
            conn.execute(
                """
                INSERT OR REPLACE INTO tutorial_steps (
                    id, scheme_id, step_number, title, description, tips
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    scheme_id,
                    step.get("step_number", 1),
                    step.get("title", ""),
                    step.get("description", ""),
                    step.get("tips"),
                ),
            )

        # Insert verification
        v_counts: dict[str, int] = {}
        for v in data.get("verification", []):
            method = v.get("verification_method", "online")
            v_counts[method] = v_counts.get(method, 0) + 1
            seed = f"{scheme_code}:verification:{method}"
            if v_counts[method] > 1:
                seed = f"{seed}:{v_counts[method]}"
            v_id = deterministic_uuid(seed)
            conn.execute(
                """
                INSERT OR REPLACE INTO scheme_verification (
                    id, scheme_id, verification_method, verification_url, helpline_number, last_verified_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    v_id,
                    scheme_id,
                    method,
                    v.get("verification_url"),
                    v.get("helpline_number"),
                    v.get("last_verified_at"),
                    v.get("notes"),
                ),
            )

        # Insert profile fields
        for pf in data.get("profile_fields", []):
            pf_id = deterministic_uuid(f"{scheme_code}:pf:{pf.get('field_name', '')}")
            allowed_vals = pf.get("allowed_values")
            conn.execute(
                """
                INSERT OR REPLACE INTO scheme_profile_fields (
                    id, scheme_id, field_name, field_type, is_required, allowed_values, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pf_id,
                    scheme_id,
                    pf.get("field_name", ""),
                    pf.get("field_type", "text"),
                    1 if pf.get("is_required", True) else 0,
                    json.dumps(allowed_vals, ensure_ascii=False) if allowed_vals is not None else None,
                    pf.get("description"),
                ),
            )

        seeded_count += 1

    logger.info("Successfully seeded %d canonical schemes into the database.", seeded_count)
    return seeded_count


# Supabase client factory
_supabase_client = None


def get_supabase_client() -> Any | None:
    """Return Supabase client if configured, else None."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from supabase import create_client

            _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            return _supabase_client
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to initialize Supabase client: %s", e)
            return None
    return None
