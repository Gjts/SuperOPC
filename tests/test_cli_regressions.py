from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cli.profile import parse_record_signals
from tests.test_user_scenarios import create_acceptance_project

REPO_ROOT = Path(__file__).resolve().parents[1]


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
