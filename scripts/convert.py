#!/usr/bin/env python3
"""
convert.py — Convert SuperOPC skills/agents/commands into runtime-specific formats.

Reads all markdown source files from skills/, agents/, commands/ and outputs
converted files to integrations/<runtime>/.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
import re
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "integrations"
TODAY = date.today().isoformat()
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
PLUGIN_VERSION = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8")).get("version", "0.1.0")

SKILL_DIRS = [
    "skills/product",
    "skills/engineering",
    "skills/business",
    "skills/learning",
    "skills/using-superopc",
]
# NOTE (v1.4.0): skills/intelligence/ 已在 v1.4 精简中全部下沉到 references/
# （market-research / follow-builders → references/intelligence/；
#  autonomous-ops → skills/using-superopc/autonomous-ops/）。
AGENT_DIR = "agents"
COMMAND_DIR = "commands/opc"

RUNTIME_ORDER = (
    "claude-code",
    "cursor",
    "windsurf",
    "copilot",
    "gemini-cli",
    "opencode",
    "codex",
    "trae",
    "cline",
    "augment",
    "openclaw",
)
VALID_TOOLS = (*RUNTIME_ORDER, "all", "auto")


IDENTITY_TOOL_MAPPING = {
    "Read": "Read",
    "Write": "Write",
    "Edit": "Edit",
    "MultiEdit": "MultiEdit",
    "Bash": "Bash",
    "Grep": "Grep",
    "Glob": "Glob",
    "WebSearch": "WebSearch",
    "WebFetch": "WebFetch",
    "AskUserQuestion": "AskUserQuestion",
    "TodoRead": "TodoRead",
    "TodoWrite": "TodoWrite",
    "Task": "Task",
    "Skill": "Skill",
}

SEMANTIC_EDITOR_MAPPING = {
    "Read": "read-file",
    "Write": "edit-file",
    "Edit": "edit-file",
    "MultiEdit": "edit-file",
    "Bash": "terminal",
    "Grep": "workspace-search",
    "Glob": "workspace-search",
    "WebSearch": "web-search",
    "WebFetch": "web-fetch",
    "AskUserQuestion": "ask-user",
    "TodoRead": "task-list",
    "TodoWrite": "task-list",
    "Task": "subagent",
    "Skill": "rule-loader",
}

COPILOT_TOOL_MAPPING = {
    "Read": "read",
    "Write": "edit",
    "Edit": "edit",
    "MultiEdit": "edit",
    "Bash": "execute",
    "Grep": "search",
    "Glob": "search",
    "WebSearch": "web",
    "WebFetch": "web",
    "AskUserQuestion": "ask_user",
    "TodoRead": "todo",
    "TodoWrite": "todo",
    "Task": "agent",
    "Skill": "skill",
}

GEMINI_TOOL_MAPPING = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "write_file",
    "MultiEdit": "write_file",
    "Bash": "run_shell_command",
    "Grep": "search_file_content",
    "Glob": "glob",
    "WebSearch": "web_search",
    "WebFetch": "web_fetch",
    "AskUserQuestion": "ask_user",
    "TodoRead": "todo",
    "TodoWrite": "todo",
    "Task": "agent",
    "Skill": "load_skill",
}

CODEX_TOOL_MAPPING = {
    "Read": "read",
    "Write": "edit",
    "Edit": "edit",
    "MultiEdit": "edit",
    "Bash": "shell",
    "Grep": "search",
    "Glob": "search",
    "WebSearch": "web",
    "WebFetch": "web",
    "AskUserQuestion": "ask-user",
    "TodoRead": "todo",
    "TodoWrite": "todo",
    "Task": "agent",
    "Skill": "prompt",
}

HOOK_MAPPING_NATIVE = {
    "PreToolUse": {
        "mappedTo": "PreToolUse",
        "status": "native",
        "notes": "Claude Code is the canonical hook runtime for SuperOPC.",
    },
    "PostToolUse": {
        "mappedTo": "PostToolUse",
        "status": "native",
        "notes": "Native Claude Code hook event.",
    },
    "Notification": {
        "mappedTo": "Notification",
        "status": "native",
        "notes": "Native Claude Code notification hook.",
    },
    "Stop": {
        "mappedTo": "Stop",
        "status": "native",
        "notes": "Native Claude Code stop hook.",
    },
}

HOOK_MAPPING_MANUAL = {
    "PreToolUse": {
        "mappedTo": None,
        "status": "manual",
        "notes": "No guaranteed native equivalent. Keep these checks as instructions, review gates, or wrapper scripts.",
    },
    "PostToolUse": {
        "mappedTo": None,
        "status": "manual",
        "notes": "No guaranteed native equivalent. Apply via manual audit or external automation.",
    },
    "Notification": {
        "mappedTo": None,
        "status": "manual",
        "notes": "Statusline and notifications degrade to conversational status updates.",
    },
    "Stop": {
        "mappedTo": None,
        "status": "manual",
        "notes": "Session-summary behavior should be handled by end-of-session prompts or wrapper tooling.",
    },
}

RUNTIME_CONFIGS: dict[str, dict[str, Any]] = {
    "claude-code": {
        "display_name": "Claude Code",
        "config_dir": ".claude",
        "instruction_file": "CLAUDE.md",
        "skills_dir": ".claude/skills",
        "agents_dir": ".claude/agents",
        "commands_dir": ".claude/commands",
        "layout": "mirror",
        "tool_mapping": IDENTITY_TOOL_MAPPING,
        "hook_mapping": HOOK_MAPPING_NATIVE,
    },
    "cursor": {
        "display_name": "Cursor",
        "config_dir": ".cursor",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".cursor/rules",
        "agents_dir": ".cursor/rules",
        "commands_dir": ".cursor/rules",
        "layout": "cursor",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "windsurf": {
        "display_name": "Windsurf",
        "config_dir": ".windsurf",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".windsurf",
        "agents_dir": ".windsurf",
        "commands_dir": ".windsurf",
        "layout": "windsurf",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "copilot": {
        "display_name": "GitHub Copilot",
        "config_dir": ".github",
        "instruction_file": "copilot-instructions.md",
        "skills_dir": ".github/instructions",
        "agents_dir": ".github/instructions",
        "commands_dir": ".github/instructions",
        "layout": "copilot",
        "tool_mapping": COPILOT_TOOL_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "gemini-cli": {
        "display_name": "Gemini CLI",
        "config_dir": ".gemini",
        "instruction_file": "GEMINI.md",
        "skills_dir": ".gemini/skills",
        "agents_dir": ".gemini/agents",
        "commands_dir": ".gemini/commands",
        "layout": "gemini",
        "tool_mapping": GEMINI_TOOL_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "opencode": {
        "display_name": "OpenCode",
        "config_dir": ".opencode",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".opencode/skills",
        "agents_dir": ".opencode/agents",
        "commands_dir": ".opencode/commands",
        "layout": "agent-markdown",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "codex": {
        "display_name": "Codex",
        "config_dir": ".codex",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".codex/skills",
        "agents_dir": ".codex/agents",
        "commands_dir": ".codex/commands",
        "layout": "agent-markdown",
        "tool_mapping": CODEX_TOOL_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "trae": {
        "display_name": "Trae",
        "config_dir": ".trae",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".trae/rules",
        "agents_dir": ".trae/rules",
        "commands_dir": ".trae/rules",
        "layout": "rules",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "cline": {
        "display_name": "Cline",
        "config_dir": ".cline",
        "instruction_file": ".clinerules",
        "skills_dir": ".clinerules",
        "agents_dir": ".clinerules",
        "commands_dir": ".clinerules",
        "layout": "rules",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "augment": {
        "display_name": "Augment Code",
        "config_dir": ".augment",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".augment/rules",
        "agents_dir": ".augment/rules",
        "commands_dir": ".augment/rules",
        "layout": "rules",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
    "openclaw": {
        "display_name": "OpenClaw",
        "config_dir": ".openclaw",
        "instruction_file": "AGENTS.md",
        "skills_dir": ".openclaw/skills",
        "agents_dir": ".openclaw/agents",
        "commands_dir": ".openclaw/commands",
        "layout": "openclaw",
        "tool_mapping": SEMANTIC_EDITOR_MAPPING,
        "hook_mapping": HOOK_MAPPING_MANUAL,
    },
}

DETECTION_MARKERS = {
    "claude-code": ["CLAUDE.md", ".claude", ".claude-plugin/plugin.json"],
    "cursor": [".cursor", ".cursor/rules"],
    "windsurf": [".windsurf", ".windsurfrules"],
    "copilot": [".github/copilot-instructions.md", ".github/instructions"],
    "gemini-cli": [".gemini", "gemini-extension.json"],
    "opencode": [".opencode"],
    "codex": [".codex"],
    "trae": [".trae"],
    "cline": [".cline", ".clinerules"],
    "augment": [".augment"],
    "openclaw": [".openclaw"],
}

STATIC_CLAUDE_EXPORTS = (
    "CLAUDE.md",
    "AGENTS.md",
    "hooks/hooks.json",
    ".claude-plugin/plugin.json",
    ".mcp.json",
    "mcp-configs/mcp-servers.json",
)


@dataclass
class ParsedMarkdown:
    meta: dict[str, Any]
    body: str


@dataclass
class SourceFile:
    kind: str
    path: Path
    relative_path: Path
    parsed: ParsedMarkdown

    @property
    def name(self) -> str:
        raw = self.parsed.meta.get("name")
        return str(raw) if raw else self.path.stem

    @property
    def description(self) -> str:
        raw = self.parsed.meta.get("description")
        return str(raw) if raw else ""


def slugify(name: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", name.lower()))


def parse_inline_list(value: str) -> list[str]:
    inner = value[1:-1].strip()
    if not inner:
        return []
    items = [item.strip() for item in inner.split(",") if item.strip()]
    return [item.strip('"').strip("'") for item in items]


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return parse_inline_list(value)
    if value == "true":
        return True
    if value == "false":
        return False
    return value.strip('"').strip("'")


def parse_frontmatter(content: str) -> ParsedMarkdown:
    match = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", content)
    if not match:
        return ParsedMarkdown(meta={}, body=content)

    meta: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in match.group(1).splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key and isinstance(meta.get(current_key), list):
            meta[current_key].append(parse_scalar(stripped[2:]))
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            meta[key] = []
            current_key = key
            continue
        meta[key] = parse_scalar(value)
        current_key = None

    return ParsedMarkdown(meta=meta, body=match.group(2))


def collect_files(directories: list[str], suffix: str = ".md") -> list[Path]:
    results: list[Path] = []
    for directory in directories:
        abs_dir = REPO_ROOT / directory
        if abs_dir.exists():
            results.extend(sorted(path for path in abs_dir.rglob(f"*{suffix}") if path.is_file()))
    return sorted(results)


def collect_skill_files(directories: list[str]) -> list[Path]:
    """Only match `SKILL.md` under each skill directory.

    v1.4.2 fix: previously used `rglob('*.md')` which incorrectly swept in
    supporting prompt templates like `implementer-prompt.md` under
    `skills/engineering/agent-dispatch/`. Those are NOT skills — they are
    prompts that the agent-dispatch skill references. Treating them as
    skills caused convert.py to export 20 'skills' per runtime (17 real +
    3 prompt templates) which in turn littered 33 bogus skill files across
    11 runtime targets per conversion.

    Canonical rule: one skill == one directory containing exactly one
    `SKILL.md`. Any additional `.md` files in the directory are
    skill-internal assets — collected separately by `collect_skill_assets()`.
    """
    results: list[Path] = []
    for directory in directories:
        abs_dir = REPO_ROOT / directory
        if abs_dir.exists():
            results.extend(sorted(path for path in abs_dir.rglob("SKILL.md") if path.is_file()))
    return sorted(results)


def collect_skill_assets(directories: list[str]) -> list[Path]:
    """Collect non-SKILL.md files inside skill directories.

    These are supporting assets (prompt templates, reference diagrams, etc.)
    that a skill references via relative paths (e.g. `./implementer-prompt.md`
    inside `agent-dispatch/SKILL.md`). They must be copied alongside the
    skill for the skill to function end-to-end — but they are NOT standalone
    skills and must never be counted or discovered as skills.

    Only runtimes that preserve the skill directory structure
    (claude-code, gemini-cli, openclaw) should copy these verbatim. Flat
    runtimes (cursor, copilot) lose them by design — users of those
    runtimes must reference the canonical SuperOPC repo for full skill
    assets.
    """
    results: list[Path] = []
    for directory in directories:
        abs_dir = REPO_ROOT / directory
        if not abs_dir.exists():
            continue
        for md_path in abs_dir.rglob("*.md"):
            if md_path.name != "SKILL.md" and md_path.is_file():
                results.append(md_path)
    return sorted(results)


def collect_sources() -> list[SourceFile]:
    sources: list[SourceFile] = []
    for path in collect_skill_files(SKILL_DIRS):
        sources.append(SourceFile("skill", path, path.relative_to(REPO_ROOT), parse_frontmatter(path.read_text(encoding="utf-8"))))
    for path in collect_files([AGENT_DIR]):
        sources.append(SourceFile("agent", path, path.relative_to(REPO_ROOT), parse_frontmatter(path.read_text(encoding="utf-8"))))
    for path in collect_files([COMMAND_DIR]):
        sources.append(SourceFile("command", path, path.relative_to(REPO_ROOT), parse_frontmatter(path.read_text(encoding="utf-8"))))
    return sources


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


def extract_tools(source: SourceFile) -> list[str]:
    raw = source.parsed.meta.get("tools")
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str) and raw:
        if raw.startswith("[") and raw.endswith("]"):
            return parse_inline_list(raw)
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def map_tools(tools: list[str], mapping: dict[str, str]) -> list[str]:
    mapped: list[str] = []
    for tool in tools:
        mapped_name = mapping.get(tool, tool)
        if mapped_name not in mapped:
            mapped.append(mapped_name)
    return mapped


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

    # Copy skill assets (non-SKILL.md files inside skill dirs) verbatim.
    # Required for skills like agent-dispatch that reference relative prompt
    # templates (./implementer-prompt.md etc.).
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

    # Gemini CLI preserves skill directory structure (skills/<slug>/SKILL.md),
    # so copy skill assets alongside each SKILL.md (slug-based relative path).
    for asset in collect_skill_assets(SKILL_DIRS):
        parts = asset.relative_to(REPO_ROOT).parts  # ("skills", "<category>", "<slug>", "<asset>.md")
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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert SuperOPC formats for Claude Code and other runtimes.")
    parser.add_argument("--tool", choices=VALID_TOOLS, default="all", help="Runtime to generate, all runtimes, or auto-detect")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory for generated integrations")
    parser.add_argument("--detect", action="store_true", help="Print detected runtimes before conversion")
    return parser.parse_args(argv)


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


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out).resolve()
    detected = detect_runtimes()

    print("\nSuperOPC Format Converter")
    print(f"  Repo:   {REPO_ROOT}")
    print(f"  Output: {out_dir}")
    print(f"  Tool:   {args.tool}")
    print(f"  Date:   {TODAY}")
    if args.detect or args.tool == "auto":
        print_detected_runtimes(detected)
    print()

    sources = collect_sources()
    skill_count = sum(1 for source in sources if source.kind == "skill")
    agent_count = sum(1 for source in sources if source.kind == "agent")
    command_count = sum(1 for source in sources if source.kind == "command")
    print(f"  Found: {skill_count} skills, {agent_count} agents, {command_count} commands\n")

    if args.tool == "all":
        runtimes = list(RUNTIME_ORDER)
    elif args.tool == "auto":
        runtimes = detected or ["claude-code"]
    else:
        runtimes = [args.tool]

    total = 0
    for runtime in runtimes:
        count = convert_runtime(runtime, sources, out_dir)
        print(f"  [OK] {runtime}: {count} items converted")
        total += count

    print(f"\n  Done. Total: {total} conversions across {len(runtimes)} runtime(s).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
