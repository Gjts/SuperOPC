from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from opc_common import find_opc_dir, now_iso, read_json, read_text

PROJECT_TEMPLATE_FILES = {
    "PROJECT.md": "project.md",
    "REQUIREMENTS.md": "requirements.md",
    "ROADMAP.md": "roadmap.md",
    "STATE.md": "state.md",
}

PROJECT_SUPPORT_DIRS = [
    "phases",
    "research",
    "debug",
    "quick",
    "todos",
    "threads",
    "seeds",
    "sessions",
]

REQUIRED_WORKFLOWS = [
    ".github/workflows/quality.yml",
    ".github/workflows/release.yml",
]

TRACEABILITY_HEADINGS = ("声明溯源", "Claim Traceability", "Sources", "来源")

REPO_REQUIRED_PATHS = [
    ".claude-plugin/plugin.json",
    "agents",
    "commands/opc",
    "hooks/hooks.json",
    "references",
    "rules",
    "scripts",
    "skills",
    "templates",
    "tests",
]

TRANSIENT_WORKSPACE_PATHS = [
    ".manual_verify",
    ".pytest_tmp",
    ".test_tmp",
]

TRANSIENT_WORKSPACE_GLOBS = [
    "pytest-cache-files-*",
]

GENERATED_ARTIFACT_POLICY_FILE = Path("integrations/README.md")
DIRECTORY_MAP_FILE = Path("docs/DIRECTORY-MAP.md")
GITIGNORE_FILE = Path(".gitignore")

GENERATED_ARTIFACT_POLICY_MARKERS = [
    "generated-output",
    "scripts/convert.py",
    "Do not manually edit",
    "python scripts/convert.py --tool all",
]

DIRECTORY_MAP_REQUIRED_MARKERS = [
    "`marketing/`",
    "`website/`",
    "`integrations/`",
    "`.manual_verify/`",
    "`.pytest_tmp/`",
    "`.test_tmp/`",
    "`pytest-cache-files-*`",
]

GITIGNORE_REQUIRED_MARKERS = [
    "integrations/*",
    "!integrations/",
    "!integrations/README.md",
    ".manual_verify/",
    ".pytest_tmp/",
    ".test_tmp/",
    "pytest-cache-files-*/",
]

SOURCE_MARKDOWN_GLOBS = [
    "agents/*.md",
    "agents/domain/*.md",
    "commands/opc/*.md",
    "skills/**/SKILL.md",
]

LINK_CHECK_GLOBS = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "COMMIT_STYLE.md",
    "AGENTS.md",
    "CLAUDE.md",
    "agents/*.md",
    "agents/domain/*.md",
    "commands/opc/*.md",
    "references/*.md",
    "rules/**/*.md",
    "skills/**/SKILL.md",
    "templates/*.md",
]


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


def parse_frontmatter(content: str) -> dict[str, Any]:
    match = re.match(r"^---\n([\s\S]*?)\n---\n?([\s\S]*)$", content)
    if not match:
        return {}

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
    return meta


def make_check(
    check_id: str,
    status: str,
    message: str,
    *,
    severity: str = "info",
    repairable: bool = False,
    files: list[str] | None = None,
    details: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "severity": severity,
        "message": message,
        "repairable": repairable,
        "files": files or [],
        "details": details or [],
    }


def summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"pass": 0, "warn": 0, "fail": 0, "fixed": 0}
    for check in checks:
        status = check["status"]
        if status in summary:
            summary[status] += 1
    return summary


def merge_summaries(results: list[dict[str, Any]]) -> dict[str, int]:
    merged = {"pass": 0, "warn": 0, "fail": 0, "fixed": 0}
    for result in results:
        for key in merged:
            merged[key] += result["summary"][key]
    return merged


def split_csv_like(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,，]", value) if item.strip()]


def find_repo_root(start_dir: Path) -> Path | None:
    current = start_dir.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".claude-plugin" / "plugin.json").exists() and (candidate / "commands" / "opc").is_dir():
            return candidate
    return None


def resolve_targets(start_dir: Path, target: str) -> list[str]:
    if target == "project":
        return ["project"]
    if target == "repo":
        return ["repo"]
    if target == "all":
        results = ["project"]
        if find_repo_root(start_dir):
            results.append("repo")
        return results
    if find_opc_dir(start_dir):
        return ["project"]
    if find_repo_root(start_dir):
        return ["repo"]
    return ["project"]


def find_transient_workspace_paths(repo_root: Path) -> list[Path]:
    matches: dict[str, Path] = {}

    for relative in TRANSIENT_WORKSPACE_PATHS:
        candidate = repo_root / relative
        if candidate.exists():
            matches[str(candidate.resolve())] = candidate

    for pattern in TRANSIENT_WORKSPACE_GLOBS:
        for candidate in repo_root.glob(pattern):
            matches[str(candidate.resolve())] = candidate

    return sorted(matches.values(), key=lambda path: path.name.lower())


def cleanup_transient_workspace_paths(repo_root: Path, paths: list[Path]) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    errors: list[str] = []
    repo_root_resolved = repo_root.resolve()

    for candidate in paths:
        try:
            if candidate.parent.resolve() != repo_root_resolved:
                errors.append(f"refused to clean non-root transient path {candidate}")
                continue

            if not candidate.exists() and not candidate.is_symlink():
                continue

            if candidate.is_symlink() or candidate.is_file():
                candidate.unlink()
            elif candidate.is_dir():
                shutil.rmtree(candidate)
            else:
                errors.append(f"unsupported transient path type {candidate}")
                continue

            removed.append(candidate.name)
        except OSError as exc:
            errors.append(f"{candidate.name}: {exc}")

    return removed, errors


def validate_generated_artifact_policy(repo_root: Path) -> list[str]:
    return validate_required_markers(
        repo_root,
        GENERATED_ARTIFACT_POLICY_FILE,
        GENERATED_ARTIFACT_POLICY_MARKERS,
        label="generated artifact policy",
    )


def validate_directory_map_coverage(repo_root: Path) -> list[str]:
    return validate_required_markers(
        repo_root,
        DIRECTORY_MAP_FILE,
        DIRECTORY_MAP_REQUIRED_MARKERS,
        label="directory map",
    )


def validate_gitignore_workspace_policy(repo_root: Path) -> list[str]:
    return validate_required_markers(
        repo_root,
        GITIGNORE_FILE,
        GITIGNORE_REQUIRED_MARKERS,
        label="gitignore workspace policy",
    )


def validate_required_markers(
    repo_root: Path,
    relative_file: Path,
    required_markers: list[str],
    *,
    label: str,
) -> list[str]:
    target_file = repo_root / relative_file
    if not target_file.exists():
        return [f"missing {label} {relative_file.as_posix()}"]

    content = read_text(target_file)
    return [
        f"{relative_file.as_posix()}: missing marker {marker!r}"
        for marker in required_markers
        if marker not in content
    ]


def template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def load_template(template_name: str) -> str:
    return read_text(template_dir() / template_name)


def scaffold_project_markdown(file_path: Path) -> str | None:
    project_root = file_path.parent.parent
    project_name = project_root.name.replace("-", " ").replace("_", " ").strip().title() or "New Project"
    timestamp = now_iso()
    date_only = timestamp.split("T", 1)[0]

    if file_path.name == "PROJECT.md":
        return "\n".join(
            [
                f"# {project_name}",
                "",
                "## 项目参考",
                "**核心价值：** Restore project continuity with a healthy SuperOPC baseline.",
                "",
                "## 这是什么？",
                "A repaired SuperOPC starter scaffold. Replace this placeholder with the actual project description before planning.",
                "",
                "## 当前范围",
                "- [ ] Confirm the first user-facing outcome",
                "- [ ] Replace scaffold assumptions with real project context",
                "",
                "## 超范围",
                "- Large scope expansion before the first buildable slice is defined",
                "",
                "## 背景",
                f"- Scaffold generated by /opc-health --repair at {timestamp}",
                "- Use /opc-start or /opc-plan after filling the core docs",
                "",
                "## 关键决策",
                "| 决策 | 理由 | 结果 |",
                "|------|------|------|",
                "| Start from a repair scaffold | Restore operability quickly | 待定 |",
            ]
        )

    if file_path.name == "REQUIREMENTS.md":
        return "\n".join(
            [
                f"# Requirements: {project_name}",
                "",
                f"**定义日期：** {date_only}",
                "**核心价值：** Restore project continuity with a healthy SuperOPC baseline.",
                "",
                "## v1 需求",
                "",
                "- [ ] **REQ-01** Establish a valid SuperOPC project scaffold that can pass health checks.",
                "- [ ] **REQ-02** Capture the first project goal, scope, and next action before execution.",
                "",
                "## 说明",
                "",
                "- Generated by /opc-health --repair.",
                "- Replace these starter requirements before /opc-build.",
            ]
        )

    if file_path.name == "ROADMAP.md":
        return "\n".join(
            [
                f"# 路线图：{project_name}",
                "",
                "## 概览",
                "Start from a repaired baseline, define the first buildable slice, and then move into planning.",
                "",
                "## 进度",
                "",
                "| 阶段 | 已完成计划 | 状态 | 完成时间 |",
                "|------|-----------|------|---------|",
                "| 基础 | 0 / 1 | 未开始 | - |",
                "",
                "- [ ] Define the first buildable slice",
                "",
                "## 阶段 1：基础",
                "**目标：** Restore a healthy project baseline and prepare the first executable plan.",
                "**依赖：** 无",
                "**需求：** [REQ-01, REQ-02]",
                "**成功标准：**",
                "  1. Health checks pass on the repaired scaffold.",
                "  2. The team can continue with /opc-start or /opc-plan.",
                "**计划数：** 1 个计划",
                "",
                "计划：",
                "- [ ] 01-01：Define the first buildable slice",
            ]
        )

    if file_path.name == "STATE.md":
        return "\n".join(
            [
                "# 项目状态",
                "",
                "## 项目参考",
                "**核心价值：** Restore project continuity with a healthy SuperOPC baseline.",
                "**当前焦点：** Define project scope",
                "",
                "## 当前位置",
                "",
                "阶段：[0] / [1]（bootstrap）",
                "计划：[0] / [1]（bootstrap）",
                "状态：准备规划",
                f"最近活动：[{date_only}] - Scaffold repaired by /opc-health",
                "",
                "进度：[□□□□□□□□□□] 0%",
                "",
                "## 商业指标",
                "",
                "- MRR: CNY 0",
                "- Burn: CNY 0 / month",
                "- Runway: unknown",
                "- Active Customers: 0",
                "",
                "## 待办事项",
                "",
                "- Replace scaffold files with real project context",
                "",
                "## 阻塞/关注",
                "",
                "- Run /opc-start or /opc-plan after reviewing the scaffold",
                "",
                "## 验证欠债",
                "",
                "- Starter scaffold still needs project-specific review",
                "",
                "## 会话连续性",
                "",
                f"上次会话：{timestamp}",
                "停止于：Scaffold repaired by /opc-health",
                "恢复文件：.opc/STATE.md",
            ]
        )

    return None


def scaffold_project_file(file_path: Path, template_name: str) -> bool:
    content = scaffold_project_markdown(file_path) or load_template(template_name)
    if not content:
        return False
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return True


def ensure_project_handoff(project_root: Path) -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "updatedAt": now_iso(),
        "project": {
            "name": project_root.name,
            "root": str(project_root),
        },
        "session": {
            "id": "",
            "mode": "",
            "source": "opc-health --repair",
        },
        "location": {
            "phase": "",
            "plan": "",
            "status": "",
        },
        "summary": {
            "completed": "",
            "stopPoint": "通过 /opc-health 自动补齐 HANDOFF.json",
            "reasonForPause": "directory integrity repair",
        },
        "nextSteps": [],
        "blockers": [],
        "validationDebt": [],
        "resumeFiles": [".opc/STATE.md"],
        "notes": ["auto-generated by /opc-health --repair"],
    }


def merge_missing_keys(current: Any, default: Any) -> Any:
    if isinstance(current, dict) and isinstance(default, dict):
        merged = dict(current)
        for key, value in default.items():
            if key not in merged:
                merged[key] = value
            else:
                merged[key] = merge_missing_keys(merged[key], value)
        return merged
    return current


def extract_inline_value(markdown: str, label: str) -> str:
    variants = [
        rf"\*\*{re.escape(label)}：\*\*\s*(.+)$",
        rf"\*\*{re.escape(label)}:\*\*\s*(.+)$",
        rf"{re.escape(label)}：\s*(.+)$",
        rf"{re.escape(label)}:\s*(.+)$",
    ]
    for pattern in variants:
        match = re.search(pattern, markdown, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def parse_requirement_ids(requirements_text: str) -> list[str]:
    return re.findall(r"\*\*(REQ-[A-Za-z0-9_-]+)\*\*", requirements_text)


def parse_roadmap_requirement_ids(roadmap_text: str) -> list[str]:
    return re.findall(r"(REQ-[A-Za-z0-9_-]+)", roadmap_text)


def gather_summary_files(opc_dir: Path) -> list[Path]:
    seen: set[Path] = set()
    matches: list[Path] = []
    for pattern in ("phases/*/SUMMARY.md", "phases/*/*-SUMMARY.md", "**/SUMMARY.md", "**/*-SUMMARY.md"):
        for file_path in sorted(opc_dir.glob(pattern)):
            if file_path.is_file() and file_path not in seen:
                seen.add(file_path)
                matches.append(file_path)
    return matches


def gather_verification_files(opc_dir: Path) -> list[Path]:
    seen: set[Path] = set()
    matches: list[Path] = []
    for pattern in ("phases/*/VERIFICATION.md", "phases/*/*-VERIFICATION.md", "**/VERIFICATION.md", "**/*-VERIFICATION.md"):
        for file_path in sorted(opc_dir.glob(pattern)):
            if file_path.is_file() and file_path not in seen:
                seen.add(file_path)
                matches.append(file_path)
    return matches


def heading_exists(markdown: str, headings: tuple[str, ...]) -> bool:
    for heading in headings:
        if re.search(rf"^\s*#+\s*{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE):
            return True
    return False


def collect_relative_markdown_links(markdown: str) -> list[str]:
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", markdown)
    results: list[str] = []
    for link in links:
        normalized = link.strip().strip("<>")
        if not normalized or normalized.startswith("#"):
            continue
        if re.match(r"^[a-z]+://", normalized, re.IGNORECASE) or normalized.startswith("mailto:"):
            continue
        results.append(normalized)
    return results


def validate_frontmatter_files(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for pattern in SOURCE_MARKDOWN_GLOBS:
        for file_path in sorted(repo_root.glob(pattern)):
            content = read_text(file_path)
            meta = parse_frontmatter(content)
            if not meta:
                errors.append(f"{file_path}: missing frontmatter")
                continue
            for field in ("name", "description"):
                value = meta.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{file_path}: missing {field}")
    return errors


def validate_plugin_manifest(repo_root: Path) -> list[str]:
    plugin_file = repo_root / ".claude-plugin" / "plugin.json"
    payload = read_json(plugin_file)
    errors: list[str] = []
    if not payload:
        return [f"{plugin_file}: invalid JSON"]

    agents = payload.get("agents")
    if not isinstance(agents, list):
        errors.append(f"{plugin_file}: agents must be a list")
    else:
        for entry in agents:
            target = repo_root / str(entry).lstrip("./")
            if not target.exists():
                errors.append(f"{plugin_file}: missing referenced path {entry}")

    hooks = payload.get("hooks")
    if hooks is not None:
        if not isinstance(hooks, list):
            errors.append(f"{plugin_file}: hooks must be a list")
        else:
            for entry in hooks:
                target = repo_root / str(entry).lstrip("./")
                if not target.exists():
                    errors.append(f"{plugin_file}: missing referenced path {entry}")
    return errors


def validate_hook_registry(repo_root: Path) -> list[str]:
    hooks_file = repo_root / "hooks" / "hooks.json"
    payload = read_json(hooks_file)
    errors: list[str] = []
    if not payload:
        return [f"{hooks_file}: invalid JSON"]

    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        return [f"{hooks_file}: missing hooks object"]

    for stage, items in hooks.items():
        if not isinstance(items, list):
            errors.append(f"{hooks_file}: {stage} must be a list")
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            nested = item.get("hooks")
            if not isinstance(nested, list):
                continue
            for hook in nested:
                if not isinstance(hook, dict):
                    continue
                command = str(hook.get("command", "")).strip()
                if not command:
                    errors.append(f"{hooks_file}: empty command in {stage}")
                    continue
                match = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"]+\.py)", command)
                if not match:
                    continue
                target = repo_root / match.group(1)
                if not target.exists():
                    errors.append(f"{hooks_file}: missing hook script {match.group(1)}")
    return errors


def validate_internal_links(repo_root: Path) -> list[str]:
    broken: list[str] = []
    seen_files: set[Path] = set()
    for pattern in LINK_CHECK_GLOBS:
        for file_path in sorted(repo_root.glob(pattern)):
            if file_path in seen_files or not file_path.is_file():
                continue
            seen_files.add(file_path)
            for raw_link in collect_relative_markdown_links(read_text(file_path)):
                path_part = raw_link.split("#", 1)[0].strip()
                if not path_part:
                    continue
                candidate = (repo_root / path_part.lstrip("/")) if raw_link.startswith("/") else (file_path.parent / path_part)
                if not candidate.exists():
                    broken.append(f"{file_path}: {raw_link}")
    return broken
