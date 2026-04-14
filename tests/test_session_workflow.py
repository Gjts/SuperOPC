from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

from opc_context import handle_backlog, handle_seed, handle_thread  # noqa: E402
from opc_insights import collect_project_insights  # noqa: E402
from opc_workflow import (  # noqa: E402
    collect_autonomous_plan,
    collect_progress_snapshot,
    collect_session_report,
    pause_project,
    resume_project,
)


def create_sample_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "sample-project"
    opc_dir = project_root / ".opc"
    sessions_dir = opc_dir / "sessions"
    todos_dir = opc_dir / "todos"
    sessions_dir.mkdir(parents=True)
    todos_dir.mkdir(parents=True)

    (opc_dir / "PROJECT.md").write_text(
        "# Sample Project\n\n## 项目参考\n\n**核心价值：** 更快恢复上下文\n\n## 商业指标\n\n- MRR：¥0\n",
        encoding="utf-8",
    )
    (opc_dir / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n- [x] 已完成需求\n- [ ] 未完成需求\n",
        encoding="utf-8",
    )
    (opc_dir / "ROADMAP.md").write_text(
        "# 路线图\n\n## 进度\n\n| 阶段 | 已完成计划 | 状态 | 完成时间 |\n|------|-----------|------|---------|\n| 基础 | 1 / 2 | 进行中 | - |\n\n- [ ] 下一个计划\n",
        encoding="utf-8",
    )
    (opc_dir / "STATE.md").write_text(
        "# 项目状态\n\n## 项目参考\n\n**核心价值：** 更快恢复上下文\n**当前焦点：** 会话恢复\n\n## 当前位置\n\n阶段：[1] / [2]（基础）\n计划：[1] / [2]（当前阶段内）\n状态：执行中\n最近活动：[2026-04-11] — 新增 progress 命令\n\n进度：[████░░░░░░] 40%\n\n## 待办事项\n\n- 清理 README 元数据\n\n## 阻塞/关注\n\n- 等待验证输出格式\n\n## 验证欠债\n\n- 未运行 CLI 冒烟测试\n\n## 会话连续性\n\n上次会话：2026-04-10T10:00:00Z\n停止于：完成 progress 草稿\n恢复文件：.opc/STATE.md\n",
        encoding="utf-8",
    )
    (sessions_dir / "session-2026-04-11T00-00-00Z.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-04-11T00:00:00Z",
                "tool_name": "Bash",
                "session_id": "session-1",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (opc_dir / "audit.log").write_text(
        "[2026-04-11T00:00:00Z] python scripts/opc_progress.py\n",
        encoding="utf-8",
    )
    return project_root


def test_collect_project_insights_includes_session_fields(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)

    insights = collect_project_insights(project_root)

    assert insights["state"]["resumeFile"] == ".opc/STATE.md"
    assert insights["state"]["blockers"] == ["等待验证输出格式"]
    assert insights["state"]["todos"] == ["清理 README 元数据"]
    assert Path(insights["files"]["handoff"]).name == "HANDOFF.json"
    assert Path(insights["files"]["handoff"]).parent.name == ".opc"


def test_progress_snapshot_exposes_validation_debt_and_resume_file(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)

    snapshot = collect_progress_snapshot(project_root)

    assert snapshot["position"]["resumeFile"] == ".opc/STATE.md"
    assert "未运行 CLI 冒烟测试" in snapshot["validationDebt"]
    assert snapshot["recommendation"]["command"] == "/opc-discuss"


def test_pause_and_resume_round_trip(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)

    handoff = pause_project(project_root, note="先暂停", stop_point="准备更新 README")
    handoff_file = project_root / ".opc" / "HANDOFF.json"

    assert handoff_file.exists()
    saved = json.loads(handoff_file.read_text(encoding="utf-8"))
    assert saved["notes"] == ["先暂停"]
    assert saved["summary"]["stopPoint"] == "准备更新 README"

    state_text = (project_root / ".opc" / "STATE.md").read_text(encoding="utf-8")
    assert "停止于：准备更新 README" in state_text
    assert "恢复文件：" in state_text and "HANDOFF.json" in state_text

    resumed = resume_project(project_root)
    assert resumed["handoff"]["notes"] == ["先暂停"]
    assert resumed["progress"]["position"]["focus"] == "会话恢复"

    resumed_state_text = (project_root / ".opc" / "STATE.md").read_text(encoding="utf-8")
    assert "恢复文件：.opc/STATE.md" in resumed_state_text
    assert "已从 HANDOFF.json 恢复上下文" in resumed_state_text


def test_autonomous_plan_degrades_to_discuss_when_blocked(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)

    plan = collect_autonomous_plan(project_root, from_index=2, to_index=4)

    assert plan["mode"] == "blocked"
    assert plan["recommendation"]["command"] == "/opc-discuss"
    assert plan["window"]["from"] == 2
    assert plan["window"]["to"] == 4
    assert ".opc/STATE.md" in plan["resumeFiles"]


def test_autonomous_plan_respects_only_range_and_interactive_mode(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)
    state_file = project_root / ".opc" / "STATE.md"
    state_text = state_file.read_text(encoding="utf-8")
    state_text = state_text.replace("- 等待验证输出格式\n", "")
    state_text = state_text.replace("- 未运行 CLI 冒烟测试\n", "")
    state_file.write_text(state_text, encoding="utf-8")

    plan = collect_autonomous_plan(project_root, only=3, interactive=True)

    assert plan["mode"] == "interactive"
    assert plan["interactive"] is True
    assert plan["window"]["only"] == 3
    assert plan["window"]["from"] == 3
    assert plan["window"]["to"] == 3
    assert plan["recommendation"]["command"] == "/opc-autonomous --interactive"


def test_context_commands_create_thread_seed_and_backlog_entries(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)
    opc_dir = project_root / ".opc"

    thread_output = handle_thread(opc_dir, "pricing-page-copy", as_json=False)
    seed_output = handle_seed(opc_dir, "viral referral loop", "当激活率停滞时", as_json=False)
    backlog_output = handle_backlog(opc_dir, "整理 onboarding 文案", "等本阶段结束后再做", as_json=False)

    thread_file = opc_dir / "threads" / "pricing-page-copy.md"
    seed_file = opc_dir / "seeds" / "SEED-001-viral-referral-loop.md"
    backlog_file = opc_dir / "todos" / "BACKLOG-001-整理-onboarding-文案.md"

    assert "Thread created" in thread_output
    assert "Seed created" in seed_output
    assert "Backlog item created" in backlog_output
    assert thread_file.exists()
    assert seed_file.exists()
    assert backlog_file.exists()
    assert "trigger: 当激活率停滞时" in seed_file.read_text(encoding="utf-8")
    assert "等本阶段结束后再做" in backlog_file.read_text(encoding="utf-8")


def test_context_commands_list_existing_entries(tmp_path: Path) -> None:
    project_root = create_sample_project(tmp_path)
    opc_dir = project_root / ".opc"

    handle_thread(opc_dir, "supabase-migration-risk", as_json=False)
    handle_seed(opc_dir, "community launch", "当 beta 结束时", as_json=False)
    handle_backlog(opc_dir, "补充 docs", "当前先不做", as_json=False)

    threads_listing = handle_thread(opc_dir, "", as_json=False)
    seeds_listing = handle_seed(opc_dir, "", "", as_json=False)
    backlog_listing = handle_backlog(opc_dir, "", "", as_json=False)

    assert "SuperOPC Threads" in threads_listing
    assert "supabase-migration-risk" in threads_listing
    assert "SuperOPC Seeds" in seeds_listing
    assert "community-launch" in seeds_listing
    assert "trigger=当 beta 结束时" in seeds_listing
    assert "SuperOPC Backlog" in backlog_listing
    assert "补充-docs" in backlog_listing


def test_convert_all_updates_generated_runtime_metadata_and_commands(tmp_path: Path) -> None:
    out_dir = tmp_path / "integrations"

    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "convert.py"), "--tool", "all", "--out", str(out_dir)],
        check=True,
        cwd=REPO_ROOT,
    )

    runtime_map = json.loads((out_dir / "claude-code" / "runtime-map.json").read_text(encoding="utf-8"))
    assert runtime_map["pluginVersion"] == "1.0.0"

    claude_plugin = json.loads((out_dir / "claude-code" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert claude_plugin["version"] == "1.0.0"
    assert not (out_dir / "claude-code" / ".claude-plugin" / "marketplace.json").exists()

    assert (out_dir / "claude-code" / "commands" / "opc" / "progress.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "pause.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "resume.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "session-report.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "autonomous.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "thread.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "seed.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "backlog.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "profile.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "research.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "intel.md").exists()
    assert (out_dir / "claude-code" / "commands" / "opc" / "plan.md").exists()

    profile_cmd = (out_dir / "claude-code" / "commands" / "opc" / "profile.md").read_text(encoding="utf-8")
    research_cmd = (out_dir / "claude-code" / "commands" / "opc" / "research.md").read_text(encoding="utf-8")
    intel_cmd = (out_dir / "claude-code" / "commands" / "opc" / "intel.md").read_text(encoding="utf-8")
    plan_cmd = (out_dir / "claude-code" / "commands" / "opc" / "plan.md").read_text(encoding="utf-8")

    assert "python bin/opc-tools profile show" in profile_cmd
    assert "feed -> insights -> methodology -> report -> extracted-skills" in research_cmd
    assert "IntelEngine.refresh()" in intel_cmd
    assert "opc-plan-checker" in plan_cmd


