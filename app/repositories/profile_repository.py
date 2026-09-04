"""Repository layer for persisting citizen profiles."""

import json
from datetime import datetime, timezone
from typing import Any

from app.db.session import get_db_connection


class ProfileRepository:
    """Repository managing storage and retrieval of citizen profiles."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path

    def save_profile(
        self, profile_data: dict[str, Any], profile_id: str = "default"
    ) -> dict[str, Any]:
        """Insert or replace a citizen profile."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            # Check if profile exists to preserve original created_at
            cursor.execute("SELECT created_at FROM user_profiles WHERE id = ?", (profile_id,))
            existing = cursor.fetchone()
            created_at = existing["created_at"] if existing else now

            cursor.execute(
                """
                INSERT OR REPLACE INTO user_profiles (id, profile_data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (profile_id, json.dumps(profile_data, ensure_ascii=False), created_at, now),
            )
            return {
                "id": profile_id,
                "profile": profile_data,
                "created_at": created_at,
                "updated_at": now,
            }

    def get_profile(self, profile_id: str = "default") -> dict[str, Any] | None:
        """Retrieve stored profile by ID, or None if not found."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            if not row:
                return None

            try:
                profile_data = json.loads(row["profile_data"])
            except (ValueError, TypeError):
                profile_data = {}

            return {
                "id": row["id"],
                "profile": profile_data,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    @staticmethod
    def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge updates into base dictionary."""
        merged = dict(base)
        for k, v in updates.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = ProfileRepository._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    def update_profile(
        self, updates: dict[str, Any], profile_id: str = "default"
    ) -> dict[str, Any] | None:
        """Partially update an existing profile by merging updates into existing fields."""
        existing = self.get_profile(profile_id)
        if not existing:
            return None

        # Recursively merge new attributes without discarding existing attributes
        merged_profile = self._deep_merge(existing["profile"], updates)

        now = datetime.now(timezone.utc).isoformat()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE user_profiles
                SET profile_data = ?, updated_at = ?
                WHERE id = ?
                """,
                (json.dumps(merged_profile, ensure_ascii=False), now, profile_id),
            )

        return {
            "id": profile_id,
            "profile": merged_profile,
            "created_at": existing["created_at"],
            "updated_at": now,
        }
