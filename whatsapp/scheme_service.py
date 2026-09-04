"""Reads scheme JSON files from data/schemes/ and provides lookup functions."""

import json
from pathlib import Path
from typing import Optional

from whatsapp.config import SCHEMES_DIR


_schemes_cache: dict[str, dict] = {}
_loaded = False


def _load_all() -> None:
    global _schemes_cache, _loaded
    if _loaded:
        return
    _schemes_cache.clear()
    if not SCHEMES_DIR.exists():
        _loaded = True
        return
    for path in sorted(SCHEMES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            code = data.get("scheme_code", path.stem)
            _schemes_cache[code] = data
        except (json.JSONDecodeError, OSError):
            continue
    _loaded = True


def reload_schemes() -> None:
    """Force reload from disk."""
    global _loaded
    _loaded = False
    _load_all()


def list_schemes() -> list[dict]:
    """Return a summary list of all schemes."""
    _load_all()
    result = []
    for code, data in _schemes_cache.items():
        result.append({
            "scheme_code": code,
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "scheme_type": data.get("scheme_type", ""),
            "tags": data.get("tags", []),
            "target_groups": data.get("target_groups", []),
        })
    return result


def get_scheme(scheme_code: str) -> Optional[dict]:
    """Return full scheme data by scheme_code."""
    _load_all()
    return _schemes_cache.get(scheme_code)


def get_scheme_names_indexed() -> list[dict]:
    """Return numbered list for display: [{index, scheme_code, name, scheme_type}]."""
    _load_all()
    result = []
    for idx, (code, data) in enumerate(_schemes_cache.items(), start=1):
        result.append({
            "index": idx,
            "scheme_code": code,
            "name": data.get("name", ""),
            "scheme_type": data.get("scheme_type", ""),
        })
    return result


def get_scheme_by_index(index: int) -> Optional[dict]:
    """Get scheme by 1-based display index."""
    _load_all()
    schemes = list(_schemes_cache.values())
    if 1 <= index <= len(schemes):
        return schemes[index - 1]
    return None


def get_scheme_code_by_index(index: int) -> Optional[str]:
    """Get scheme_code by 1-based display index."""
    _load_all()
    codes = list(_schemes_cache.keys())
    if 1 <= index <= len(codes):
        return codes[index - 1]
    return None


def get_scheme_documents(scheme_code: str) -> list[dict]:
    """Return documents for a scheme."""
    scheme = get_scheme(scheme_code)
    if not scheme:
        return []
    return scheme.get("documents", [])


def get_scheme_tutorial(scheme_code: str) -> list[dict]:
    """Return tutorial steps for a scheme, sorted by step_number."""
    scheme = get_scheme(scheme_code)
    if not scheme:
        return []
    steps = scheme.get("tutorial_steps", [])
    return sorted(steps, key=lambda s: s.get("step_number", 0))


def get_scheme_benefits(scheme_code: str) -> list[str]:
    """Return benefits list for a scheme."""
    scheme = get_scheme(scheme_code)
    if not scheme:
        return []
    return scheme.get("benefits", [])


def get_scheme_official_url(scheme_code: str) -> Optional[str]:
    """Return official URL if present."""
    scheme = get_scheme(scheme_code)
    if not scheme:
        return None
    return scheme.get("official_url")


def search_schemes(query: str) -> list[dict]:
    """Basic text search across name, description, and tags."""
    _load_all()
    q = query.lower()
    results = []
    for code, data in _schemes_cache.items():
        name = data.get("name", "").lower()
        desc = data.get("description", "").lower()
        tags = " ".join(data.get("tags", [])).lower()
        aliases = " ".join(data.get("aliases", [])).lower()
        if q in name or q in desc or q in tags or q in aliases:
            results.append({
                "scheme_code": code,
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "scheme_type": data.get("scheme_type", ""),
            })
    return results


def scheme_count() -> int:
    """Return total number of loaded schemes."""
    _load_all()
    return len(_schemes_cache)
