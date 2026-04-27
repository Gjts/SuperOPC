from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cli.profile import parse_record_signals
from tests.test_user_scenarios import create_acceptance_project

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_template_project_root(tmp_path: Path) -> Path:
    project_root = tmp_path / "template-fill"
    project_root.mkdir(parents=True, exist_ok=False)
    (project_root / ".opc" / "phases").mkdir(parents=True, exist_ok=True)
    return project_root


def _make_state_project_root(tmp_path: Path) -> Path:
    root = tmp_path / "state"
    opc_dir = root / ".opc"
    opc_dir.mkdir(parents=True, exist_ok=False)
    (opc_dir / "STATE.md").write_text(
        "# 项目状态\n\n"
        "## 项目参考\n"
        "**核心价值：** 更快恢复上下文\n"
        "**当前焦点：** 会话恢复\n\n"
        "## 当前位置\n\n"
        "阶段：[1] / [2]（基础）\n"
        "计划：[1] / [2]（当前阶段内）\n"
        "状态：执行中\n"
        "最近活动：[2026-04-11] — 新增 progress 命令\n\n"
        "## 会话连续性\n\n"
        "上次会话：2026-04-10T10:00:00Z\n"
        "停止于：完成 progress 草稿\n"
        "恢复文件：.opc/STATE.md\n",
        encoding="utf-8",
    )
    return root


def test_init_new_project_succeeds_without_existing_opc_dir(tmp_path: Path) -> None:
    project_root = tmp_path / "empty-project"
    project_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "init",
            "new-project",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["opc_exists"] is False
    assert payload["recommended_command"] == "/opc-start"
    assert payload["project_root"].replace("\\", "/") == str(project_root).replace("\\", "/")


def test_init_new_project_does_not_reuse_parent_opc_dir(tmp_path: Path) -> None:
    parent_root = create_acceptance_project(tmp_path)
    nested_root = parent_root / "nested-new-project"
    nested_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(nested_root),
            "--raw",
            "init",
            "new-project",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["opc_exists"] is False
    assert payload["project_root"].replace("\\", "/") == str(nested_root).replace("\\", "/")


def test_verify_health_repair_scaffolds_nested_project_in_requested_cwd(tmp_path: Path) -> None:
    parent_root = create_acceptance_project(tmp_path)
    nested_root = parent_root / "nested-new-project"
    nested_root.mkdir()

    repair = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(nested_root),
            "--raw",
            "verify",
            "health",
            "--repair",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    stats = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(nested_root),
            "--raw",
            "stats",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    repair_payload = json.loads(repair.stdout)
    stats_payload = json.loads(stats.stdout)

    assert repair.returncode == 0
    assert repair_payload["healthy"] is True
    assert (nested_root / ".opc" / "PROJECT.md").exists()
    assert stats.returncode == 0
    assert stats_payload["project"]["root"].replace("\\", "/") == str(nested_root).replace("\\", "/")


def test_raw_pick_extracts_single_field(tmp_path: Path) -> None:
    project_root = tmp_path / "empty-project"
    project_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "--pick",
            "recommended_command",
            "init",
            "new-project",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "/opc-start"


def test_verify_health_matches_project_scaffold_from_opc_health(tmp_path: Path) -> None:
    project_root = tmp_path / "starter-project"
    project_root.mkdir()

    repair = subprocess.run(
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
    verify = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "verify",
            "health",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    repair_payload = json.loads(repair.stdout)
    verify_payload = json.loads(verify.stdout)

    assert repair.returncode == 0
    assert repair_payload["ok"] is True
    assert verify.returncode == 0
    assert verify_payload["healthy"] is True
    assert verify_payload["issues"] == []
    assert not any("todos/pending" in item or "todos/completed" in item for item in verify_payload["warnings"])


def test_list_todos_reads_flat_backlog_entries_created_by_current_runtime(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    create = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "opc_backlog.py"),
            "--cwd",
            str(project_root),
            "--json",
            "补充 docs",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "list-todos",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    init_result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "init",
            "todos",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    create_payload = json.loads(create.stdout)
    payload = json.loads(result.stdout)
    init_payload = json.loads(init_result.stdout)

    assert create.returncode == 0
    assert result.returncode == 0
    assert init_result.returncode == 0
    assert create_payload["id"] == "BACKLOG-001"
    assert payload["count"] == 1
    assert init_payload["count"] == 1
    assert payload["todos"][0]["file"].startswith("BACKLOG-001")
    assert payload["todos"][0]["status"] == "PARKED"
    assert payload["todos"][0]["title"] == "补充 docs"


def test_init_progress_reads_current_chinese_state_labels(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "init",
            "progress",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["current_focus"] == "会话恢复"
    assert payload["status"] == "执行中"
    assert payload["phase"] == "[1] / [2]（基础）"


def test_init_resume_reads_current_chinese_state_labels(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "init",
            "resume",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["current_focus"] == "会话恢复"
    assert payload["status"] == "执行中"
    assert payload["stop_point"] == "完成 progress 草稿"
    assert payload["resume_file"] == ".opc/STATE.md"


def test_parse_record_signals_accepts_relaxed_object_syntax() -> None:
    payload = parse_record_signals("{communication_style:terse,tech_stack:[python,nextjs],friction:quoting}")

    assert payload["communication_style"] == "terse"
    assert payload["tech_stack"] == ["python", "nextjs"]
    assert payload["friction"] == "quoting"


def test_profile_record_accepts_relaxed_signal_pairs_in_cli(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)
    profile_dir = tmp_path / "profile-store"

    record = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "profile",
            "record",
            "--profile-dir",
            str(profile_dir),
            "--command",
            "/opc-plan",
            "--project",
            "acceptance-project",
            "--signals",
            "{communication_style:terse,tech_stack:[python,nextjs],friction:quoting}",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    show = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "profile",
            "show",
            "--profile-dir",
            str(profile_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    record_payload = json.loads(record.stdout)
    show_payload = json.loads(show.stdout)
    profile = show_payload["developer_profile"]

    assert record.returncode == 0
    assert show.returncode == 0
    assert record_payload["recorded"] is True
    assert profile["communication_style"] == "terse"
    assert "python" in profile["tech_stack_affinity"]
    assert "nextjs" in profile["tech_stack_affinity"]
    assert "quoting" in profile["friction_triggers"]


def test_research_insights_human_output_is_actionable(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "research",
            "insights",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0
    assert "Research insights:" in result.stdout
    assert "[" in result.stdout
    assert "next:" in result.stdout


def test_research_insights_accepts_bom_feed_via_relative_project_path(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)
    feed_path = project_root / ".opc" / "market_feed_latest.json"
    original = feed_path.read_text(encoding="utf-8")
    feed_path.write_bytes(b"\xef\xbb\xbf" + original.encode("utf-8"))

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "research",
            "insights",
            "--feed",
            ".opc/market_feed_latest.json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["count"] >= 3


def test_dashboard_text_mode_is_console_safe_under_gbk(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "gbk"

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_dashboard.py"), "--cwd", str(project_root)],
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )

    stdout = result.stdout.decode("gbk", errors="replace")
    stderr = result.stderr.decode("gbk", errors="replace")

    assert result.returncode == 0, stderr
    assert "SuperOPC Dashboard" in stdout
    assert "CNY 1200" in stdout


def test_opc_tools_dashboard_raw_routes_to_insights_payload(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "dashboard",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["projectName"] == "Acceptance Project"
    assert payload["state"]["resumeFile"] == ".opc/STATE.md"


def test_opc_tools_stats_raw_routes_to_stats_payload(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "stats",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["project"]["name"] == "Acceptance Project"
    assert payload["progress"]["requirementsCompleted"] == 1


def test_roadmap_analyze_reads_localized_phase_headers(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)
    (project_root / ".opc" / "phases" / "01-foundation").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "roadmap",
            "analyze",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["total_phases"] == 1
    assert payload["phases"][0]["phase_number"] == "1"
    assert payload["phases"][0]["has_directory"] is True


def test_roadmap_get_phase_reads_localized_phase_header_with_name(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)
    (project_root / ".opc" / "ROADMAP.md").write_text(
        "# Roadmap\n\n"
        "## \u9636\u6bb5 1\uff1a\u57fa\u7840\n"
        "**\u76ee\u6807\uff1a** Restore context cleanly\n"
        "**\u9700\u6c42\uff1a** [REQ-01]\n"
        "**\u6210\u529f\u6807\u51c6\uff1a**\n"
        "  1. Resume command returns state\n\n"
        "## \u9636\u6bb5 2\uff1a\u4ea4\u4ed8\n"
        "- **Goal:** Ship safely\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "roadmap",
            "get-phase",
            "1",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["found"] is True
    assert payload["phase_name"] == "\u57fa\u7840"
    assert payload["goal"] == "Restore context cleanly"
    assert payload["requirements"] == "[REQ-01]"
    assert payload["success_criteria"] == ["Resume command returns state"]
    assert "Restore context cleanly" in payload["section"]
    assert "Ship safely" not in payload["section"]


def test_state_json_parses_chinese_state_fields(tmp_path: Path) -> None:
    project_root = _make_state_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "state",
            "json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["Current Focus"] == "会话恢复"
    assert payload["Status"] == "执行中"
    assert payload["Phase"] == "1"
    assert payload["Total Phases"] == "2"
    assert payload["Phase Name"] == "基础"
    assert payload["Current Plan"] == "1"
    assert payload["Total Plans in Phase"] == "2"
    assert payload["Recent Activity"] == "[2026-04-11] — 新增 progress 命令"
    assert payload["Last Session"] == "2026-04-10T10:00:00Z"
    assert payload["Stop Point"] == "完成 progress 草稿"
    assert payload["Resume File"] == ".opc/STATE.md"


def test_state_get_english_alias_reads_chinese_status(tmp_path: Path) -> None:
    project_root = _make_state_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "state",
            "get",
            "Status",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"Status": "执行中"}


def test_state_begin_phase_updates_chinese_position_lines(tmp_path: Path) -> None:
    project_root = _make_state_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "state",
            "begin-phase",
            "--phase",
            "2",
            "--name",
            "交付",
            "--plans",
            "3",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    state_text = (project_root / ".opc" / "STATE.md").read_text(encoding="utf-8")
    assert "阶段：[2] / [3]（交付）" in state_text
    assert "计划：[1] / [3]（当前阶段内）" in state_text
    assert "状态：执行中" in state_text


def test_template_fill_plan_defaults_optional_fields_when_flags_are_missing(tmp_path: Path) -> None:
    project_root = _make_template_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "template",
            "fill",
            "plan",
            "--phase",
            "1",
            "--name",
            "Onboarding MVP",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    created_path = project_root / payload["path"]
    created_text = created_path.read_text(encoding="utf-8")

    assert payload["created"] is True
    assert payload["path"].endswith("01-PLAN.md")
    assert "plan: 1" in created_text
    assert "type: execute" in created_text
    assert "wave: 1" in created_text


def test_template_fill_plan_keeps_explicit_plan_type_and_wave(tmp_path: Path) -> None:
    project_root = _make_template_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "template",
            "fill",
            "plan",
            "--phase",
            "1",
            "--plan",
            "2",
            "--type",
            "research",
            "--wave",
            "3",
            "--name",
            "Onboarding MVP",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    created_path = project_root / payload["path"]
    created_text = created_path.read_text(encoding="utf-8")

    assert payload["created"] is True
    assert payload["path"].endswith("02-PLAN.md")
    assert created_path.name == "02-PLAN.md"
    assert "plan: 2" in created_text
    assert "type: research" in created_text
    assert "wave: 3" in created_text


def test_template_fill_summary_defaults_plan_when_plan_flag_is_missing(tmp_path: Path) -> None:
    project_root = _make_template_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "template",
            "fill",
            "summary",
            "--phase",
            "1",
            "--name",
            "Onboarding MVP",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    created_path = project_root / payload["path"]
    created_text = created_path.read_text(encoding="utf-8")

    assert payload["created"] is True
    assert payload["path"].endswith("01-SUMMARY.md")
    assert created_path.name == "01-SUMMARY.md"
    assert "plan: 1" in created_text


def test_template_fill_verification_defaults_to_matching_plan_prefix(tmp_path: Path) -> None:
    project_root = _make_template_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "template",
            "fill",
            "verification",
            "--phase",
            "1",
            "--name",
            "Onboarding MVP",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    created_path = project_root / payload["path"]
    created_text = created_path.read_text(encoding="utf-8")

    assert payload["created"] is True
    assert payload["path"].endswith("01-VERIFICATION.md")
    assert created_path.name == "01-VERIFICATION.md"
    assert "plan: 1" in created_text
    assert "verification: 01-VERIFICATION" in created_text


def test_template_fill_verification_keeps_explicit_plan_prefix(tmp_path: Path) -> None:
    project_root = _make_template_project_root(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "template",
            "fill",
            "verification",
            "--phase",
            "1",
            "--plan",
            "2",
            "--name",
            "Onboarding MVP",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    created_path = project_root / payload["path"]
    created_text = created_path.read_text(encoding="utf-8")

    assert payload["created"] is True
    assert payload["path"].endswith("02-VERIFICATION.md")
    assert created_path.name == "02-VERIFICATION.md"
    assert "plan: 2" in created_text
    assert "verification: 02-VERIFICATION" in created_text
