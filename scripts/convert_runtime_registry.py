from __future__ import annotations

import json
from datetime import date
from pathlib import Path
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
