from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cli import verify as verify_cli  # noqa: E402
from opc_quality import (  # noqa: E402
    collect_project_quality_report,
    collect_quality_report,
    collect_repo_quality_report,
    format_quality_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def create_quality_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "quality-project"
    opc_dir = project_root / ".opc"
    phase_dir = opc_dir / "phases" / "01-foundation"

    for name in ("phases", "research", "debug", "quick", "todos", "threads", "seeds", "sessions"):
        (opc_dir / name).mkdir(parents=True, exist_ok=True)
    phase_dir.mkdir(parents=True, exist_ok=True)

    (opc_dir / "PROJECT.md").write_text(
        "# Project\n\n## 项目参考\n\n**核心价值：** 质量系统可回归\n",
        encoding="utf-8",
    )
    (opc_dir / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n- [ ] **REQ-01** — Health command works\n- [ ] **REQ-02** — Verification traceability exists\n",
        encoding="utf-8",
    )
    (opc_dir / "ROADMAP.md").write_text(
        "# Roadmap\n\n## 阶段 1\n\n- **需求**：[REQ-01, REQ-02]\n",
        encoding="utf-8",
    )
    (opc_dir / "STATE.md").write_text(
        "# State\n\n## 会话连续性\n\n恢复文件：.opc/STATE.md\n",
        encoding="utf-8",
    )
    (opc_dir / "config.json").write_text(
        json.dumps(
            {
                "workflow": {
                    "nyquist": True,
                    "node_repair": True,
                    "requirements_gate": True,
                    "regression_gate": True,
                    "schema_drift": True,
                    "scope_guard": True,
                    "claim_traceability": True,
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (opc_dir / "HANDOFF.json").write_text(
        json.dumps(
            {
                "resumeFiles": [".opc/STATE.md"],
                "notes": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (phase_dir / "01-SUMMARY.md").write_text(
        """---
phase: 01-foundation
summary: 01-SUMMARY
requirements-completed: [REQ-01, REQ-02]
---

# 阶段 1 总结

## 声明溯源
- 需求来源：REQ-01, REQ-02
""",
        encoding="utf-8",
    )
    (phase_dir / "01-VERIFICATION.md").write_text(
        """---
phase: 01-foundation
verification: 01-VERIFICATION
requirements-verified: [REQ-01, REQ-02]
---

# 阶段 1 验证

## 声明溯源
- 验证证据：pytest
""",
        encoding="utf-8",
    )

    return project_root


def create_quality_repo(
    tmp_path: Path,
    *,
    version: str = "0.9.0",
    broken_link: bool = False,
    add_workflows: bool = True,
) -> Path:
    repo_root = tmp_path / "quality-repo"

    required_dirs = [
        ".claude-plugin",
        "agents",
        "commands/opc",
        "docs",
        "hooks",
        "integrations",
        "references",
        "rules/common",
        "scripts/hooks",
        "skills/example-skill",
        "templates",
        "tests",
    ]
    for relative in required_dirs:
        (repo_root / relative).mkdir(parents=True, exist_ok=True)

    (repo_root / "agents").mkdir(parents=True, exist_ok=True)
    (repo_root / "agents" / "example.md").write_text(
        "---\nname: example-agent\ndescription: Example agent\n---\n\n# Agent\n",
        encoding="utf-8",
    )
    (repo_root / "agents" / "domain").mkdir(parents=True, exist_ok=True)
    (repo_root / "commands" / "opc" / "example.md").write_text(
        "---\nname: example-command\ndescription: Example command\n---\n\n# Command\n",
        encoding="utf-8",
    )
    (repo_root / "skills" / "example-skill" / "SKILL.md").write_text(
        "---\nname: example-skill\ndescription: Example skill\n---\n\n# Skill\n",
        encoding="utf-8",
    )
    (repo_root / "integrations" / "README.md").write_text(
        "# Integrations Output\n\n"
        "`integrations/` is a generated-output directory.\n\n"
        "Source of truth lives in `agents/`, `commands/`, `skills/`, and `scripts/convert.py`.\n\n"
        "Do not manually edit runtime files under `integrations/<tool>/`.\n\n"
        "Regenerate them with `python scripts/convert.py --tool all`.\n",
        encoding="utf-8",
    )
    (repo_root / "docs" / "DIRECTORY-MAP.md").write_text(
        "# Directory Map\n\n"
        "| Path | Notes |\n"
        "| --- | --- |\n"
        "| `marketing/` | launch assets |\n"
        "| `website/` | landing page |\n"
        "| `integrations/` | generated runtime output |\n"
        "| `.manual_verify/` | manual verification temp files |\n"
        "| `.pytest_tmp/` | legacy pytest temp files |\n"
        "| `.test_tmp/` | controlled test workspace |\n"
        "| `pytest-cache-files-*` | transient pytest cache directories |\n",
        encoding="utf-8",
    )
    (repo_root / ".gitignore").write_text(
        "integrations/*\n"
        "!integrations/\n"
        "!integrations/README.md\n"
        ".manual_verify/\n"
        ".pytest_tmp/\n"
        ".test_tmp/\n"
        "pytest-cache-files-*/\n",
        encoding="utf-8",
    )
    (repo_root / "scripts" / "convert.py").write_text("print('convert')\n", encoding="utf-8")
    (repo_root / "scripts" / "hooks" / "mock.py").write_text("print('ok')\n", encoding="utf-8")
    (repo_root / "README.md").write_text(
        "# Repo\n\n[Broken](docs/missing.md)\n" if broken_link else "# Repo\n",
        encoding="utf-8",
    )

    (repo_root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": "quality-repo",
                "version": version,
                "agents": ["./agents/example.md"],
                "hooks": ["./hooks/hooks.json"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (repo_root / "hooks" / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/hooks/mock.py",
                                }
                            ],
                        }
                    ]
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if add_workflows:
        workflows_dir = repo_root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "quality.yml").write_text("name: quality\n", encoding="utf-8")
        (workflows_dir / "release.yml").write_text("name: release\n", encoding="utf-8")

    return repo_root


def test_project_quality_report_passes_for_well_formed_project(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)

    report = collect_project_quality_report(project_root)

    assert report["ok"] is True
    assert report["summary"]["fail"] == 0
    assert report["qualitySignals"]["requirementsCoverageDebt"] == 0
    assert report["qualitySignals"]["traceabilityDebt"] == 0
    assert report["validationDebt"] == []


def test_project_quality_report_warns_for_missing_verification_and_traceability(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    phase_dir = project_root / ".opc" / "phases" / "01-foundation"

    (phase_dir / "01-VERIFICATION.md").unlink()
    (phase_dir / "01-SUMMARY.md").write_text(
        """---
phase: 01-foundation
summary: 01-SUMMARY
requirements-completed: [REQ-01, REQ-02]
---

# 阶段 1 总结
""",
        encoding="utf-8",
    )

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is True
    assert checks["project.verification-files"]["status"] == "warn"
    assert checks["project.claim-traceability"]["status"] == "warn"
    assert report["qualitySignals"]["regressionDebt"] >= 1
    assert report["qualitySignals"]["traceabilityDebt"] >= 1
    assert report["validationDebt"] == []


def test_project_quality_report_fails_on_unknown_requirement_ids(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    phase_dir = project_root / ".opc" / "phases" / "01-foundation"

    (phase_dir / "01-VERIFICATION.md").write_text(
        """---
phase: 01-foundation
verification: 01-VERIFICATION
requirements-verified: [REQ-99]
---

# 阶段 1 验证

## 声明溯源
- 验证证据：pytest
""",
        encoding="utf-8",
    )

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["project.verification-requirements"]["status"] == "fail"
    assert report["summary"]["fail"] >= 1
    assert "未知需求 ID" in report["validationDebt"][0]


def test_project_quality_report_fails_on_unmapped_requirements(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    roadmap_file = project_root / ".opc" / "ROADMAP.md"
    roadmap_file.write_text(
        "# Roadmap\n\n## 阶段 1\n\n- **需求**：[REQ-01]\n",
        encoding="utf-8",
    )

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["project.requirements-coverage"]["status"] == "fail"
    assert "REQ-02" in checks["project.requirements-coverage"]["details"]


def test_project_quality_repair_merges_missing_quality_flags(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    config_file = project_root / ".opc" / "config.json"
    config_file.write_text(
        json.dumps({"workflow": {"nyquist": True}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = collect_project_quality_report(project_root, repair=True)
    repaired = json.loads(config_file.read_text(encoding="utf-8"))
    checks = {check["id"]: check for check in report["checks"]}

    assert checks["project.config-quality-flags"]["status"] == "fixed"
    assert repaired["workflow"]["nyquist"] is True
    assert repaired["workflow"]["node_repair"] is True
    assert repaired["workflow"]["claim_traceability"] is True


def test_repo_quality_report_passes_current_repository_state() -> None:
    report = collect_repo_quality_report(REPO_ROOT)

    assert report["ok"] is True
    assert report["summary"]["fail"] == 0
    assert report["validationDebt"] == []


def test_collect_quality_report_all_includes_project_result_for_standalone_fixture(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)

    report = collect_quality_report(project_root, target="all")

    assert report["ok"] is True
    assert report["resolvedTargets"] == ["project"]
    assert len(report["results"]) == 1


def test_collect_quality_report_auto_resolves_project_when_opc_exists(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)

    report = collect_quality_report(project_root, target="auto")

    assert report["resolvedTargets"] == ["project"]
    assert report["results"][0]["target"] == "project"


def test_project_quality_report_warns_on_schema_drift_signal(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    prisma_dir = project_root / "prisma"
    prisma_dir.mkdir()
    (prisma_dir / "schema.prisma").write_text("datasource db {}\n", encoding="utf-8")

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is True
    assert checks["project.schema-drift"]["status"] == "warn"
    assert report["qualitySignals"]["schemaDriftDebt"] >= 1


def test_project_quality_report_warns_on_missing_resume_file_reference(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    state_file = project_root / ".opc" / "STATE.md"
    state_file.write_text("# State\n\n## 会话连续性\n\n恢复文件：.opc/MISSING.md\n", encoding="utf-8")

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is True
    assert checks["project.resume-files"]["status"] == "warn"
    assert ".opc/MISSING.md" in checks["project.resume-files"]["details"]


def test_project_quality_report_warns_on_missing_verification_requirements_field(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    verification_file = project_root / ".opc" / "phases" / "01-foundation" / "01-VERIFICATION.md"
    verification_file.write_text(
        """---
phase: 01-foundation
verification: 01-VERIFICATION
---

# 阶段 1 验证

## 声明溯源
- 验证证据：pytest
""",
        encoding="utf-8",
    )

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is True
    assert checks["project.verification-requirements"]["status"] == "warn"
    assert str(verification_file) in checks["project.verification-requirements"]["files"]


def test_project_quality_report_fails_on_invalid_handoff_json(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    handoff_file = project_root / ".opc" / "HANDOFF.json"
    handoff_file.write_text("{not-json}", encoding="utf-8")

    report = collect_project_quality_report(project_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["project.handoff"]["status"] == "fail"
    assert ".opc/HANDOFF.json" not in report["validationDebt"]


def test_format_quality_report_includes_targets_and_check_lines(tmp_path: Path) -> None:
    project_root = create_quality_project(tmp_path)
    payload = collect_quality_report(project_root, target="project")

    rendered = format_quality_report(payload)

    assert "SuperOPC Health" in rendered
    assert "targets: project" in rendered
    assert "[project]" in rendered
    assert "project.opc-dir" in rendered


def test_project_quality_report_fails_without_opc_dir(tmp_path: Path) -> None:
    project_root = tmp_path / "empty-project"
    project_root.mkdir()

    report = collect_project_quality_report(project_root)
    check = report["checks"][0]

    assert report["ok"] is False
    assert check["id"] == "project.opc-dir"
    assert check["status"] == "fail"
    assert check["repairable"] is True


def test_repo_quality_report_flags_broken_links_missing_workflows_and_version(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path, version="invalid", broken_link=True, add_workflows=False)

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.internal-links"]["status"] == "fail"
    assert checks["repo.ci-workflows"]["status"] == "fail"
    assert checks["repo.version"]["status"] == "fail"
    assert report["qualitySignals"]["regressionDebt"] >= 1


def test_repo_quality_report_warns_on_transient_workspace_artifacts(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    (repo_root / ".manual_verify").mkdir()
    (repo_root / "pytest-cache-files-temp").mkdir()

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is True
    assert checks["repo.transient-dirs"]["status"] == "warn"
    assert ".manual_verify" in checks["repo.transient-dirs"]["details"]
    assert "pytest-cache-files-temp" in checks["repo.transient-dirs"]["details"]


def test_repo_quality_report_repair_removes_transient_workspace_artifacts(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    (repo_root / ".manual_verify").mkdir()
    (repo_root / "pytest-cache-files-temp").mkdir()

    report = collect_repo_quality_report(repo_root, repair=True)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is True
    assert checks["repo.transient-dirs"]["status"] == "fixed"
    assert not (repo_root / ".manual_verify").exists()
    assert not (repo_root / "pytest-cache-files-temp").exists()
    assert "removed .manual_verify" in report["repairs"]
    assert "removed pytest-cache-files-temp" in report["repairs"]


def test_repo_quality_report_fails_on_missing_generated_artifact_policy(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    (repo_root / "integrations" / "README.md").unlink()

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.generated-artifacts"]["status"] == "fail"
    assert "missing generated artifact policy integrations/README.md" in checks["repo.generated-artifacts"]["details"][0]


def test_repo_quality_report_fails_on_missing_gitignore_workspace_policy(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    (repo_root / ".gitignore").write_text("integrations/*\n", encoding="utf-8")

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.gitignore-policy"]["status"] == "fail"
    assert any(".manual_verify/" in detail for detail in checks["repo.gitignore-policy"]["details"])


def test_repo_quality_report_fails_on_incomplete_directory_map(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    (repo_root / "docs" / "DIRECTORY-MAP.md").write_text("# Directory Map\n\n| Path | Notes |\n| --- | --- |\n| `integrations/` | generated |\n", encoding="utf-8")

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.directory-map"]["status"] == "fail"
    assert any("`website/`" in detail for detail in checks["repo.directory-map"]["details"])


def test_repo_quality_report_fails_on_invalid_hook_registry_reference(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    hooks_file = repo_root / "hooks" / "hooks.json"
    hooks_file.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python ${CLAUDE_PLUGIN_ROOT}/scripts/hooks/missing.py",
                                }
                            ],
                        }
                    ]
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.hook-registry"]["status"] == "fail"
    assert any("missing hook script scripts/hooks/missing.py" in detail for detail in checks["repo.hook-registry"]["details"])


def test_repo_quality_report_fails_on_invalid_plugin_manifest_reference(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    plugin_file = repo_root / ".claude-plugin" / "plugin.json"
    plugin_file.write_text(
        json.dumps(
            {
                "name": "quality-repo",
                "version": "0.9.0",
                "agents": ["./agents/missing.md"],
                "hooks": ["./hooks/hooks.json"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.plugin-manifest"]["status"] == "fail"
    assert any("missing referenced path ./agents/missing.md" in detail for detail in checks["repo.plugin-manifest"]["details"])


def test_repo_quality_report_fails_on_missing_frontmatter_in_domain_agent(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    bad_agent = repo_root / "agents" / "domain" / "bad-agent.md"
    bad_agent.write_text("# Missing frontmatter\n", encoding="utf-8")

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.frontmatter"]["status"] == "fail"
    assert any("agents/domain/bad-agent.md: missing frontmatter" in detail.replace("\\", "/") for detail in checks["repo.frontmatter"]["details"])


def test_repo_quality_report_fails_on_missing_description_in_domain_agent(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)
    bad_agent = repo_root / "agents" / "domain" / "bad-agent.md"
    bad_agent.write_text("---\nname: bad-agent\n---\n\n# Agent\n", encoding="utf-8")

    report = collect_repo_quality_report(repo_root)
    checks = {check["id"]: check for check in report["checks"]}

    assert report["ok"] is False
    assert checks["repo.frontmatter"]["status"] == "fail"
    assert any("agents/domain/bad-agent.md: missing description" in detail.replace("\\", "/") for detail in checks["repo.frontmatter"]["details"])


def test_opc_health_cli_fails_for_missing_opc_dir(tmp_path: Path) -> None:
    project_root = tmp_path / "cli-fail-project"
    project_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "opc_health.py"),
            "--cwd",
            str(project_root),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["ok"] is False
    assert payload["resolvedTargets"] == ["project"]
    assert payload["results"][0]["checks"][0]["id"] == "project.opc-dir"


def test_collect_quality_report_repo_target_for_standalone_repo_fixture(tmp_path: Path) -> None:
    repo_root = create_quality_repo(tmp_path)

    payload = collect_quality_report(repo_root, target="repo")

    assert payload["ok"] is True
    assert payload["resolvedTargets"] == ["repo"]
    assert payload["results"][0]["target"] == "repo"


def test_format_quality_report_includes_repairs_for_fixed_project(tmp_path: Path) -> None:
    project_root = tmp_path / "repairable-project"
    project_root.mkdir()

    payload = collect_quality_report(project_root, target="project", repair=True)
    rendered = format_quality_report(payload)

    assert "repairs:" in rendered
    assert "project.opc-dir" in rendered
    assert "[FIXED]" in rendered


def test_opc_health_cli_repair_scaffolds_a_healthy_starter_project(tmp_path: Path) -> None:
    project_root = tmp_path / "cli-repair-project"
    project_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "opc_health.py"),
            "--cwd",
            str(project_root),
            "--repair",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)
    checks = {check["id"]: check for check in payload["results"][0]["checks"]}

    assert result.returncode == 0
    assert payload["ok"] is True
    assert payload["results"][0]["summary"]["fixed"] >= 3
    assert (project_root / ".opc" / "HANDOFF.json").exists()
    assert checks["project.requirements-coverage"]["status"] == "pass"
    assert checks["project.core-files"]["status"] == "fixed"


def test_verify_plan_structure_passes_for_gate_approved_plan(tmp_path: Path, monkeypatch) -> None:
    project_root = create_quality_project(tmp_path)
    plan_file = project_root / "PLAN.md"
    plan_file.write_text(
        """# Demo Plan

**Goal:** Ship the feature safely

## Task 1
- [ ] Implement feature
- [ ] Add tests

<opc-plan>
<metadata><goal>Ship the feature safely</goal></metadata>
<waves>
  <wave id="1" description="Initial wave">
    <task id="1.1"><title>Implement</title><file>app.py</file><action>Add feature</action></task>
  </wave>
</waves>
</opc-plan>

## OPC Plan Check
### 判决: APPROVED

## OPC Assumptions Analysis
### 🟢 已验证假设
- API shape confirmed

## OPC Pre-flight Gate

- plan-check: APPROVED
- assumptions: PASS
- ready-for-build: true
""",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_output(data, raw=False, text=None):
        captured["data"] = data
        captured["raw"] = raw
        captured["text"] = text
        raise SystemExit(0)

    monkeypatch.setattr(verify_cli, "output", fake_output)

    try:
        verify_cli.cmd_verify_plan_structure(project_root, "PLAN.md", raw=True)
    except SystemExit:
        pass

    payload = captured["data"]
    assert isinstance(payload, dict)
    assert payload["valid"] is True
    assert payload["has_plan_check"] is True
    assert payload["has_assumptions_analysis"] is True
    assert payload["preflight_gate"]["ready-for-build"] == "true"


def test_verify_plan_structure_fails_when_preflight_gate_missing(tmp_path: Path, monkeypatch) -> None:
    project_root = create_quality_project(tmp_path)
    plan_file = project_root / "PLAN.md"
    plan_file.write_text(
        """# Demo Plan

**Goal:** Ship the feature safely

## Task 1
- [ ] Implement feature
- [ ] Add tests

<opc-plan>
<metadata><goal>Ship the feature safely</goal></metadata>
<waves>
  <wave id="1" description="Initial wave">
    <task id="1.1"><title>Implement</title><file>app.py</file><action>Add feature</action></task>
  </wave>
</waves>
</opc-plan>
""",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_output(data, raw=False, text=None):
        captured["data"] = data
        raise SystemExit(0)

    monkeypatch.setattr(verify_cli, "output", fake_output)

    try:
        verify_cli.cmd_verify_plan_structure(project_root, "PLAN.md", raw=True)
    except SystemExit:
        pass

    payload = captured["data"]
    assert isinstance(payload, dict)
    assert payload["valid"] is False
    assert "Missing ## OPC Plan Check section" in payload["errors"]
    assert "Missing ## OPC Assumptions Analysis section" in payload["errors"]
    assert "Missing ## OPC Pre-flight Gate section" in payload["errors"]
