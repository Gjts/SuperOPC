from __future__ import annotations

import subprocess

from insights_helpers import (
    parse_next_roadmap_task,
    parse_git_info,
    parse_roadmap_progress,
    parse_state,
    parse_validation_debt,
)


def test_parse_roadmap_progress_and_next_task() -> None:
    roadmap_text = """# 路线图

## 进度

| 阶段 | 已完成计划 | 状态 | 完成时间 |
|------|-----------|------|---------|
| 基础 | 1 / 2 | 进行中 | - |
| 发布 | 3 / 3 | 已完成 | 2026-04-01 |

- [ ] 完成 dashboard polish
- [ ] 阶段 4 不应被当成 next task
"""

    rows = parse_roadmap_progress(roadmap_text)

    assert len(rows) == 2
    assert rows[0].phase == "基础"
    assert rows[0].completed_plans == 1
    assert rows[0].total_plans == 2
    assert rows[1].status == "已完成"
    assert parse_next_roadmap_task(roadmap_text) == "完成 dashboard polish"


def test_parse_state_extracts_position_and_lists() -> None:
    state_text = """# 项目状态

## 项目参考

**核心价值：** 更快恢复上下文
**当前焦点：** 会话恢复

## 当前位置

阶段：[1] / [3]（基础）
计划：[2] / [5]（当前阶段内）
状态：执行中
最近活动：[2026-04-11] — 新增 progress 命令
进度：[████░░░░░░] 40%

## 待办事项

- 清理 README 元数据

## 阻塞/关注

- 等待验证输出格式

## 会话连续性

上次会话：2026-04-10T10:00:00Z
停止于：完成 progress 草稿
恢复文件：.opc/STATE.md
"""

    state = parse_state(state_text)

    assert state["currentFocus"] == "会话恢复"
    assert state["status"] == "执行中"
    assert state["phase"] == {"current": "1", "total": "3", "name": "基础"}
    assert state["plan"] == {"current": "2", "total": "5"}
    assert state["progressPercent"] == 40
    assert state["blockers"] == ["等待验证输出格式"]
    assert state["todos"] == ["清理 README 元数据"]
    assert state["resumeFile"] == ".opc/STATE.md"


def test_parse_validation_debt_merges_and_dedupes_sources() -> None:
    state_text = """# 项目状态

## 验证欠债

- 未运行 CLI 冒烟测试
- 未运行 CLI 冒烟测试
"""

    debt = parse_validation_debt(
        state_text,
        {"available": True, "dirtyFiles": 2},
        ["未记录 MRR", "未记录 MRR"],
        extra_items=["未知需求 ID", "未知需求 ID"],
    )

    assert debt == [
        "未运行 CLI 冒烟测试",
        "未提交工作区变更：2 个文件",
        "未记录 MRR",
        "未知需求 ID",
    ]


def test_parse_git_info_retries_status_without_global_excludesfile(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    def fake_check_output(cmd, **kwargs):
        calls.append(cmd)
        assert kwargs.get("encoding") == "utf-8"
        assert kwargs.get("errors") == "replace"
        if cmd == ["git", "branch", "--show-current"]:
            return "main\n"
        if cmd == ["git", "status", "--short"]:
            raise subprocess.CalledProcessError(1, cmd)
        if cmd == ["git", "-c", "core.excludesfile=", "status", "--short"]:
            return " M scripts/opc_insights.py\n?? tests/test_insights_helpers.py\n"
        if cmd == ["git", "log", "-1", "--pretty=format:%h %cs %s"]:
            return "abc1234 2026-04-27 test commit"
        raise AssertionError(f"unexpected git command: {cmd}")

    monkeypatch.setattr("insights_helpers.subprocess.run", fake_run)
    monkeypatch.setattr("insights_helpers.subprocess.check_output", fake_check_output)

    git_info = parse_git_info(tmp_path)

    assert git_info == {
        "available": True,
        "branch": "main",
        "dirtyFiles": 2,
        "lastCommit": "abc1234 2026-04-27 test commit",
    }
    assert ["git", "-c", "core.excludesfile=", "status", "--short"] in calls
