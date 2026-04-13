"""
security.py — Security utilities for opc-tools.

Provides: path traversal validation, prompt injection scanning,
field name validation, safe JSON parsing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cli.core import error, output


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def dispatch_security(args: list[str], cwd: Path, raw: bool) -> None:
    """Route security subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "validate-path":
        if not rest:
            error("path required for validate-path")
        cmd_validate_path(cwd, rest[0], raw)
    elif sub == "scan-injection":
        if not rest:
            error("text required for scan-injection")
        text = " ".join(rest)
        cmd_scan_injection(text, raw)
    elif sub == "validate-field":
        if not rest:
            error("field name required")
        cmd_validate_field(rest[0], raw)
    elif sub == "safe-json-parse":
        if not rest:
            error("JSON string required")
        cmd_safe_json_parse(" ".join(rest), raw)
    else:
        error(f"Unknown security subcommand: {sub}\nAvailable: validate-path, scan-injection, validate-field, safe-json-parse")


# ---------------------------------------------------------------------------
# Path validation
# ---------------------------------------------------------------------------

def validate_path(file_path: str, base_dir: Path, allow_absolute: bool = False) -> dict[str, Any]:
    """Check a path for directory traversal attacks."""
    p = Path(file_path)

    # Block obvious traversal
    if ".." in p.parts:
        return {"safe": False, "error": "Path contains '..' traversal", "resolved": None}

    # Resolve to absolute
    if p.is_absolute():
        if not allow_absolute:
            return {"safe": False, "error": "Absolute paths not allowed", "resolved": None}
        resolved = p.resolve()
    else:
        resolved = (base_dir / p).resolve()

    # Ensure resolved path is within base_dir
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        return {"safe": False, "error": f"Path escapes project directory: {resolved}", "resolved": None}

    return {"safe": True, "error": None, "resolved": str(resolved)}


def cmd_validate_path(cwd: Path, file_path: str, raw: bool) -> None:
    """Check a path for traversal attacks."""
    result = validate_path(file_path, cwd, allow_absolute=True)
    output(result, raw, "safe" if result["safe"] else f"unsafe: {result['error']}")


# ---------------------------------------------------------------------------
# Injection scanning
# ---------------------------------------------------------------------------

INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions?", "ignore-previous-instructions"),
    (r"you\s+are\s+now\s+(?:a|an|the)", "role-reassignment"),
    (r"system\s*(?:prompt|message)\s*:", "system-prompt-injection"),
    (r"<\s*(?:system|admin|root)\s*>", "xml-tag-injection"),
    (r"(?:IMPORTANT|CRITICAL|OVERRIDE)\s*:", "priority-escalation"),
    (r"(?:act|behave|pretend)\s+as\s+(?:if|though)", "persona-manipulation"),
    (r"forget\s+(?:everything|all|your)", "memory-wipe-attempt"),
    (r"do\s+not\s+follow\s+(?:the|your)\s+(?:rules|instructions)", "rule-override"),
]

# Unicode invisible characters
INVISIBLE_CHARS = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff\u00ad]")


def scan_injection(text: str) -> list[dict[str, str]]:
    """Scan text for prompt injection patterns. Returns list of findings."""
    findings: list[dict[str, str]] = []

    # Check for invisible Unicode characters
    if INVISIBLE_CHARS.search(text):
        findings.append({
            "type": "unicode-invisible",
            "detail": "Text contains invisible Unicode characters",
            "severity": "high",
        })

    # Check patterns
    for pattern, name in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append({
                "type": name,
                "detail": f"Matched pattern: {pattern}",
                "severity": "medium",
            })

    # Check for base64-encoded suspicious content
    import base64
    b64_pattern = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
    for match in b64_pattern.finditer(text):
        try:
            decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
            if any(kw in decoded.lower() for kw in ["ignore", "system", "override", "admin"]):
                findings.append({
                    "type": "encoded-injection",
                    "detail": "Base64-encoded suspicious content found",
                    "severity": "high",
                })
        except Exception:
            pass

    return findings


def cmd_scan_injection(text: str, raw: bool) -> None:
    """Scan text for prompt injection patterns."""
    findings = scan_injection(text)
    clean = not findings
    output({"clean": clean, "findings": findings}, raw, "clean" if clean else f"suspicious ({len(findings)} findings)")


# ---------------------------------------------------------------------------
# Field validation
# ---------------------------------------------------------------------------

ALLOWED_FIELD_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9 _-]{0,99}$")


def validate_field_name(field: str) -> dict[str, bool | str | None]:
    """Validate a STATE.md field name."""
    if not field:
        return {"valid": False, "error": "Field name is empty"}
    if not ALLOWED_FIELD_PATTERN.match(field):
        return {"valid": False, "error": f"Invalid field name: {field}. Must match [a-zA-Z][a-zA-Z0-9 _-]{{0,99}}"}
    return {"valid": True, "error": None}


def cmd_validate_field(field: str, raw: bool) -> None:
    """Validate a STATE.md field name."""
    result = validate_field_name(field)
    output(result, raw, "valid" if result["valid"] else f"invalid: {result['error']}")


# ---------------------------------------------------------------------------
# Safe JSON parsing
# ---------------------------------------------------------------------------

def safe_json_parse(text: str, label: str = "input") -> dict[str, Any]:
    """Parse JSON with error handling."""
    try:
        value = json.loads(text)
        return {"ok": True, "value": value, "error": None}
    except json.JSONDecodeError as e:
        return {"ok": False, "value": None, "error": f"Invalid JSON in {label}: {e}"}


def cmd_safe_json_parse(text: str, raw: bool) -> None:
    """Parse and validate JSON string."""
    result = safe_json_parse(text)
    output(result, raw, "ok" if result["ok"] else f"error: {result['error']}")
