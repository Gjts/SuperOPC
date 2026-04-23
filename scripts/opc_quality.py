#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from opc_common import now_iso, read_json
from quality_helpers import (
    REPO_REQUIRED_PATHS,
    REQUIRED_WORKFLOWS,
    cleanup_transient_workspace_paths,
    find_transient_workspace_paths,
    find_repo_root,
    make_check,
    merge_summaries,
    resolve_targets,
    summarize_checks,
    validate_directory_map_coverage,
    validate_generated_artifact_policy,
    validate_frontmatter_files,
    validate_gitignore_workspace_policy,
    validate_hook_registry,
    validate_internal_links,
    validate_plugin_manifest,
)
from quality_project_checks import validate_project_checks

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("mode", nargs="?", choices=("health", "quality"))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--target", choices=("auto", "project", "repo", "all"), default="auto")
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def validate_repo_checks(start_dir: Path, repair: bool = False) -> dict[str, Any]:
    repo_root = find_repo_root(start_dir) or start_dir.resolve()
    checks: list[dict[str, Any]] = []
    repairs: list[str] = []

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

    transient_paths = find_transient_workspace_paths(repo_root)
    if transient_paths and repair:
        removed, cleanup_errors = cleanup_transient_workspace_paths(repo_root, transient_paths)
        if removed and not cleanup_errors:
            checks.append(
                make_check(
                    "repo.transient-dirs",
                    "fixed",
                    "Removed transient local workspace artifacts from the repo root.",
                    severity="warning",
                    files=[str(repo_root / name) for name in removed],
                    details=removed,
                )
            )
            repairs.extend(f"removed {name}" for name in removed)
        elif cleanup_errors:
            checks.append(
                make_check(
                    "repo.transient-dirs",
                    "warn",
                    "Some transient local workspace artifacts could not be removed automatically.",
                    severity="warning",
                    repairable=True,
                    files=[str(path) for path in transient_paths],
                    details=cleanup_errors,
                )
            )
        else:
            checks.append(
                make_check(
                    "repo.transient-dirs",
                    "pass",
                    "No transient local workspace artifacts detected at the repo root.",
                )
            )
    elif transient_paths:
        checks.append(
            make_check(
                "repo.transient-dirs",
                "warn",
                "Detected transient local workspace artifacts at the repo root; keep them ignored and clean them before review.",
                severity="warning",
                repairable=True,
                files=[str(path) for path in transient_paths],
                details=[path.name for path in transient_paths],
            )
        )
    else:
        checks.append(
            make_check(
                "repo.transient-dirs",
                "pass",
                "No transient local workspace artifacts detected at the repo root.",
            )
        )

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

    gitignore_policy_errors = validate_gitignore_workspace_policy(repo_root)
    if gitignore_policy_errors:
        checks.append(
            make_check(
                "repo.gitignore-policy",
                "fail",
                "Workspace ignore policy is missing required generated/temp directory rules.",
                severity="error",
                details=gitignore_policy_errors,
                files=[str(repo_root / ".gitignore")],
            )
        )
    else:
        checks.append(
            make_check(
                "repo.gitignore-policy",
                "pass",
                "Workspace ignore policy covers generated and transient directories.",
                files=[str(repo_root / ".gitignore")],
            )
        )

    directory_map_errors = validate_directory_map_coverage(repo_root)
    if directory_map_errors:
        checks.append(
            make_check(
                "repo.directory-map",
                "fail",
                "Directory map is missing required top-level directory coverage.",
                severity="error",
                details=directory_map_errors,
                files=[str(repo_root / "docs" / "DIRECTORY-MAP.md")],
            )
        )
    else:
        checks.append(
            make_check(
                "repo.directory-map",
                "pass",
                "Directory map documents the key source, generated, and local-runtime directories.",
                files=[str(repo_root / "docs" / "DIRECTORY-MAP.md")],
            )
        )

    generated_artifact_policy_errors = validate_generated_artifact_policy(repo_root)
    if generated_artifact_policy_errors:
        checks.append(
            make_check(
                "repo.generated-artifacts",
                "fail",
                "Generated artifact policy for integrations/ is missing or incomplete.",
                severity="error",
                details=generated_artifact_policy_errors,
                files=[str(repo_root / "integrations" / "README.md")],
            )
        )
    else:
        checks.append(
            make_check(
                "repo.generated-artifacts",
                "pass",
                "Generated artifact policy for integrations/ is documented and points to scripts/convert.py.",
                files=[str(repo_root / "integrations" / "README.md")],
            )
        )

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

    registry_check = validate_skill_registry_consistency(repo_root)
    if registry_check is not None:
        checks.append(registry_check)

    summary = summarize_checks(checks)
    return {
        "target": "repo",
        "root": str(repo_root),
        "ok": summary["fail"] == 0,
        "summary": summary,
        "checks": checks,
        "repairs": repairs,
    }


def validate_skill_registry_consistency(repo_root: Path) -> dict[str, Any] | None:
    """Run `scripts/build_skill_registry.py --check`; return a check dict or None."""
    import subprocess
    import sys as _sys

    script = repo_root / "scripts" / "build_skill_registry.py"
    registry_file = repo_root / "skills" / "registry.json"
    schema_file = repo_root / "skills" / "registry.schema.json"
    if not script.exists() or not schema_file.exists():
        return None  # registry feature not present in this checkout

    if not registry_file.exists():
        return make_check(
            "repo.skill-registry-consistency",
            "fail",
            "skills/registry.json 缺失，请运行 python scripts/build_skill_registry.py 生成。",
            severity="error",
            repairable=True,
            files=[str(registry_file)],
        )

    try:
        result = subprocess.run(
            [_sys.executable, str(script), "--check"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return make_check(
            "repo.skill-registry-consistency",
            "warn",
            f"无法运行 skill registry --check: {exc}",
            severity="warning",
            files=[str(script)],
        )

    if result.returncode == 0:
        return make_check(
            "repo.skill-registry-consistency",
            "pass",
            "skill registry 与 SKILL.md frontmatter 同步。",
            files=[str(registry_file)],
        )

    details = [line.strip() for line in (result.stderr or result.stdout).splitlines() if line.strip()]
    return make_check(
        "repo.skill-registry-consistency",
        "fail",
        "skill registry 与 SKILL.md frontmatter 漂移。运行 python scripts/build_skill_registry.py 重新生成。",
        severity="error",
        repairable=True,
        files=[str(registry_file)],
        details=details[:12],
    )


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
    result = validate_repo_checks(start_dir, repair)
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
            results.append(validate_repo_checks(start_dir, repair))

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
