from __future__ import annotations

import json
from pathlib import Path

from engine.intel_builders import (
    build_api_map_index,
    build_arch_decisions_index,
    build_dependency_graph_index,
    build_file_roles_index,
    build_stack_index,
)
from engine.intel_helpers import (
    diff_intel_snapshot,
    now_iso,
    query_intel_dir,
    status_for_intel_dir,
    take_snapshot,
    validate_intel_dir,
)


def test_query_intel_dir_matches_nested_values_and_keys(tmp_path: Path) -> None:
    intel_dir = tmp_path / "intel"
    intel_dir.mkdir()
    (intel_dir / "stack.json").write_text(
        json.dumps(
            {
                "_meta": {"updated_at": now_iso(), "version": 1},
                "frameworks": ["SuperOPC Engine"],
                "notes": {"primary": "router orchestration"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = query_intel_dir(intel_dir, "router")

    assert result["total"] == 1
    assert result["matches"][0]["source"] == "stack.json"
    assert result["matches"][0]["entries"][0]["key"] == "notes"


def test_status_validate_and_diff_cover_missing_and_changed_files(tmp_path: Path) -> None:
    intel_dir = tmp_path / "intel"
    intel_dir.mkdir()
    stack_file = intel_dir / "stack.json"
    stack_file.write_text(
        json.dumps({"_meta": {"updated_at": now_iso(), "version": 1}, "languages": ["Python"]}, indent=2),
        encoding="utf-8",
    )

    status = status_for_intel_dir(intel_dir)
    validation = validate_intel_dir(intel_dir)
    snapshot = take_snapshot(intel_dir)
    stack_file.write_text(
        json.dumps({"_meta": {"updated_at": now_iso(), "version": 2}, "languages": ["Python", "TypeScript"]}, indent=2),
        encoding="utf-8",
    )
    diff = diff_intel_snapshot(intel_dir)

    assert status["files"]["stack.json"]["exists"] is True
    assert status["overall_stale"] is True
    assert validation["valid"] is False
    assert any("file-roles.json: file does not exist" == err for err in validation["errors"])
    assert snapshot.exists()
    assert diff["changes"]["stack.json"]["status"] == "changed"


def test_builders_detect_routes_dependencies_roles_and_architecture(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    (project_root / "commands" / "opc").mkdir(parents=True)
    (project_root / "agents").mkdir(parents=True)
    (project_root / "skills" / "demo").mkdir(parents=True)
    (project_root / "scripts" / "engine").mkdir(parents=True)
    (project_root / "scripts" / "cli").mkdir(parents=True)

    (project_root / "commands" / "opc" / "demo.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
    (project_root / "agents" / "demo.md").write_text("---\nname: demo-agent\n---\n", encoding="utf-8")
    (project_root / "skills" / "demo" / "SKILL.md").write_text("---\nname: demo-skill\n---\n", encoding="utf-8")
    (project_root / "scripts" / "cli" / "router.py").write_text(
        "from engine.event_bus import EventBus\nelif command == \"demo\":\n    pass\nrouter.get(\"/health\")\n",
        encoding="utf-8",
    )
    (project_root / "requirements.txt").write_text("pytest\nrequests>=2\n", encoding="utf-8")
    (project_root / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^18.0.0"}, "devDependencies": {"vite": "^5.0.0"}}, indent=2),
        encoding="utf-8",
    )

    files = build_file_roles_index(project_root)
    apis = build_api_map_index(project_root)
    deps = build_dependency_graph_index(project_root)
    stack = build_stack_index(project_root)
    arch = build_arch_decisions_index(project_root, files)

    assert files["entries"]["commands/opc/demo.md"]["type"] == "command"
    assert files["entries"]["agents/demo.md"]["type"] == "agent"
    assert files["entries"]["scripts/cli/router.py"]["imports"] == ["engine.event_bus"]
    assert "CLI demo" in apis["entries"]
    assert "GET /health" in apis["entries"]
    assert deps["entries"]["requests"]["used_by"] == ["requirements.txt"]
    assert deps["entries"]["react"]["type"] == "production"
    assert deps["entries"]["vite"]["type"] == "development"
    assert "Python" in stack["languages"]
    assert "SuperOPC Engine" in stack["frameworks"]
    assert "ARCH-003" in arch["entries"]
