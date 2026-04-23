from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from opc_common import find_opc_dir, read_json, read_text, write_json
from quality_helpers import (
    PROJECT_SUPPORT_DIRS,
    PROJECT_TEMPLATE_FILES,
    TRACEABILITY_HEADINGS,
    ensure_project_handoff,
    extract_inline_value,
    gather_summary_files,
    gather_verification_files,
    heading_exists,
    load_template,
    make_check,
    merge_missing_keys,
    parse_frontmatter,
    scaffold_project_file,
    split_csv_like,
    summarize_checks,
    template_dir,
)


def parse_requirement_ids(requirements_text: str) -> list[str]:
    return re.findall(r"^- \[(?: |x)\]\s+\*\*([A-Z0-9_-]+)\*\*", requirements_text, re.MULTILINE | re.IGNORECASE)


def parse_roadmap_requirement_ids(roadmap_text: str) -> list[str]:
    collected: list[str] = []
    for match in re.finditer(r"\*\*需求\*\*[：:]\s*\[([^\]]*)\]", roadmap_text):
        collected.extend(split_csv_like(match.group(1)))
    if not collected:
        collected.extend(re.findall(r"(REQ-[A-Za-z0-9_-]+)", roadmap_text))
    deduped: list[str] = []
    seen: set[str] = set()
    for item in collected:
        normalized = item.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


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


def phase_artifact_key(file_path: Path, suffix: str) -> str:
    stem = file_path.stem
    normalized_suffix = f"-{suffix}"
    if stem == suffix:
        return file_path.parent.name
    if stem.endswith(normalized_suffix):
        return stem[: -len(normalized_suffix)]
    return stem


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
    verification_map = {phase_artifact_key(file, "VERIFICATION"): file for file in verification_files}
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
            summary_key = phase_artifact_key(summary_file, "SUMMARY")
            if summary_key not in verification_map:
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
