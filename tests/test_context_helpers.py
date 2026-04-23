from __future__ import annotations

import os
from pathlib import Path

from context_helpers import entry_summary, list_entries, next_index, resolve_existing, slugify, write_text


def test_slugify_preserves_chinese_and_normalizes_separators() -> None:
    assert slugify("  Viral Referral Loop  ") == "viral-referral-loop"
    assert slugify("整理 onboarding 文案") == "整理-onboarding-文案"
    assert slugify("!!!") == "item"


def test_next_index_and_resolve_existing_work_for_prefixed_entries(tmp_path: Path) -> None:
    directory = tmp_path / "seeds"
    write_text(
        directory / "SEED-001-growth-loop.md",
        "---\nname: growth-loop\nstatus: DORMANT\nupdatedAt: 2026-04-11T00:00:00Z\n---\n\n# Seed: Growth Loop\n",
    )
    write_text(
        directory / "SEED-002-community-launch.md",
        "---\nname: community-launch\nstatus: DORMANT\nupdatedAt: 2026-04-12T00:00:00Z\ntrigger: 当 beta 结束时\n---\n\n# Seed: Community Launch\n",
    )

    assert next_index(directory, "SEED") == 3
    assert resolve_existing(directory, "community launch") == directory / "SEED-002-community-launch.md"
    assert resolve_existing(directory, "growth-loop") == directory / "SEED-001-growth-loop.md"


def test_entry_summary_and_list_entries_return_latest_first(tmp_path: Path) -> None:
    directory = tmp_path / "threads"
    first = directory / "first-thread.md"
    second = directory / "second-thread.md"

    write_text(
        first,
        "---\nname: first-thread\nstatus: OPEN\nupdatedAt: 2026-04-11T00:00:00Z\n---\n\n# Thread: First\n",
    )
    write_text(
        second,
        "---\nname: second-thread\nstatus: IN_PROGRESS\nupdatedAt: 2026-04-12T00:00:00Z\n---\n\n# Thread: Second\n",
    )
    os.utime(first, (1_000_000, 1_000_000))
    os.utime(second, (1_000_100, 1_000_100))

    summary = entry_summary(second)
    entries = list_entries(directory)

    assert summary["name"] == "second-thread"
    assert summary["status"] == "IN_PROGRESS"
    assert summary["title"] == "Thread: Second"
    assert [Path(item["path"]).name for item in entries] == ["second-thread.md", "first-thread.md"]
