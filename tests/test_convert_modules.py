from __future__ import annotations

from pathlib import Path

import convert_renderers
import convert_sources
from convert_sources import ParsedMarkdown, SourceFile


def make_source(*, kind: str = "skill", name: str = "Demo Skill", body: str = "# Body\n") -> SourceFile:
    return SourceFile(
        kind=kind,
        path=Path("skills/engineering/demo-skill/SKILL.md"),
        relative_path=Path("skills/engineering/demo-skill/SKILL.md"),
        parsed=ParsedMarkdown(
            meta={"name": name, "description": "Demo description", "tools": ["AskUserQuestion", "Skill"]},
            body=body,
        ),
    )


def test_collect_skill_files_excludes_supporting_markdown(tmp_path: Path) -> None:
    original_root = convert_sources.REPO_ROOT
    original_dirs = convert_sources.SKILL_DIRS
    try:
        convert_sources.REPO_ROOT = tmp_path
        convert_sources.SKILL_DIRS = ["skills/engineering"]

        skill_dir = tmp_path / "skills" / "engineering" / "agent-dispatch"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
        (skill_dir / "implementer-prompt.md").write_text("# Prompt\n", encoding="utf-8")

        skill_files = convert_sources.collect_skill_files(convert_sources.SKILL_DIRS)
        assert [path.name for path in skill_files] == ["SKILL.md"]
    finally:
        convert_sources.REPO_ROOT = original_root
        convert_sources.SKILL_DIRS = original_dirs


def test_collect_skill_assets_includes_supporting_markdown(tmp_path: Path) -> None:
    original_root = convert_sources.REPO_ROOT
    original_dirs = convert_sources.SKILL_DIRS
    try:
        convert_sources.REPO_ROOT = tmp_path
        convert_sources.SKILL_DIRS = ["skills/engineering"]

        skill_dir = tmp_path / "skills" / "engineering" / "agent-dispatch"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
        (skill_dir / "implementer-prompt.md").write_text("# Prompt\n", encoding="utf-8")
        (skill_dir / "notes.txt").write_text("ignored\n", encoding="utf-8")

        assets = convert_sources.collect_skill_assets(convert_sources.SKILL_DIRS)
        assert [path.name for path in assets] == ["implementer-prompt.md"]
    finally:
        convert_sources.REPO_ROOT = original_root
        convert_sources.SKILL_DIRS = original_dirs


def test_runtime_output_path_uses_runtime_layouts(tmp_path: Path) -> None:
    source = make_source()

    assert convert_renderers.runtime_output_path("claude-code", source, tmp_path) == tmp_path / "claude-code" / source.relative_path
    assert convert_renderers.runtime_output_path("codex", source, tmp_path) == tmp_path / "codex" / "skills" / "demo-skill.md"
    assert convert_renderers.runtime_output_path("gemini-cli", source, tmp_path) == tmp_path / "gemini-cli" / "skills" / "demo-skill" / "SKILL.md"


def test_adapt_body_rewrites_paths_and_tool_names_for_codex() -> None:
    source = make_source(
        body=(
            "Use ~/.claude/skills/demo/ and .claude/commands/opc/.\n"
            "Claude Code can AskUserQuestion before loading Skill.\n"
        )
    )

    adapted = convert_renderers.adapt_body(source, "codex")

    assert "~/.codex/skills/demo/" in adapted
    assert ".codex/commands/opc/" in adapted
    assert "Codex can ask-user before loading prompt." in adapted
