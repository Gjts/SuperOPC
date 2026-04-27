from __future__ import annotations

from pathlib import Path

import run_pytest


def test_default_runtime_root_uses_system_temp_outside_repo_on_posix(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SUPEROPC_PYTEST_RUNTIME_ROOT", raising=False)
    monkeypatch.setattr(run_pytest.tempfile, "gettempdir", lambda: str(tmp_path))

    runtime_root = run_pytest._default_runtime_root("posix")

    assert runtime_root == tmp_path / "superopc-pytest-runtime"
    assert run_pytest.REPO_ROOT not in runtime_root.parents


def test_default_runtime_root_accepts_explicit_override(monkeypatch, tmp_path: Path) -> None:
    override = tmp_path / "custom-runtime"
    monkeypatch.setenv("SUPEROPC_PYTEST_RUNTIME_ROOT", str(override))

    assert run_pytest._default_runtime_root("posix") == override
