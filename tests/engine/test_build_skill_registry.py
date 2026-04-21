"""Contract tests for scripts/build_skill_registry.py (Phase A Wave 1.2).

These tests are authored BEFORE the generator script exists (TDD RED stage).
After the generator is implemented in Wave 2.1, running this file must go
from all-failing to all-passing without modification.

Contracts asserted:
  (a) Every SKILL.md under skills/ is represented in skills/registry.json
  (b) All skill ids are unique
  (c) Every skill.type is one of {dispatcher, atomic, meta, learning}
  (d) Every dispatcher-type skill has dispatches_to pointing to a real
      agent id in agents/registry.json
  (e) The generated registry passes skills/registry.schema.json validation
  (f) --check mode exits non-zero when the registry drifts from frontmatter
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
REGISTRY_PATH = SKILLS_DIR / "registry.json"
SCHEMA_PATH = SKILLS_DIR / "registry.schema.json"
AGENT_REGISTRY = REPO_ROOT / "agents" / "registry.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registry() -> dict:
    """Lazy-load the (possibly generated) skill registry."""
    if not REGISTRY_PATH.exists():
        pytest.fail(
            f"{REGISTRY_PATH.relative_to(REPO_ROOT)} not found; "
            "run `python scripts/build_skill_registry.py` first (Wave 2.1)."
        )
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def skill_md_files() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


@pytest.fixture(scope="module")
def agent_ids() -> set[str]:
    data = json.loads(AGENT_REGISTRY.read_text(encoding="utf-8"))
    return {a["id"] for a in data.get("agents", [])}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------

def test_skill_count_matches_registry(registry, skill_md_files):
    """(a) registry.skills[] length equals number of SKILL.md files on disk."""
    assert len(registry["skills"]) == len(skill_md_files), (
        f"Mismatch: {len(skill_md_files)} SKILL.md files on disk "
        f"but registry has {len(registry['skills'])} entries"
    )


def test_skill_ids_are_unique(registry):
    """(b) Every skill.id appears exactly once."""
    ids = [s["id"] for s in registry["skills"]]
    assert len(ids) == len(set(ids)), (
        f"Duplicate skill ids detected: {[i for i in ids if ids.count(i) > 1]}"
    )


def test_skill_types_are_whitelisted(registry):
    """(c) skill.type must be one of the four allowed categories."""
    allowed = {"dispatcher", "atomic", "meta", "learning"}
    for s in registry["skills"]:
        assert s["type"] in allowed, (
            f"skill {s['id']}: type={s.get('type')!r} not in {allowed}"
        )


def test_dispatcher_dispatches_to_real_agent(registry, agent_ids):
    """(d) Every dispatcher-type skill's dispatches_to points to a real agent."""
    dispatchers = [s for s in registry["skills"] if s.get("type") == "dispatcher"]
    assert dispatchers, "At least one dispatcher skill is expected"
    for s in dispatchers:
        target = s.get("dispatches_to")
        assert target, f"dispatcher {s['id']}: missing dispatches_to"
        assert target in agent_ids, (
            f"dispatcher {s['id']}: dispatches_to={target!r} "
            f"not found in agents/registry.json (known: {sorted(agent_ids)[:5]}...)"
        )


def test_registry_passes_json_schema(registry):
    """(e) registry.json validates against registry.schema.json."""
    import jsonschema
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(schema).validate(registry)


def test_registry_paths_exist(registry):
    """Every skill.path must point to an existing SKILL.md file."""
    for s in registry["skills"]:
        p = REPO_ROOT / s["path"]
        assert p.is_file(), f"skill {s['id']}: path {s['path']} does not exist"


def test_frontmatter_and_registry_core_fields_agree(registry, skill_md_files):
    """name / id in frontmatter should match registry entry for same path."""
    reg_by_path = {s["path"].replace("\\", "/"): s for s in registry["skills"]}
    for md in skill_md_files:
        rel = str(md.relative_to(REPO_ROOT)).replace("\\", "/")
        if rel not in reg_by_path:
            continue  # covered by test_skill_count_matches_registry
        fm = _frontmatter(md)
        entry = reg_by_path[rel]
        assert entry["name"] == fm.get("name"), (
            f"{rel}: registry.name={entry['name']!r} vs frontmatter.name={fm.get('name')!r}"
        )
        fm_id = fm.get("id") or fm.get("name")
        assert entry["id"] == fm_id, (
            f"{rel}: registry.id={entry['id']!r} vs frontmatter id/name={fm_id!r}"
        )


def test_check_mode_rejects_drift(tmp_path, monkeypatch):
    """(f) `build_skill_registry.py --check` exits non-zero if registry is stale."""
    script = REPO_ROOT / "scripts" / "build_skill_registry.py"
    if not script.exists():
        pytest.fail(
            f"{script.relative_to(REPO_ROOT)} not found; Wave 2.1 not yet done."
        )
    # Write a stale registry to a temp location and ask --check to validate it.
    stale = tmp_path / "registry.json"
    stale.write_text(
        json.dumps({"$schema": "x", "version": "0.0.0", "skills": []}),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(script), "--check", "--registry", str(stale)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0, (
        f"--check must exit non-zero for stale registry; "
        f"stdout={result.stdout[:200]} stderr={result.stderr[:200]}"
    )
