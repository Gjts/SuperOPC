from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class UserScenario:
    key: str
    name: str
    role: str
    context: str
    goal: str
    validation: str
    commands: tuple[str, ...]


TEST_USERS = (
    UserScenario(
        key="status-observer",
        name="林岚",
        role="运营观测者",
        context="单人项目经营者，需要快速判断项目健康度和进度。",
        goal="在不改代码的前提下读取健康度、面板和统计信息。",
        validation="runtime",
        commands=("health", "dashboard", "stats"),
    ),
    UserScenario(
        key="context-curator",
        name="周默",
        role="上下文整理者",
        context="频繁记录想法、线索和延后事项。",
        goal="低摩擦创建或重新打开 thread / seed / backlog 条目。",
        validation="runtime",
        commands=("thread", "seed", "backlog"),
    ),
    UserScenario(
        key="session-builder",
        name="沈跃",
        role="会话恢复型开发者",
        context="跨天和跨上下文继续同一阶段工作。",
        goal="查看进度、暂停、恢复并导出会话报告。",
        validation="runtime+contract",
        commands=("progress", "pause", "resume", "session-report"),
    ),
    UserScenario(
        key="research-operator",
        name="许策",
        role="研究与索引维护者",
        context="同时关心个人画像、市场情报和代码索引。",
        goal="记录 profile、离线生成 insights、查询 methods、刷新 intel。",
        validation="runtime",
        commands=("profile", "research", "intel"),
    ),
    UserScenario(
        key="bounded-autonomy",
        name="顾行",
        role="受边界约束的自主推进者",
        context="希望在安全边界内自动推进计划，但保留人工检查点。",
        goal="进入 autonomous 计划并验证 cruise/heartbeat 契约入口。",
        validation="runtime+contract",
        commands=("autonomous", "cruise", "heartbeat"),
    ),
    UserScenario(
        key="workflow-orchestrator",
        name="程策",
        role="工作流编排者",
        context="依赖 slash 入口把任务交给 dispatcher skill 和 agent workflow。",
        goal="确保规划、构建、评审、发布、调试与业务入口持续遵守命令契约。",
        validation="contract",
        commands=("opc", "start", "plan", "build", "review", "ship", "debug", "security", "business"),
    ),
)


def create_acceptance_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "acceptance-project"
    opc_dir = project_root / ".opc"

    for relative in (
        "phases",
        "research",
        "debug",
        "quick",
        "todos",
        "threads",
        "seeds",
        "sessions",
        "intelligence",
        "intelligence/methodologies",
    ):
        (opc_dir / relative).mkdir(parents=True, exist_ok=True)

    (project_root / "commands" / "opc").mkdir(parents=True, exist_ok=True)
    (project_root / "agents").mkdir(parents=True, exist_ok=True)
    (project_root / "skills" / "demo").mkdir(parents=True, exist_ok=True)
    (project_root / "scripts" / "engine").mkdir(parents=True, exist_ok=True)
    (project_root / "scripts" / "cli").mkdir(parents=True, exist_ok=True)

    (opc_dir / "PROJECT.md").write_text(
        "# Acceptance Project\n\n"
        "## 项目参考\n"
        "**核心价值：** 更快恢复上下文\n\n"
        "## 商业指标\n"
        "- MRR：¥1200\n"
        "- Active Customers：12\n",
        encoding="utf-8",
    )
    (opc_dir / "REQUIREMENTS.md").write_text(
        "# Requirements\n\n"
        "- [x] **REQ-01** 支持会话恢复\n"
        "- [ ] **REQ-02** 输出 dashboard 结构化 JSON\n",
        encoding="utf-8",
    )
    (opc_dir / "ROADMAP.md").write_text(
        "# 路线图\n"
        "## 进度\n\n"
        "| 阶段 | 已完成计划 | 状态 | 完成时间 |\n"
        "|------|-----------|------|---------|\n"
        "| 基础 | 1 / 2 | 进行中 | - |\n\n"
        "- [ ] 完成 dashboard polish\n\n"
        "## 阶段 1\n"
        "- **需求**：[REQ-01, REQ-02]\n",
        encoding="utf-8",
    )
    (opc_dir / "STATE.md").write_text(
        "# 项目状态\n"
        "## 项目参考\n"
        "**核心价值：** 更快恢复上下文\n"
        "**当前焦点：** 会话恢复\n\n"
        "## 当前位置\n\n"
        "阶段：[1] / [2]（基础）\n"
        "计划：[1] / [2]（当前阶段内）\n"
        "状态：执行中\n"
        "最近活动：[2026-04-11] - 新增 progress 命令\n"
        "进度：[■■□□□] 40%\n\n"
        "## 待办事项\n\n"
        "- 清理 README 元数据\n\n"
        "## 阻塞/关注\n\n"
        "- 等待验证输出格式\n\n"
        "## 验证欠债\n\n"
        "- 未运行 CLI 冒烟测试\n\n"
        "## 会话连续性\n\n"
        "上次会话：2026-04-10T10:00:00Z\n"
        "停止于：完成 progress 草稿\n"
        "恢复文件：.opc/STATE.md\n",
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
                "updatedAt": "2026-04-10T10:00:00Z",
                "summary": {"stopPoint": "完成 progress 草稿", "reasonForPause": "跨会话交接"},
                "resumeFiles": [".opc/STATE.md"],
                "notes": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (opc_dir / "sessions" / "session-2026-04-11T00-00-00Z.json").write_text(
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
    (opc_dir / "market_feed_latest.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-04-23T00:00:00Z",
                "target_niche": "developer productivity",
                "sources_succeeded": ["github", "reddit", "hackernews"],
                "guardrail_status": "READY_FOR_EVALUATION",
                "github_trends": [
                    {
                        "repo": "acme/demo",
                        "stars": 4200,
                        "desc": "AI workflow orchestration",
                        "url": "https://github.com/acme/demo",
                        "created": "2026-04-20",
                        "language": "Python",
                        "topics": ["automation", "agents"],
                    }
                ],
                "reddit_mentions": [
                    {
                        "title": "Need better project memory",
                        "ups": 123,
                        "comments": 20,
                        "url": "https://reddit.com/r/startups/demo",
                        "subreddit": "startups",
                        "created": "2026-04-21",
                    }
                ],
                "hackernews_stories": [
                    {
                        "title": "Autonomous coding agents",
                        "points": 150,
                        "comments": 42,
                        "url": "https://news.ycombinator.com/item?id=1",
                        "author": "pg",
                        "created": "2026-04-22",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (project_root / "commands" / "opc" / "demo.md").write_text(
        "---\nname: demo\ndescription: Demo\n---\n",
        encoding="utf-8",
    )
    (project_root / "agents" / "demo.md").write_text(
        "---\nname: demo-agent\ndescription: Demo agent\n---\n",
        encoding="utf-8",
    )
    (project_root / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo skill\n---\n",
        encoding="utf-8",
    )
    (project_root / "scripts" / "cli" / "router.py").write_text(
        "from engine.event_bus import EventBus\n"
        "elif command == \"demo\":\n"
        "    pass\n"
        "router.get(\"/health\")\n",
        encoding="utf-8",
    )
    (project_root / "requirements.txt").write_text("pytest\nrequests>=2\n", encoding="utf-8")

    return project_root


def run_json(command: list[str], *, expected_code: int = 0) -> tuple[dict, subprocess.CompletedProcess[str]]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == expected_code, f"command failed: {' '.join(command)}\nstdout={result.stdout}\nstderr={result.stderr}"
    return json.loads(result.stdout), result


def test_user_persona_matrix_covers_all_command_entries() -> None:
    covered = {command for user in TEST_USERS for command in user.commands}
    actual = {path.stem for path in (REPO_ROOT / "commands" / "opc").glob("*.md")}

    assert covered == actual
    assert all(user.context and user.goal and user.validation for user in TEST_USERS)


def test_status_observer_can_monitor_health_dashboard_and_stats(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    health, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_health.py"), "--cwd", str(project_root), "--target", "project", "--json"]
    )
    dashboard, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_dashboard.py"), "--cwd", str(project_root), "--json"]
    )
    stats, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_stats.py"), "--cwd", str(project_root), "--json"]
    )

    assert health["ok"] is True
    assert health["resolvedTargets"] == ["project"]
    assert dashboard["projectName"] == "Acceptance Project"
    assert dashboard["state"]["resumeFile"] == ".opc/STATE.md"
    assert stats["project"]["name"] == "Acceptance Project"
    assert stats["progress"]["requirementsCompleted"] == 1


def test_context_curator_can_create_and_list_threads_seeds_and_backlog(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    thread_create, thread_result = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_thread.py"), "--cwd", str(project_root), "--json", "pricing page copy"]
    )
    seed_create, seed_result = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_seed.py"), "--cwd", str(project_root), "--json", "--trigger", "当 beta 结束时", "community launch"]
    )
    backlog_create, backlog_result = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_backlog.py"), "--cwd", str(project_root), "--json", "--note", "等本阶段结束后再做", "补充 docs"]
    )

    thread_list, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_thread.py"), "--cwd", str(project_root), "--json"]
    )
    seed_list, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_seed.py"), "--cwd", str(project_root), "--json"]
    )
    backlog_list, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_backlog.py"), "--cwd", str(project_root), "--json"]
    )

    assert thread_create["created"] is True
    assert thread_create["name"] == "pricing-page-copy"
    assert "[opc-thread] note:" in thread_result.stderr
    assert seed_create["id"] == "SEED-001"
    assert "[opc-seed] note:" in seed_result.stderr
    assert backlog_create["id"] == "BACKLOG-001"
    assert "[opc-backlog] note:" in backlog_result.stderr
    assert thread_list["items"][0]["name"] == "pricing-page-copy"
    assert seed_list["items"][0]["trigger"] == "当 beta 结束时"
    assert backlog_list["items"][0]["name"] == "补充-docs"


def test_session_builder_can_progress_pause_resume_report_and_plan_autonomously(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)

    progress, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_progress.py"), "--cwd", str(project_root), "--json"]
    )
    pause, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "opc_pause.py"),
            "--cwd",
            str(project_root),
            "--json",
            "--note",
            "先暂停",
            "--stop-point",
            "准备更新 README",
        ]
    )
    resume, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_resume.py"), "--cwd", str(project_root), "--json"]
    )
    report, _ = run_json(
        [sys.executable, str(REPO_ROOT / "scripts" / "opc_session_report.py"), "--cwd", str(project_root), "--json"]
    )

    state_file = project_root / ".opc" / "STATE.md"
    state_text = state_file.read_text(encoding="utf-8")
    state_text = state_text.replace("- 等待验证输出格式\n", "")
    state_text = state_text.replace("- 未运行 CLI 冒烟测试\n", "")
    state_file.write_text(state_text, encoding="utf-8")
    state_text = "\n".join(
        line for line in state_file.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("- ")
    )
    state_file.write_text(state_text + "\n", encoding="utf-8")

    autonomous, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "opc_autonomous.py"),
            "--cwd",
            str(project_root),
            "--json",
            "--interactive",
            "--only",
            "3",
        ]
    )

    assert progress["position"]["resumeFile"] == ".opc/STATE.md"
    assert pause["summary"]["stopPoint"] == "准备更新 README"
    assert resume["progress"]["position"]["focus"] == "会话恢复"
    assert report["recommendation"]["command"] == "/opc discuss"
    assert report["reportFile"].startswith(".opc/session-reports/")
    assert (project_root / report["reportFile"]).exists()
    assert autonomous["mode"] == "interactive"
    assert autonomous["recommendation"]["command"] == "/opc-autonomous --interactive"


def test_research_operator_can_manage_profile_generate_insights_and_refresh_intel(tmp_path: Path) -> None:
    project_root = create_acceptance_project(tmp_path)
    profile_dir = tmp_path / "profile-store"
    export_dir = tmp_path / "profile-export"

    profile_record, _ = run_json(
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
            json.dumps({"tech_stack": ["python", "nextjs"], "communication_style": "terse"}, ensure_ascii=False),
        ]
    )
    profile_show, _ = run_json(
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
        ]
    )
    profile_export, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "profile",
            "export",
            "--profile-dir",
            str(profile_dir),
            "--dir",
            str(export_dir),
        ]
    )
    research_insights, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "research",
            "insights",
        ]
    )
    research_method, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "research",
            "methods",
            "show",
            "mom-test",
        ]
    )
    intel_refresh, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "intel",
            "refresh",
        ]
    )
    intel_status, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "intel",
            "status",
        ]
    )
    intel_query, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "intel",
            "query",
            "demo",
        ]
    )
    intel_validate, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "intel",
            "validate",
        ]
    )
    intel_diff, _ = run_json(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--cwd",
            str(project_root),
            "--raw",
            "intel",
            "diff",
        ]
    )

    assert profile_record["recorded"] is True
    assert profile_show["developer_profile"]["communication_style"] == "terse"
    assert "nextjs" in profile_show["developer_profile"]["tech_stack_affinity"]
    assert Path(profile_export["exported"]).exists()
    assert research_insights["count"] >= 3
    assert research_method["found"] is True
    assert research_method["methodology"]["id"] == "mom-test"
    assert intel_refresh["ok"] is True
    assert intel_status["files"]["stack.json"]["exists"] is True
    assert intel_query["total"] >= 1
    assert intel_validate["valid"] is True
    assert intel_diff["changes"] == {}


def test_autonomy_and_dispatcher_users_are_guarded_by_contract_lint() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "verify_command_contract.py")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
