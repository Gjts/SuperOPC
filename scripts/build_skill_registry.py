#!/usr/bin/env python3
"""Build skills/registry.json from SKILL.md frontmatter.

Usage:
    python scripts/build_skill_registry.py              # generate & write
    python scripts/build_skill_registry.py --check      # validate only; non-zero on drift
    python scripts/build_skill_registry.py --registry PATH  # custom registry path (check)

Design: docs/adr/0001-skill-registry-schema.md
Tests:  tests/engine/test_build_skill_registry.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
DEFAULT_REGISTRY = SKILLS_DIR / "registry.json"
SCHEMA_PATH = SKILLS_DIR / "registry.schema.json"
AGENT_REGISTRY = REPO_ROOT / "agents" / "registry.json"

REGISTRY_VERSION = "2.0.0-phase-a"
ALLOWED_TYPES = {"dispatcher", "atomic", "meta", "learning"}


def _parse_frontmatter(md_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{md_path}: no YAML frontmatter delimited by ---")
    fm = yaml.safe_load(parts[1]) or {}
    if not isinstance(fm, dict):
        raise ValueError(f"{md_path}: frontmatter is not a mapping")
    return fm


def _rel_posix(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT)).replace("\\", "/")


def _build_entry(md_path: Path) -> dict[str, Any]:
    fm = _parse_frontmatter(md_path)
    name = fm.get("name")
    if not name:
        raise ValueError(f"{md_path}: missing frontmatter.name")

    skill_id = fm.get("id") or name
    skill_type = fm.get("type")
    if skill_type not in ALLOWED_TYPES:
        raise ValueError(
            f"{md_path}: type={skill_type!r} not in {sorted(ALLOWED_TYPES)}"
        )

    entry: dict[str, Any] = {
        "id": skill_id,
        "name": name,
        "path": _rel_posix(md_path),
        "type": skill_type,
        "description": fm.get("description", ""),
        "version": fm.get("version", "1.0.0"),
    }

    triggers = fm.get("triggers") or {}
    if isinstance(triggers, dict):
        norm: dict[str, list[str]] = {}
        for key in ("keywords", "phrases", "phases"):
            val = triggers.get(key)
            if val is None:
                continue
            if isinstance(val, list):
                norm[key] = [str(v) for v in val]
        if norm:
            entry["triggers"] = norm

    if fm.get("tags"):
        entry["tags"] = [str(t) for t in fm["tags"]]

    dispatches_to = fm.get("dispatches_to")
    if skill_type == "dispatcher":
        if not dispatches_to:
            raise ValueError(
                f"{md_path}: dispatcher must declare dispatches_to"
            )
        entry["dispatches_to"] = dispatches_to
    elif dispatches_to:
        entry["dispatches_to"] = dispatches_to

    deps = fm.get("dependencies")
    if isinstance(deps, dict):
        clean: dict[str, list[str]] = {}
        for key in ("downstream", "atomic", "references"):
            val = deps.get(key)
            if isinstance(val, list):
                clean[key] = [str(v) for v in val]
        if clean:
            entry["dependencies"] = clean

    if fm.get("priority") is not None:
        try:
            entry["priority"] = int(fm["priority"])
        except (TypeError, ValueError):
            pass

    if fm.get("deprecated"):
        entry["deprecated"] = bool(fm["deprecated"])

    return entry


def build_registry(skills_dir: Path = SKILLS_DIR) -> dict[str, Any]:
    """Scan every SKILL.md under skills_dir and build a registry document."""
    md_files = sorted(skills_dir.rglob("SKILL.md"))
    entries: list[dict[str, Any]] = []
    for md in md_files:
        entries.append(_build_entry(md))

    # Stable ordering for deterministic diff.
    entries.sort(key=lambda e: (e["type"], e["id"]))

    registry = {
        "$schema": "SuperOPC Skill Registry",
        "version": REGISTRY_VERSION,
        "description": "Generated from SKILL.md frontmatter. DO NOT EDIT MANUALLY.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skills": entries,
    }
    return registry


def _agent_ids() -> set[str]:
    if not AGENT_REGISTRY.exists():
        return set()
    data = json.loads(AGENT_REGISTRY.read_text(encoding="utf-8"))
    return {a["id"] for a in data.get("agents", []) if a.get("id")}


def _validate_cross_refs(registry: dict[str, Any]) -> list[str]:
    """Check dispatches_to targets exist in agents/registry.json."""
    errors: list[str] = []
    known = _agent_ids()
    if not known:
        errors.append(f"agents/registry.json missing or empty: {AGENT_REGISTRY}")
        return errors
    ids_seen: set[str] = set()
    for s in registry["skills"]:
        if s["id"] in ids_seen:
            errors.append(f"duplicate skill id: {s['id']}")
        ids_seen.add(s["id"])
        if s.get("type") == "dispatcher":
            target = s.get("dispatches_to")
            if not target:
                errors.append(f"{s['id']}: dispatcher missing dispatches_to")
            elif target not in known:
                errors.append(
                    f"{s['id']}: dispatches_to={target!r} not found in agents/registry.json"
                )
    return errors


def _validate_schema(registry: dict[str, Any]) -> list[str]:
    import jsonschema  # lazy import

    if not SCHEMA_PATH.exists():
        return [f"schema file missing: {SCHEMA_PATH}"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    return [f"schema: {e.message} @ {list(e.absolute_path)}" for e in validator.iter_errors(registry)]


def _strip_nondeterministic(registry: dict[str, Any]) -> dict[str, Any]:
    clone = dict(registry)
    clone.pop("generated_at", None)
    return clone


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _diff_registries(generated: dict[str, Any], existing: dict[str, Any]) -> list[str]:
    """Return human-readable drift lines; empty == in sync."""
    gen = _strip_nondeterministic(generated)
    ext = _strip_nondeterministic(existing)
    diffs: list[str] = []
    if gen.get("version") != ext.get("version"):
        diffs.append(f"registry.version: generated={gen.get('version')!r} existing={ext.get('version')!r}")
    gen_map = {s["id"]: s for s in gen.get("skills", [])}
    ext_map = {s["id"]: s for s in ext.get("skills", [])}
    only_gen = sorted(set(gen_map) - set(ext_map))
    only_ext = sorted(set(ext_map) - set(gen_map))
    for sid in only_gen:
        diffs.append(f"+ skill {sid} (present in frontmatter, missing in registry.json)")
    for sid in only_ext:
        diffs.append(f"- skill {sid} (in registry.json but no matching SKILL.md)")
    for sid in sorted(set(gen_map) & set(ext_map)):
        if gen_map[sid] != ext_map[sid]:
            diffs.append(f"~ skill {sid} differs between frontmatter and registry.json")
    return diffs


def check(registry_path: Path) -> tuple[bool, list[str]]:
    """Return (ok, messages)."""
    messages: list[str] = []
    try:
        generated = build_registry()
    except Exception as exc:  # generation itself failed -> not ok
        return False, [f"build failed: {exc}"]

    schema_errs = _validate_schema(generated)
    messages.extend(schema_errs)

    cross_errs = _validate_cross_refs(generated)
    messages.extend(cross_errs)

    if not registry_path.exists():
        messages.append(f"registry file missing: {registry_path}")
        return False, messages

    try:
        existing = _load_json(registry_path)
    except Exception as exc:
        messages.append(f"existing registry is not valid JSON: {exc}")
        return False, messages

    drift = _diff_registries(generated, existing)
    messages.extend(drift)

    ok = not schema_errs and not cross_errs and not drift
    return ok, messages


def write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate registry against frontmatter; exit non-zero on drift.",
    )
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY),
        help=f"Path to registry.json (default: {DEFAULT_REGISTRY})",
    )
    args = parser.parse_args(argv)

    registry_path = Path(args.registry).resolve()

    if args.check:
        ok, messages = check(registry_path)
        if messages:
            print("# skill registry drift report", file=sys.stderr)
            for m in messages:
                print(f"  - {m}", file=sys.stderr)
        if ok:
            print(f"OK: registry is in sync ({registry_path})")
            return 0
        print("DRIFT: registry is NOT in sync", file=sys.stderr)
        return 1

    registry = build_registry()
    schema_errs = _validate_schema(registry)
    cross_errs = _validate_cross_refs(registry)
    errs = schema_errs + cross_errs
    if errs:
        print("registry generation failed validation:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 2

    write_registry(registry_path, registry)
    print(
        f"wrote {registry_path.relative_to(REPO_ROOT)} "
        f"({len(registry['skills'])} skills)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
