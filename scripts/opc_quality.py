#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

SOURCE_MARKDOWN_GLOBS = [
    "agents/*.md",
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
    "commands/opc/*.md",
    "references/*.md",
    "rules/**/*.md",
    "skills/**/SKILL.md",
    "templates/*.md",
]


def find_opc_dir(start_dir: Path) -> Path | None:
    current = start_dir.resolve()

    if current.name == ".opc" and current.exists():
        return current

    for candidate in (current, *current.parents):
        opc_dir = candidate / ".opc"
        if opc_dir.exists() and opc_dir.is_dir():
            return opc_dir

    return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("mode", nargs="?", choices=("health", "quality"))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--target", choices=("auto", "project", "repo", "all"), default="auto")
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(file_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_json(file_path: Path, payload: dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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


def template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates"


def load_template(template_name: str) -> str:
    return read_text(template_dir() / template_name)


def scaffold_project_file(file_path: Path, template_name: str) -> bool:
    content = load_template(template_name)
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
    for variant in variants:
        match = re.search(variant, markdown, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def parse_requirement_ids(requirements_text: str) -> list[str]:
    return re.findall(r"^- \[(?: |x)\]\s+\*\*([A-Z0-9_-]+)\*\*", requirements_text, re.MULTILINE | re.IGNORECASE)


def parse_roadmap_requirement_ids(roadmap_text: str) -> list[str]:
    collected: list[str] = []
    for match in re.finditer(r"\*\*需求\*\*[：:]\s*\[([^\]]*)\]", roadmap_text):
        collected.extend(split_csv_like(match.group(1)))
    deduped: list[str] = []
    seen: set[str] = set()
    for item in collected:
        normalized = item.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def gather_summary_files(opc_dir: Path) -> list[Path]:
    phases_dir = opc_dir / "phases"
    if not phases_dir.exists():
        return []
    return sorted(phases_dir.rglob("*SUMMARY.md"))


def gather_verification_files(opc_dir: Path) -> list[Path]:
    phases_dir = opc_dir / "phases"
    if not phases_dir.exists():
        return []
    return sorted(phases_dir.rglob("*VERIFICATION.md"))


def heading_exists(markdown: str, headings: tuple[str, ...]) -> bool:
    for heading in headings:
        if re.search(rf"^##\s+{re.escape(heading)}\s*$", markdown, re.MULTILINE):
            return True
    return False


def detect_schema_drift(project_root: Path) -> list[str]:
    findings: list[str] = []

    prisma_schema = project_root / "prisma" / "schema.prisma"
    if prisma_schema.exists() and not (project_root / "prisma" / "migrations").exists():
        findings.append("Prisma schema 存在但缺少 prisma/migrations。")

    alembic_ini = project_root / "alembic.ini"
    alembic_versions = project_root / "migrations" / "versions"
    if alembic_ini.exists() and not alembic_versions.exists():
        findings.append("Alembic 配置存在但缺少 migrations/versions。")

    supabase_dir = project_root / "supabase"
    if supabase_dir.exists() and not (supabase_dir / "migrations").exists():
        findings.append("Supabase 目录存在但缺少 supabase/migrations。")

    ef_migrations = list(project_root.rglob("Migrations"))
    db_contexts = list(project_root.rglob("*DbContext*.cs"))
    if db_contexts and not ef_migrations:
        findings.append("检测到 EF Core DbContext，但未找到 Migrations 目录。")

    return findings


def parse_summary_requirements(summary_file: Path) -> tuple[str, list[str]]:
    meta = parse_frontmatter(read_text(summary_file))
    value = meta.get("requirements-completed")
    if isinstance(value, list):
        return "ok", [str(item) for item in value]
    if value is None:
        return "missing", []
    if isinstance(value, str) and not value.strip():
        return "missing", []
    return "ok", [str(value)]


def parse_verification_requirements(verification_file: Path) -> list[str]:
    meta = parse_frontmatter(read_text(verification_file))
    value = meta.get("requirements-verified")
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def validate_project_checks(start_dir: Path, repair: bool) -> dict[str, Any]:
    original_opc_dir = find_opc_dir(start_dir)
    opc_dir = original_opc_dir if original_opc_dir is not None else start_dir.resolve() / ".opc"
    project_root = opc_dir.parent
    checks: list[dict[str, Any]] = []
    repairs: list[str] = []

    if original_opc_dir is None:
        if repair:
            opc_dir.mkdir(parents=True, exist_ok=True)
            repairs.append(f"created {opc_dir}")
            checks.append(make_check("project.opc-dir", "fixed", "已创建 .opc 目录。", files=[str(opc_dir)]))
        else:
            checks.append(
                make_check(
                    "project.opc-dir",
                    "fail",
                    "未找到 .opc 目录。",
                    severity="error",
                    repairable=True,
                    files=[str(opc_dir)],
                    details=["运行 /opc-start 初始化项目，或使用 /opc-health --repair 自动补齐基础结构。"],
                )
            )
            return {
                "target": "project",
                "root": str(project_root),
                "ok": False,
                "summary": summarize_checks(checks),
                "checks": checks,
                "repairs": repairs,
            }
    else:
        checks.append(make_check("project.opc-dir", "pass", "检测到 .opc 目录。", files=[str(opc_dir)]))

    missing_files = [name for name in PROJECT_TEMPLATE_FILES if not (opc_dir / name).exists()]
    if missing_files and repair:
        created: list[str] = []
        for name in missing_files:
            if scaffold_project_file(opc_dir / name, PROJECT_TEMPLATE_FILES[name]):
                created.append(str(opc_dir / name))
                repairs.append(f"scaffolded {opc_dir / name}")
        status = "fixed" if len(created) == len(missing_files) else "fail"
        checks.append(
            make_check(
                "project.core-files",
                status,
                "已补齐缺失的 .opc 核心文件。" if status == "fixed" else "部分核心文件模板缺失，无法完成补齐。",
                severity="error" if status == "fail" else "info",
                repairable=status != "fixed",
                files=created or [str(opc_dir / name) for name in missing_files],
                details=missing_files,
            )
        )
    elif missing_files:
        checks.append(
            make_check(
                "project.core-files",
                "fail",
                "缺少 .opc 核心文件。",
                severity="error",
                repairable=True,
                files=[str(opc_dir / name) for name in missing_files],
                details=missing_files,
            )
        )
    else:
        checks.append(make_check("project.core-files", "pass", "核心项目文件完整。"))

    missing_dirs = [name for name in PROJECT_SUPPORT_DIRS if not (opc_dir / name).exists()]
    if missing_dirs and repair:
        for name in missing_dirs:
            (opc_dir / name).mkdir(parents=True, exist_ok=True)
            repairs.append(f"created {opc_dir / name}")
        checks.append(
            make_check(
                "project.support-dirs",
                "fixed",
                "已补齐 .opc 支撑目录。",
                files=[str(opc_dir / name) for name in missing_dirs],
                details=missing_dirs,
            )
        )
    elif missing_dirs:
        checks.append(
            make_check(
                "project.support-dirs",
                "warn",
                "缺少部分 .opc 支撑目录。",
                severity="warning",
                repairable=True,
                files=[str(opc_dir / name) for name in missing_dirs],
                details=missing_dirs,
            )
        )
    else:
        checks.append(make_check("project.support-dirs", "pass", ".opc 支撑目录完整。"))

    config_file = opc_dir / "config.json"
    config_payload = read_json(config_file)
    if not config_file.exists() and repair:
        template_text = load_template("config.json")
        if template_text:
            config_file.write_text(template_text, encoding="utf-8")
            repairs.append(f"scaffolded {config_file}")
            checks.append(make_check("project.config", "fixed", "已创建 .opc/config.json。", files=[str(config_file)]))
            config_payload = read_json(config_file)
        else:
            checks.append(make_check("project.config", "fail", "缺少 config.json 模板，无法自动创建配置。", severity="error", repairable=True))
    elif not config_file.exists():
        checks.append(make_check("project.config", "warn", "缺少 .opc/config.json。", severity="warning", repairable=True, files=[str(config_file)]))
    elif not config_payload:
        checks.append(make_check("project.config", "fail", ".opc/config.json 不是有效 JSON。", severity="error", files=[str(config_file)]))
    else:
        workflow = config_payload.get("workflow")
        if not isinstance(workflow, dict):
            checks.append(make_check("project.config", "fail", ".opc/config.json 缺少 workflow 配置。", severity="error", files=[str(config_file)]))
        else:
            missing_workflow_keys = [key for key in ("nyquist", "node_repair") if key not in workflow]
            if missing_workflow_keys and repair:
                default_payload = read_json(template_dir() / "config.json")
                merged = merge_missing_keys(config_payload, default_payload)
                write_json(config_file, merged)
                repairs.append(f"updated {config_file}")
                checks.append(
                    make_check(
                        "project.config-quality-flags",
                        "fixed",
                        "已补齐质量工作流配置项。",
                        files=[str(config_file)],
                        details=missing_workflow_keys,
                    )
                )
            elif missing_workflow_keys:
                checks.append(
                    make_check(
                        "project.config-quality-flags",
                        "warn",
                        "workflow 配置缺少质量开关（nyquist/node_repair）。",
                        severity="warning",
                        repairable=True,
                        files=[str(config_file)],
                        details=missing_workflow_keys,
                    )
                )
            else:
                checks.append(make_check("project.config-quality-flags", "pass", "质量工作流配置完整。"))

    handoff_file = opc_dir / "HANDOFF.json"
    handoff_payload = read_json(handoff_file)
    if not handoff_file.exists() and repair:
        write_json(handoff_file, ensure_project_handoff(project_root))
        repairs.append(f"scaffolded {handoff_file}")
        handoff_payload = read_json(handoff_file)
        checks.append(make_check("project.handoff", "fixed", "已创建 HANDOFF.json。", files=[str(handoff_file)]))
    elif not handoff_file.exists():
        checks.append(make_check("project.handoff", "warn", "缺少 HANDOFF.json。", severity="warning", repairable=True, files=[str(handoff_file)]))
    elif not handoff_payload:
        checks.append(make_check("project.handoff", "fail", "HANDOFF.json 不是有效 JSON。", severity="error", files=[str(handoff_file)]))
    else:
        checks.append(make_check("project.handoff", "pass", "HANDOFF.json 可读取。", files=[str(handoff_file)]))

    requirements_text = read_text(opc_dir / "REQUIREMENTS.md")
    roadmap_text = read_text(opc_dir / "ROADMAP.md")
    requirement_ids = parse_requirement_ids(requirements_text)
    roadmap_ids = parse_roadmap_requirement_ids(roadmap_text)
    if requirement_ids:
        uncovered = [item for item in requirement_ids if item not in roadmap_ids]
        if uncovered:
            checks.append(
                make_check(
                    "project.requirements-coverage",
                    "fail",
                    "存在未映射到路线图的 v1 需求。",
                    severity="error",
                    files=[str(opc_dir / "REQUIREMENTS.md"), str(opc_dir / "ROADMAP.md")],
                    details=uncovered,
                )
            )
        else:
            checks.append(make_check("project.requirements-coverage", "pass", "v1 需求已映射到路线图。"))
    else:
        checks.append(
            make_check(
                "project.requirements-coverage",
                "warn",
                "未找到带 ID 的 v1 需求，无法执行覆盖率检查。",
                severity="warning",
                files=[str(opc_dir / "REQUIREMENTS.md")],
            )
        )

    summary_files = gather_summary_files(opc_dir)
    verification_files = gather_verification_files(opc_dir)
    verification_map = {file.stem.replace('-VERIFICATION', ''): file for file in verification_files}
    if not summary_files:
        checks.append(make_check("project.summary-traceability", "pass", "尚无阶段 SUMMARY 文件需要检查。"))
    else:
        missing_requirements: list[str] = []
        unknown_requirements: list[str] = []
        missing_traceability: list[str] = []
        missing_verifications: list[str] = []
        for summary_file in summary_files:
            summary_text = read_text(summary_file)
            state, completed = parse_summary_requirements(summary_file)
            if state != "ok" or not completed:
                missing_requirements.append(str(summary_file))
            else:
                unknown_requirements.extend(f"{summary_file}:{item}" for item in completed if item not in requirement_ids)
            if not heading_exists(summary_text, TRACEABILITY_HEADINGS):
                missing_traceability.append(str(summary_file))
            summary_prefix = summary_file.stem.replace('-SUMMARY', '')
            if summary_prefix not in verification_map:
                missing_verifications.append(str(summary_file))

        if missing_requirements:
            checks.append(
                make_check(
                    "project.summary-traceability",
                    "warn",
                    "部分 SUMMARY 文件缺少 requirements-completed。",
                    severity="warning",
                    files=missing_requirements,
                )
            )
        elif unknown_requirements:
            checks.append(
                make_check(
                    "project.summary-traceability",
                    "fail",
                    "部分 SUMMARY 文件引用了未知需求 ID。",
                    severity="error",
                    details=unknown_requirements,
                )
            )
        else:
            checks.append(make_check("project.summary-traceability", "pass", "SUMMARY 需求追踪字段有效。"))

        if missing_traceability:
            checks.append(
                make_check(
                    "project.claim-traceability",
                    "warn",
                    "部分 SUMMARY 文件缺少声明溯源区块。",
                    severity="warning",
                    files=missing_traceability,
                )
            )
        else:
            checks.append(make_check("project.claim-traceability", "pass", "SUMMARY 声明溯源区块完整。"))

        if missing_verifications:
            checks.append(
                make_check(
                    "project.verification-files",
                    "warn",
                    "部分 SUMMARY 尚未对应 VERIFICATION 文件。",
                    severity="warning",
                    files=missing_verifications,
                )
            )
        else:
            checks.append(make_check("project.verification-files", "pass", "SUMMARY 与 VERIFICATION 已配对。"))

    schema_findings = detect_schema_drift(project_root)
    if schema_findings:
        checks.append(
            make_check(
                "project.schema-drift",
                "warn",
                "检测到潜在 schema drift 风险。",
                severity="warning",
                details=schema_findings,
            )
        )
    else:
        checks.append(make_check("project.schema-drift", "pass", "未检测到明显 schema drift 风险。"))

    verification_missing_requirements: list[str] = []
    verification_unknown_requirements: list[str] = []
    verification_missing_traceability: list[str] = []
    for verification_file in verification_files:
        verification_text = read_text(verification_file)
        verified = parse_verification_requirements(verification_file)
        if not verified:
            verification_missing_requirements.append(str(verification_file))
        else:
            verification_unknown_requirements.extend(
                f"{verification_file}:{item}" for item in verified if item not in requirement_ids
            )
        if not heading_exists(verification_text, TRACEABILITY_HEADINGS):
            verification_missing_traceability.append(str(verification_file))

    if verification_missing_requirements:
        checks.append(
            make_check(
                "project.verification-requirements",
                "warn",
                "部分 VERIFICATION 文件缺少 requirements-verified。",
                severity="warning",
                files=verification_missing_requirements,
            )
        )
    elif verification_unknown_requirements:
        checks.append(
            make_check(
                "project.verification-requirements",
                "fail",
                "部分 VERIFICATION 文件引用了未知需求 ID。",
                severity="error",
                details=verification_unknown_requirements,
            )
        )
    elif verification_files:
        checks.append(make_check("project.verification-requirements", "pass", "VERIFICATION 需求字段有效。"))
    else:
        checks.append(make_check("project.verification-requirements", "pass", "尚无 VERIFICATION 文件需要检查。"))

    if verification_missing_traceability:
        checks.append(
            make_check(
                "project.verification-traceability",
                "warn",
                "部分 VERIFICATION 文件缺少声明溯源区块。",
                severity="warning",
                files=verification_missing_traceability,
            )
        )
    elif verification_files:
        checks.append(make_check("project.verification-traceability", "pass", "VERIFICATION 声明溯源区块完整。"))
    else:
        checks.append(make_check("project.verification-traceability", "pass", "尚无 VERIFICATION 文件需要检查。"))

    state_text = read_text(opc_dir / "STATE.md")
    state_resume = extract_inline_value(state_text, "恢复文件")
    missing_resume_files: list[str] = []
    if state_resume and state_resume not in {"无", "未记录"}:
        candidate = Path(state_resume)
        resolved = candidate if candidate.is_absolute() else project_root / candidate
        if not resolved.exists():
            missing_resume_files.append(state_resume)

    handoff_resume = handoff_payload.get("resumeFiles") if isinstance(handoff_payload.get("resumeFiles"), list) else []
    for item in handoff_resume:
        candidate = Path(str(item))
        resolved = candidate if candidate.is_absolute() else project_root / str(item)
        if str(item).strip() and not resolved.exists():
            missing_resume_files.append(str(item))

    if missing_resume_files:
        checks.append(
            make_check(
                "project.resume-files",
                "warn",
                "检测到不存在的恢复文件引用。",
                severity="warning",
                details=sorted(set(missing_resume_files)),
            )
        )
    else:
        checks.append(make_check("project.resume-files", "pass", "恢复文件引用有效。"))

    summary = summarize_checks(checks)
    return {
        "target": "project",
        "root": str(project_root),
        "ok": summary["fail"] == 0,
        "summary": summary,
        "checks": checks,
        "repairs": repairs,
    }


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

    for key in ("agents", "hooks"):
        value = payload.get(key)
        if not isinstance(value, list):
            errors.append(f"{plugin_file}: {key} must be a list")
            continue
        for entry in value:
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


def validate_repo_checks(start_dir: Path) -> dict[str, Any]:
    repo_root = find_repo_root(start_dir) or start_dir.resolve()
    checks: list[dict[str, Any]] = []

    missing_paths = [str(repo_root / path) for path in REPO_REQUIRED_PATHS if not (repo_root / path).exists()]
    if missing_paths:
        checks.append(
            make_check(
                "repo.required-paths",
                "fail",
                "仓库缺少关键目录或文件。",
                severity="error",
                files=missing_paths,
            )
        )
    else:
        checks.append(make_check("repo.required-paths", "pass", "仓库关键目录完整。"))

    frontmatter_errors = validate_frontmatter_files(repo_root)
    if frontmatter_errors:
        checks.append(
            make_check(
                "repo.frontmatter",
                "fail",
                "技能/代理/命令 frontmatter 校验失败。",
                severity="error",
                details=frontmatter_errors,
            )
        )
    else:
        checks.append(make_check("repo.frontmatter", "pass", "源 Markdown frontmatter 有效。"))

    plugin_errors = validate_plugin_manifest(repo_root)
    if plugin_errors:
        checks.append(
            make_check(
                "repo.plugin-manifest",
                "fail",
                "插件清单引用无效。",
                severity="error",
                details=plugin_errors,
                files=[str(repo_root / ".claude-plugin" / "plugin.json")],
            )
        )
    else:
        checks.append(make_check("repo.plugin-manifest", "pass", "插件清单引用完整。"))

    hook_errors = validate_hook_registry(repo_root)
    if hook_errors:
        checks.append(
            make_check(
                "repo.hook-registry",
                "fail",
                "Hook 注册表存在无效引用。",
                severity="error",
                details=hook_errors,
                files=[str(repo_root / "hooks" / "hooks.json")],
            )
        )
    else:
        checks.append(make_check("repo.hook-registry", "pass", "Hook 注册表与脚本一致。"))

    broken_links = validate_internal_links(repo_root)
    if broken_links:
        checks.append(
            make_check(
                "repo.internal-links",
                "fail",
                "检测到无效的内部 Markdown 链接。",
                severity="error",
                details=broken_links,
            )
        )
    else:
        checks.append(make_check("repo.internal-links", "pass", "内部 Markdown 链接有效。"))

    missing_workflows = [str(repo_root / path) for path in REQUIRED_WORKFLOWS if not (repo_root / path).exists()]
    if missing_workflows:
        checks.append(
            make_check(
                "repo.ci-workflows",
                "fail",
                "缺少所需的 GitHub Actions workflows。",
                severity="error",
                files=missing_workflows,
            )
        )
    else:
        checks.append(make_check("repo.ci-workflows", "pass", "GitHub Actions workflows 已就绪。"))

    plugin_payload = read_json(repo_root / ".claude-plugin" / "plugin.json")
    plugin_version = plugin_payload.get("version", "")
    if not plugin_version or not re.match(r"^\d+\.\d+\.\d+", plugin_version):
        checks.append(
            make_check(
                "repo.version",
                "fail",
                "插件版本缺失或格式无效。",
                severity="error",
                files=[str(repo_root / ".claude-plugin" / "plugin.json")],
                details=[f"当前值: {plugin_version or 'missing'}"],
            )
        )
    else:
        checks.append(make_check("repo.version", "pass", f"插件版本有效: {plugin_version}。"))

    summary = summarize_checks(checks)
    return {
        "target": "repo",
        "root": str(repo_root),
        "ok": summary["fail"] == 0,
        "summary": summary,
        "checks": checks,
        "repairs": [],
    }


def collect_project_quality_report(start_dir: Path, repair: bool = False) -> dict[str, Any]:
    result = validate_project_checks(start_dir, repair)
    findings = [check for check in result["checks"] if check["status"] in {"warn", "fail", "fixed"}]
    quality_signals = {
        "requirementsCoverageDebt": sum(1 for check in result["checks"] if check["id"] == "project.requirements-coverage" and check["status"] != "pass"),
        "regressionDebt": sum(1 for check in result["checks"] if check["id"] in {"project.verification-files", "project.verification-requirements"} and check["status"] != "pass"),
        "scopeDebt": sum(1 for check in result["checks"] if check["id"] == "project.summary-traceability" and check["status"] != "pass"),
        "traceabilityDebt": sum(1 for check in result["checks"] if check["id"] in {"project.summary-traceability", "project.claim-traceability", "project.verification-traceability", "project.resume-files"} and check["status"] != "pass"),
        "schemaDriftDebt": sum(1 for check in result["checks"] if check["id"] == "project.schema-drift" and check["status"] != "pass"),
        "integrityDebt": sum(1 for check in result["checks"] if check["id"] in {"project.opc-dir", "project.core-files", "project.support-dirs", "project.config", "project.handoff"} and check["status"] != "pass"),
        "skillContractDebt": 0,
    }
    validation_debt = [check["message"] for check in result["checks"] if check["status"] == "fail"]
    return {
        **result,
        "findings": findings,
        "qualitySignals": quality_signals,
        "validationDebt": validation_debt,
    }


def collect_repo_quality_report(start_dir: Path, repair: bool = False) -> dict[str, Any]:
    result = validate_repo_checks(start_dir)
    findings = [check for check in result["checks"] if check["status"] in {"warn", "fail", "fixed"}]
    quality_signals = {
        "requirementsCoverageDebt": 0,
        "regressionDebt": sum(1 for check in result["checks"] if check["id"] == "repo.ci-workflows" and check["status"] != "pass"),
        "scopeDebt": 0,
        "traceabilityDebt": 0,
        "schemaDriftDebt": 0,
        "integrityDebt": sum(1 for check in result["checks"] if check["status"] != "pass"),
        "skillContractDebt": sum(1 for check in result["checks"] if check["id"] == "repo.frontmatter" and check["status"] != "pass"),
    }
    validation_debt = [check["message"] for check in result["checks"] if check["status"] == "fail"]
    return {
        **result,
        "findings": findings,
        "qualitySignals": quality_signals,
        "validationDebt": validation_debt,
    }


def collect_quality_report(start_dir: Path, *, target: str = "auto", repair: bool = False) -> dict[str, Any]:
    resolved_targets = resolve_targets(start_dir, target)
    results: list[dict[str, Any]] = []
    for resolved_target in resolved_targets:
        if resolved_target == "project":
            results.append(validate_project_checks(start_dir, repair))
        elif resolved_target == "repo":
            results.append(validate_repo_checks(start_dir))

    summary = merge_summaries(results)
    return {
        "mode": "health",
        "generatedAt": now_iso(),
        "requestedTarget": target,
        "resolvedTargets": resolved_targets,
        "repairRequested": repair,
        "ok": all(result["ok"] for result in results),
        "summary": summary,
        "results": results,
    }


def format_quality_report(payload: dict[str, Any]) -> str:
    lines = [
        "SuperOPC Health",
        f"targets: {', '.join(payload['resolvedTargets'])}",
        f"summary: pass={payload['summary']['pass']} warn={payload['summary']['warn']} fail={payload['summary']['fail']} fixed={payload['summary']['fixed']}",
    ]

    for result in payload["results"]:
        lines.extend(
            [
                "",
                f"[{result['target']}] {result['root']}",
                f"status: {'PASS' if result['ok'] else 'FAIL'}",
                f"checks: pass={result['summary']['pass']} warn={result['summary']['warn']} fail={result['summary']['fail']} fixed={result['summary']['fixed']}",
            ]
        )
        if result["repairs"]:
            lines.append("repairs:")
            lines.extend(f"- {item}" for item in result["repairs"])
        for check in result["checks"]:
            lines.append(f"- [{check['status'].upper()}] {check['id']} — {check['message']}")
            for detail in check["details"]:
                lines.append(f"    • {detail}")
    return "\n".join(lines)


def run_cli(default_mode: str = "health") -> int:
    try:
        args = parse_args(sys.argv[1:])
        _mode = args.mode or default_mode
        payload = collect_quality_report(Path(args.cwd), target=args.target, repair=args.repair)
        if args.json:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            sys.stdout.write(f"{format_quality_report(payload)}\n")
        return 0 if payload["ok"] else 1
    except Exception as exc:
        sys.stderr.write(f"SuperOPC quality error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli("health"))
