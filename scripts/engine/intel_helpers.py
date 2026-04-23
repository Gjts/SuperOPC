from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INTEL_FILES = {
    "stack": "stack.json",
    "files": "file-roles.json",
    "apis": "api-map.json",
    "deps": "dependency-graph.json",
    "arch": "arch-decisions.json",
}

STALE_SECONDS = 24 * 60 * 60
DISABLED_MESSAGE = "Intel system is disabled"


def disabled_payload() -> dict[str, Any]:
    return {"disabled": True, "message": DISABLED_MESSAGE}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""


def safe_read_json(filepath: Path) -> dict[str, Any] | None:
    try:
        if not filepath.exists():
            return None
        payload = json.loads(filepath.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def hash_file(filepath: Path) -> str | None:
    try:
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    except OSError:
        return None


def matches_in_value(value: Any, lower_term: str) -> bool:
    if isinstance(value, str):
        return lower_term in value.lower()
    if isinstance(value, list):
        return any(matches_in_value(item, lower_term) for item in value)
    if isinstance(value, dict):
        return any(matches_in_value(item, lower_term) for item in value.values())
    return False


def search_entries(data: Any, lower_term: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []

    results: list[dict[str, Any]] = []
    for key, value in data.items():
        if key == "_meta":
            continue
        if lower_term in key.lower() or matches_in_value(value, lower_term):
            results.append({"key": key, "value": value})
    return results


def query_intel_dir(intel_dir: Path, term: str) -> dict[str, Any]:
    lower_term = term.lower()
    matches: list[dict[str, Any]] = []
    total = 0

    for filename in INTEL_FILES.values():
        data = safe_read_json(intel_dir / filename)
        if data is None:
            continue

        entries = data.get("entries", data)
        found = search_entries(entries, lower_term)
        if found:
            matches.append({"source": filename, "entries": found})
            total += len(found)

    return {"matches": matches, "term": term, "total": total}


def status_for_intel_dir(intel_dir: Path) -> dict[str, Any]:
    now_ts = datetime.now(timezone.utc).timestamp()
    files_status: dict[str, dict[str, Any]] = {}
    overall_stale = False

    for filename in INTEL_FILES.values():
        filepath = intel_dir / filename
        if not filepath.exists():
            files_status[filename] = {"exists": False, "updated_at": None, "stale": True}
            overall_stale = True
            continue

        data = safe_read_json(filepath)
        updated_at = None
        if data and "_meta" in data:
            updated_at = data["_meta"].get("updated_at")

        stale = True
        if updated_at:
            try:
                updated_ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).timestamp()
                stale = (now_ts - updated_ts) > STALE_SECONDS
            except ValueError:
                stale = True

        if stale:
            overall_stale = True

        files_status[filename] = {
            "exists": True,
            "updated_at": updated_at,
            "stale": stale,
        }

    return {"files": files_status, "overall_stale": overall_stale}


def write_intel_payload(intel_dir: Path, key: str, data: dict[str, Any]) -> tuple[Path, int] | None:
    filename = INTEL_FILES.get(key)
    if filename is None:
        return None

    intel_dir.mkdir(parents=True, exist_ok=True)

    payload = dict(data)
    meta = dict(payload.get("_meta") or {})
    version = meta.get("version", 0)
    version = version + 1 if isinstance(version, int) else 1
    meta["updated_at"] = now_iso()
    meta["version"] = version
    payload["_meta"] = meta

    filepath = intel_dir / filename
    filepath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath, version


def take_snapshot(intel_dir: Path) -> Path:
    intel_dir.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "created_at": now_iso(),
        "hashes": {
            filename: hash_file(intel_dir / filename) if (intel_dir / filename).exists() else None
            for filename in INTEL_FILES.values()
        },
    }

    snapshot_file = intel_dir / ".last-refresh.json"
    snapshot_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot_file


def diff_intel_snapshot(intel_dir: Path) -> dict[str, Any]:
    snapshot_file = intel_dir / ".last-refresh.json"
    if not snapshot_file.exists():
        return {"error": "No snapshot recorded. Run /opc-intel refresh first."}

    snapshot = safe_read_json(snapshot_file)
    if snapshot is None:
        return {"error": "Snapshot file is invalid."}

    old_hashes = snapshot.get("hashes", {})
    changes: dict[str, dict[str, Any]] = {}
    for filename in INTEL_FILES.values():
        filepath = intel_dir / filename
        current_hash = hash_file(filepath) if filepath.exists() else None
        old_hash = old_hashes.get(filename)

        if current_hash and not old_hash:
            changes[filename] = {"status": "added"}
        elif old_hash and not current_hash:
            changes[filename] = {"status": "removed"}
        elif current_hash != old_hash:
            changes[filename] = {"status": "changed"}

    return {"changes": changes, "snapshot_at": snapshot.get("created_at", "unknown")}


def validate_intel_dir(intel_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    valid_count = 0

    for key, filename in INTEL_FILES.items():
        filepath = intel_dir / filename
        if not filepath.exists():
            errors.append(f"{filename}: file does not exist")
            continue

        data = safe_read_json(filepath)
        if data is None:
            errors.append(f"{filename}: invalid JSON")
            continue

        if "_meta" not in data:
            errors.append(f"{filename}: missing _meta object")
        elif "updated_at" not in data["_meta"]:
            errors.append(f"{filename}: missing _meta.updated_at")

        if key in {"files", "apis", "deps", "arch"} and "entries" not in data:
            errors.append(f"{filename}: missing entries object")

        valid_count += 1

    return {
        "valid": len(errors) == 0,
        "files_checked": len(INTEL_FILES),
        "valid_count": valid_count,
        "errors": errors,
    }
