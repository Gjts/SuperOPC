"""Unit tests for scripts/verify_command_contract.py.

These tests exercise the lint logic with ephemeral command files in tmp_path,
so they don't depend on the real repo commands/ state.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_command_contract.py"


@pytest.fixture
def lint_module(monkeypatch, tmp_path):
    """Load verify_command_contract.py as a module with REPO_ROOT redirected to tmp_path."""
    # Create a minimal skills/registry.json with at least one dispatcher.
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "registry.json").write_text(
        '{"skills":['
        '{"id":"planning","type":"dispatcher","dispatches_to":"opc-planner"},'
        '{"id":"debugging","type":"dispatcher","dispatches_to":"opc-debugger"}'
        "]}",
        encoding="utf-8",
    )
    (tmp_path / "commands" / "opc").mkdir(parents=True)

    # Load module fresh with patched paths.
    spec = importlib.util.spec_from_file_location("vcc_test_copy", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vcc_test_copy"] = mod
    spec.loader.exec_module(mod)

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "COMMANDS_DIR", tmp_path / "commands" / "opc")
    monkeypatch.setattr(mod, "SKILLS_REGISTRY", skills_dir / "registry.json")
    return mod


def _write_cmd(tmp_path: Path, stem: str, content: str) -> None:
    (tmp_path / "commands" / "opc" / f"{stem}.md").write_text(content, encoding="utf-8")


def test_command_that_dispatches_skill_passes(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "plan",
        "---\nname: opc-plan\ndescription: Plan\n---\n## 动作\n调用 `planning` skill。\n",
    )
    report = lint_module.verify()
    assert report.violations == []
    assert report.dispatchers == 1


def test_command_without_skill_dispatch_fails(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "foo",
        "---\nname: opc-foo\ndescription: Foo\n---\n## 动作\n调用 `python scripts/foo.py`。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    v = report.violations[0]
    assert v.command == "opc-foo"
    assert "does not dispatch" in v.issue


def test_local_runtime_command_allowed_to_call_script_directly(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "health",
        "---\nname: opc-health\ndescription: Health\n---\n"
        "## 动作\n"
        "调用 `python scripts/opc_health.py`。\n"
        "默认诊断只读；`--repair` 会做受控本地修复。\n",
    )
    report = lint_module.verify()
    assert report.violations == []
    assert report.whitelisted == 1
    assert report.local_runtime == 1
    assert report.mixed_low_friction == 0


def test_local_runtime_health_missing_repair_contract_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "health",
        "---\nname: opc-health\ndescription: Health\n---\n## 动作\n调用 `python scripts/opc_health.py`。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "--repair" in report.violations[0].issue


def test_local_runtime_profile_missing_record_contract_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "profile",
        "---\nname: opc-profile\ndescription: Profile\n---\n## 动作\n调用 `python bin/opc-tools profile $ARGUMENTS`。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "record" in report.violations[0].issue


def test_local_runtime_research_missing_feed_run_contract_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "research",
        "---\nname: opc-research\ndescription: Research\n---\n"
        "## 动作\n"
        "调用 `python bin/opc-tools research $ARGUMENTS`。\n"
        "支持 `insights`、`methods list/show`。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "feed" in report.violations[0].issue
    assert "run" in report.violations[0].issue


def test_opc_intel_refresh_requires_dispatcher_guard(lint_module, tmp_path):
    (tmp_path / "skills" / "registry.json").write_text(
        '{"skills":['
        '{"id":"planning","type":"dispatcher","dispatches_to":"opc-planner"},'
        '{"id":"debugging","type":"dispatcher","dispatches_to":"opc-debugger"},'
        '{"id":"workflow-modes","type":"dispatcher","dispatches_to":"opc-orchestrator"}'
        "]}",
        encoding="utf-8",
    )
    _write_cmd(
        tmp_path,
        "intel",
        "---\nname: opc-intel\ndescription: Intel\n---\n"
        "## 动作\n"
        "查询类子命令调用本地 runtime：`python bin/opc-tools intel $ARGUMENTS`。\n"
        "`refresh` 不走本地 runtime；调用 `workflow-modes` skill，并附加 `sub_scenario=intel-refresh`。\n",
    )
    report = lint_module.verify()
    assert report.violations == []
    assert report.local_runtime == 1


def test_opc_intel_refresh_local_runtime_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "intel",
        "---\nname: opc-intel\ndescription: Intel\n---\n"
        "## 动作\n"
        "调用本地 runtime：`python bin/opc-tools intel $ARGUMENTS`。\n"
        "`refresh` 由 `scripts/engine/intel_engine.py` 重建 `.opc/intel/`。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) >= 1
    issues = "\n".join(v.issue for v in report.violations)
    assert "refresh" in issues


def test_mixed_whitelist_command_with_marker_passes(lint_module, tmp_path):
    """档二 MIXED 命令：带 <!-- MIXED: ... --> 注释应通过。"""
    _write_cmd(
        tmp_path,
        "thread",
        "---\nname: opc-thread\ndescription: Thread\n---\n"
        "## 动作\n"
        "<!-- MIXED: list=readonly, create=writes .opc/threads/ -->\n"
        "调用 `python scripts/opc_thread.py`。\n",
    )
    report = lint_module.verify()
    assert report.violations == []
    assert report.mixed_low_friction == 1
    assert report.local_runtime == 0


def test_mixed_whitelist_command_without_marker_fails(lint_module, tmp_path):
    """档二 MIXED 命令：缺少 <!-- MIXED: ... --> 注释应被 lint 拦截。"""
    _write_cmd(
        tmp_path,
        "thread",
        "---\nname: opc-thread\ndescription: Thread\n---\n"
        "## 动作\n调用 `python scripts/opc_thread.py`。\n",
    )
    report = lint_module.verify()
    assert report.mixed_low_friction == 1
    assert len(report.violations) == 1
    v = report.violations[0]
    assert v.command == "opc-thread"
    assert "MIXED" in v.issue


def test_mixed_whitelist_marker_case_insensitive(lint_module, tmp_path):
    """档二 MIXED 注释匹配应大小写不敏感。"""
    _write_cmd(
        tmp_path,
        "seed",
        "---\nname: opc-seed\ndescription: Seed\n---\n"
        "## Action\n"
        "<!-- mixed: LIST=readonly, CREATE=writes .opc/seeds/ -->\n"
        "Calls `python scripts/opc_seed.py`.\n",
    )
    report = lint_module.verify()
    assert report.violations == []


def test_command_dispatching_skill_but_also_calling_script_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "build",
        "---\nname: opc-build\ndescription: Build\n---\n"
        "## 动作\n调用 `planning` skill。然后直接 `python scripts/opc_build.py`。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "direct local runtime invocation" in report.violations[0].issue


def test_command_dispatching_non_dispatcher_skill_fails(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "bar",
        "---\nname: opc-bar\ndescription: Bar\n---\n## 动作\n调用 `non-existent` skill。\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "does not dispatch" in report.violations[0].issue


def test_command_dispatching_skill_but_also_calling_bin_opc_tools_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "build-runtime",
        "---\nname: opc-build-runtime\ndescription: Build runtime\n---\n"
        "## Action\nDispatches the `planning` skill, then directly runs `python bin/opc-tools verify health`.\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "direct local runtime invocation" in report.violations[0].issue


def test_missing_frontmatter_is_flagged(lint_module, tmp_path):
    _write_cmd(tmp_path, "broken", "# /opc-broken\nno frontmatter\n")
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "frontmatter" in report.violations[0].issue.lower() or "---" in report.violations[0].issue


def test_english_dispatch_phrase_also_recognized(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "eng",
        "---\nname: opc-eng\ndescription: English\n---\n"
        "## Action\nDispatches the `debugging` skill to run the workflow.\n",
    )
    report = lint_module.verify()
    assert report.violations == []


def test_command_exceeding_line_budget_is_flagged(lint_module, tmp_path):
    _write_cmd(
        tmp_path,
        "long",
        "---\nname: opc-long\ndescription: Long\n---\n"
        "# /opc-long\n"
        "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\n"
        "## Action\n"
        "Dispatches the `planning` skill to run the workflow.\n"
        "line 7\nline 8\nline 9\n",
    )
    report = lint_module.verify()
    assert len(report.violations) == 1
    assert "entry budget" in report.violations[0].issue


def test_real_repo_commands_pass_contract():
    """Integration: run the actual script against the real repo."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"real repo commands violate the contract:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_workflow_modes_docs_cover_guarded_sub_scenarios():
    workflow_skill = (REPO_ROOT / "skills" / "using-superopc" / "workflow-modes" / "SKILL.md").read_text(encoding="utf-8")
    orchestrator_agent = (REPO_ROOT / "agents" / "opc-orchestrator.md").read_text(encoding="utf-8")

    assert "project-init" in workflow_skill
    assert "intel-refresh" in workflow_skill
    assert "project-init" in orchestrator_agent
    assert "intel-refresh" in orchestrator_agent
    assert "opc-intel-updater" in orchestrator_agent


def test_opc_intel_refresh_requires_dispatcher_guard(lint_module, tmp_path):
    (tmp_path / "skills" / "registry.json").write_text(
        '{"skills":['
        '{"id":"planning","type":"dispatcher","dispatches_to":"opc-planner"},'
        '{"id":"debugging","type":"dispatcher","dispatches_to":"opc-debugger"},'
        '{"id":"workflow-modes","type":"dispatcher","dispatches_to":"opc-orchestrator"}'
        "]}",
        encoding="utf-8",
    )
    _write_cmd(
        tmp_path,
        "intel",
        "---\nname: opc-intel\ndescription: Intel\n---\n"
        "## Actions\n"
        "Query subcommands call the local runtime: `python bin/opc-tools intel $ARGUMENTS`.\n"
        "For `refresh`, dispatch the `workflow-modes` skill with `sub_scenario=intel-refresh`.\n",
    )
    report = lint_module.verify()
    assert report.violations == []
    assert report.local_runtime == 1
