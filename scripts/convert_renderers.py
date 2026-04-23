from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from convert_runtime_registry import (
    DETECTION_MARKERS,
    GEMINI_TOOL_MAPPING,
    PLUGIN_VERSION,
    REPO_ROOT,
    RUNTIME_CONFIGS,
    RUNTIME_ORDER,
    SKILL_DIRS,
    STATIC_CLAUDE_EXPORTS,
    TODAY,
)
from convert_sources import SourceFile, collect_skill_assets, extract_tools, map_tools, slugify


def ensure_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)


def write_file(file_path: Path, content: str) -> None:
    ensure_dir(file_path.parent)
    file_path.write_text(content, encoding="utf-8")


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if text == "":
        return '""'
    if any(token in text for token in (":", "#", "[", "]", "{", "}")) or text.strip() != text:
        return json.dumps(text, ensure_ascii=False)
    return text


def render_frontmatter(meta: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if value is None or value == "" or value == []:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {yaml_scalar(item)}")
            continue
        lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def replace_tool_names(text: str, mapping: dict[str, str]) -> str:
    result = text
    for source_name in sorted(mapping, key=len, reverse=True):
        target_name = mapping[source_name]
        if source_name == target_name:
            continue
        pattern = rf"(?<![A-Za-z0-9_-]){re.escape(source_name)}(?![A-Za-z0-9_-])"
        result = re.sub(pattern, target_name, result)
    return result


def apply_path_replacements(text: str, config: dict[str, Any]) -> str:
    config_dir = config["config_dir"]
    skills_dir = config["skills_dir"]
    agents_dir = config["agents_dir"]
    commands_dir = config["commands_dir"]
    instruction_file = config["instruction_file"]

    replacements = [
        ("~/.claude/skills/", f"~/{skills_dir}/"),
        ("~/.claude/agents/", f"~/{agents_dir}/"),
        ("~/.claude/commands/", f"~/{commands_dir}/"),
        ("$HOME/.claude/skills/", f"$HOME/{skills_dir}/"),
        ("$HOME/.claude/agents/", f"$HOME/{agents_dir}/"),
        ("$HOME/.claude/commands/", f"$HOME/{commands_dir}/"),
        ("./.claude/", f"./{config_dir}/"),
        (".claude/skills/", f"{skills_dir}/"),
        (".claude/agents/", f"{agents_dir}/"),
        (".claude/commands/", f"{commands_dir}/"),
        (".agents/skills/", f"{skills_dir}/"),
        ("~/.claude/", f"~/{config_dir}/"),
        ("$HOME/.claude/", f"$HOME/{config_dir}/"),
        (".claude/", f"{config_dir}/"),
    ]

    result = text
    for old, new in replacements:
        result = result.replace(old, new)

    if instruction_file != "CLAUDE.md":
        result = result.replace("CLAUDE.md", instruction_file)

    return result


def adapt_body(source: SourceFile, runtime: str) -> str:
    config = RUNTIME_CONFIGS[runtime]
    body = source.parsed.body
    body = apply_path_replacements(body, config)
    body = replace_tool_names(body, config["tool_mapping"])
    if runtime != "claude-code":
        body = body.replace("Claude Code", config["display_name"])
    if runtime == "gemini-cli":
        body = body.replace("${", "$")
    return body.rstrip() + "\n"


def render_rule_markdown(source: SourceFile, runtime: str) -> str:
    meta = {
        "name": source.name,
        "description": source.description,
        "source-kind": source.kind,
    }
    return render_frontmatter(meta) + adapt_body(source, runtime)


def render_agent_markdown(source: SourceFile, runtime: str) -> str:
    meta: dict[str, Any] = {
        "name": source.name,
        "description": source.description,
        "source-kind": source.kind,
    }
    if source.kind == "agent":
        meta["mode"] = "subagent"
    return render_frontmatter(meta) + adapt_body(source, runtime)


def render_copilot_instruction(source: SourceFile) -> str:
    meta = {
        "applyTo": "**",
        "description": source.description or f"SuperOPC {source.kind}",
        "source-kind": source.kind,
    }
    title = f"# {source.name}\n\n"
    return render_frontmatter(meta) + title + adapt_body(source, "copilot")


def render_gemini_skill(source: SourceFile) -> str:
    meta: dict[str, Any] = {
        "name": slugify(source.name),
        "description": source.description,
        "source-kind": source.kind,
    }
    if source.kind == "agent":
        tools = map_tools(extract_tools(source), GEMINI_TOOL_MAPPING)
        if tools:
            meta["tools"] = tools
    return render_frontmatter(meta) + adapt_body(source, "gemini-cli")


def split_openclaw_body(body: str, name: str, description: str) -> tuple[str, str]:
    soul_sections: list[str] = []
    agent_sections: list[str] = []
    current_target = "agents"
    current_lines: list[str] = []

    def flush(target: str, lines: list[str]) -> None:
        section = "\n".join(lines).strip()
        if not section:
            return
        if target == "soul":
            soul_sections.append(section)
        else:
            agent_sections.append(section)

    for line in body.splitlines():
        if line.startswith("## "):
            flush(current_target, current_lines)
            current_lines = []
            lowered = line.lower()
            if any(token in lowered for token in ("identity", "communication", "style", "critical.rule", "rules.you.must")):
                current_target = "soul"
            else:
                current_target = "agents"
        current_lines.append(line)

    flush(current_target, current_lines)
    soul = "\n\n".join(soul_sections).strip() or f"# {name}\n\n{description}\n"
    agents = "\n\n".join(agent_sections).strip() or body
    return soul.rstrip() + "\n", agents.rstrip() + "\n"


def runtime_slug(source: SourceFile) -> str:
    return slugify(source.name or source.path.stem)


def runtime_output_path(runtime: str, source: SourceFile, out_dir: Path) -> Path:
    slug = runtime_slug(source)
    if runtime == "claude-code":
        return out_dir / "claude-code" / source.relative_path
    if runtime == "cursor":
        return out_dir / "cursor" / "rules" / f"{slug}.mdc"
    if runtime == "gemini-cli":
        return out_dir / "gemini-cli" / "skills" / slug / "SKILL.md"
    if runtime == "copilot":
        return out_dir / "copilot" / "instructions" / f"{slug}.instructions.md"
    if runtime == "opencode":
        folder = "agents" if source.kind == "agent" else f"{source.kind}s"
        return out_dir / "opencode" / folder / f"{slug}.md"
    if runtime == "codex":
        folder = "agents" if source.kind == "agent" else f"{source.kind}s"
        return out_dir / "codex" / folder / f"{slug}.md"
    if runtime == "trae":
        return out_dir / "trae" / "rules" / f"{slug}.md"
    if runtime == "cline":
        return out_dir / "cline" / ".clinerules" / f"{slug}.md"
    if runtime == "augment":
        return out_dir / "augment" / "rules" / f"{slug}.md"
    return out_dir / "openclaw" / slug


def write_runtime_metadata(runtime: str, out_dir: Path) -> None:
    config = RUNTIME_CONFIGS[runtime]
    runtime_root = out_dir / runtime
    metadata = {
        "runtime": runtime,
        "displayName": config["display_name"],
        "pluginVersion": PLUGIN_VERSION,
        "generatedAt": TODAY,
        "toolMappingMode": "semantic",
        "toolMapping": config["tool_mapping"],
        "hookEventMapping": config["hook_mapping"],
    }
    write_file(runtime_root / "runtime-map.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")

    lines = [
        f"# {config['display_name']} hook mapping\n",
        "| Claude Code event | Target mapping | Status | Notes |\n",
        "|---|---|---|---|\n",
    ]
    for event in ("PreToolUse", "PostToolUse", "Notification", "Stop"):
        item = config["hook_mapping"][event]
        mapped_to = item["mappedTo"] if item["mappedTo"] else "manual"
        lines.append(f"| {event} | {mapped_to} | {item['status']} | {item['notes']} |\n")
    write_file(runtime_root / "HOOKS.md", "".join(lines))


def convert_claude_code(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    runtime_root = out_dir / "claude-code"
    for source in sources:
        write_file(runtime_root / source.relative_path, source.path.read_text(encoding="utf-8"))
        count += 1

    for asset in collect_skill_assets(SKILL_DIRS):
        write_file(runtime_root / asset.relative_to(REPO_ROOT), asset.read_text(encoding="utf-8"))

    for relative in STATIC_CLAUDE_EXPORTS:
        source_path = REPO_ROOT / relative
        if source_path.exists():
            write_file(runtime_root / relative, source_path.read_text(encoding="utf-8"))
    write_runtime_metadata("claude-code", out_dir)
    return count


def convert_cursor(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        content = render_frontmatter({"description": source.description, "globs": "", "alwaysApply": False}) + adapt_body(source, "cursor")
        write_file(runtime_output_path("cursor", source, out_dir), content)
        count += 1
    write_runtime_metadata("cursor", out_dir)
    return count


def convert_windsurf(sources: list[SourceFile], out_dir: Path) -> int:
    parts = [
        "# SuperOPC - AI Rules for Windsurf\n",
        "#\n",
        "# One-Person Company AI Operating System\n",
        f"# Generated by scripts/convert.py on {TODAY}\n",
        "#\n\n",
    ]
    count = 0
    for source in sources:
        parts.extend(
            [
                f"{'=' * 80}\n",
                f"## {source.name} [{source.kind}]\n",
                f"{source.description}\n",
                f"{'=' * 80}\n\n",
                adapt_body(source, "windsurf"),
                "\n",
            ]
        )
        count += 1

    write_file(out_dir / "windsurf" / ".windsurfrules", "".join(parts))
    write_runtime_metadata("windsurf", out_dir)
    return count


def convert_gemini_cli(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        write_file(runtime_output_path("gemini-cli", source, out_dir), render_gemini_skill(source))
        count += 1

    for asset in collect_skill_assets(SKILL_DIRS):
        parts = asset.relative_to(REPO_ROOT).parts
        if len(parts) >= 4:
            slug = parts[-2]
            target = out_dir / "gemini-cli" / "skills" / slug / parts[-1]
            write_file(target, asset.read_text(encoding="utf-8"))

    write_file(
        out_dir / "gemini-cli" / "gemini-extension.json",
        json.dumps({"name": "superopc", "version": PLUGIN_VERSION}, ensure_ascii=False, indent=2) + "\n",
    )
    write_runtime_metadata("gemini-cli", out_dir)
    return count


def convert_opencode(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        write_file(runtime_output_path("opencode", source, out_dir), render_agent_markdown(source, "opencode"))
        count += 1
    write_runtime_metadata("opencode", out_dir)
    return count


def convert_codex(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        write_file(runtime_output_path("codex", source, out_dir), render_agent_markdown(source, "codex"))
        count += 1
    write_runtime_metadata("codex", out_dir)
    return count


def convert_copilot(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        write_file(runtime_output_path("copilot", source, out_dir), render_copilot_instruction(source))
        count += 1
    write_runtime_metadata("copilot", out_dir)
    return count


def convert_rules_runtime(runtime: str, sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        write_file(runtime_output_path(runtime, source, out_dir), render_rule_markdown(source, runtime))
        count += 1
    write_runtime_metadata(runtime, out_dir)
    return count


def convert_openclaw(sources: list[SourceFile], out_dir: Path) -> int:
    count = 0
    for source in sources:
        agent_dir = runtime_output_path("openclaw", source, out_dir)
        body = adapt_body(source, "openclaw")
        soul, agents = split_openclaw_body(body, source.name, source.description)
        write_file(agent_dir / "SOUL.md", soul)
        write_file(agent_dir / "AGENTS.md", agents)
        write_file(agent_dir / "IDENTITY.md", f"# {source.name}\n\n{source.description}\n")
        count += 1
    write_runtime_metadata("openclaw", out_dir)
    return count


def convert_runtime(runtime: str, sources: list[SourceFile], out_dir: Path) -> int:
    if runtime == "claude-code":
        return convert_claude_code(sources, out_dir)
    if runtime == "cursor":
        return convert_cursor(sources, out_dir)
    if runtime == "windsurf":
        return convert_windsurf(sources, out_dir)
    if runtime == "copilot":
        return convert_copilot(sources, out_dir)
    if runtime == "gemini-cli":
        return convert_gemini_cli(sources, out_dir)
    if runtime == "opencode":
        return convert_opencode(sources, out_dir)
    if runtime == "codex":
        return convert_codex(sources, out_dir)
    if runtime in {"trae", "cline", "augment"}:
        return convert_rules_runtime(runtime, sources, out_dir)
    return convert_openclaw(sources, out_dir)


def detect_runtimes() -> list[str]:
    roots = [REPO_ROOT, Path.cwd(), Path.home()]
    found: list[str] = []
    for runtime in RUNTIME_ORDER:
        for root in roots:
            for marker in DETECTION_MARKERS.get(runtime, []):
                if (root / marker).exists():
                    found.append(runtime)
                    break
            if runtime in found:
                break
    return found


def print_detected_runtimes(detected: list[str]) -> None:
    if detected:
        print(f"  Detected runtimes: {', '.join(detected)}")
    else:
        print("  Detected runtimes: none")
