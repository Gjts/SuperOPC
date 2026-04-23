from __future__ import annotations

import ctypes
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if os.name == "nt":
    RUNTIME_ROOT = Path.home() / ".codex" / "memories" / "superopc-pytest-runtime"
else:
    RUNTIME_ROOT = REPO_ROOT / ".test_tmp" / "pytest-runtime"


def _short_path(path: Path) -> str:
    resolved = str(path.resolve())
    if os.name != "nt":
        return resolved
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetShortPathNameW(resolved, buffer, len(buffer))
        if length > 0:
            return buffer.value
    except Exception:
        pass
    return resolved


def _patch_pytest_for_windows() -> None:
    if os.name != "nt":
        return

    from _pytest import tmpdir as pytest_tmpdir
    from _pytest.pathlib import LOCK_TIMEOUT, make_numbered_dir, make_numbered_dir_with_cleanup, rm_rf

    def getbasetemp(self):
        if self._basetemp is not None:
            return self._basetemp

        if self._given_basetemp is not None:
            basetemp = self._given_basetemp
            if basetemp.exists():
                rm_rf(basetemp)
            basetemp.mkdir(parents=True, exist_ok=True)
            basetemp = basetemp.resolve()
        else:
            from_env = os.environ.get("PYTEST_DEBUG_TEMPROOT")
            temproot = Path(from_env or tempfile.gettempdir()).resolve()
            user = pytest_tmpdir.get_user() or "unknown"
            rootdir = temproot.joinpath(f"pytest-of-{user}")
            try:
                rootdir.mkdir(parents=True, exist_ok=True)
            except OSError:
                rootdir = temproot.joinpath("pytest-of-unknown")
                rootdir.mkdir(parents=True, exist_ok=True)

            keep = self._retention_count
            if self._retention_policy == "none":
                keep = 0
            basetemp = make_numbered_dir_with_cleanup(
                prefix="pytest-",
                root=rootdir,
                keep=keep,
                lock_timeout=LOCK_TIMEOUT,
                mode=0o777,
            )

        assert basetemp is not None, basetemp
        self._basetemp = basetemp
        self._trace("new basetemp", basetemp)
        return basetemp

    def mktemp(self, basename: str, numbered: bool = True) -> Path:
        basename = self._ensure_relative_to_basetemp(basename)
        if not numbered:
            path = self.getbasetemp().joinpath(basename)
            path.mkdir(parents=True, exist_ok=False)
            return path

        path = make_numbered_dir(root=self.getbasetemp(), prefix=basename, mode=0o777)
        self._trace("mktemp", path)
        return path

    def cleanup_dead_symlinks(root: Path) -> None:
        try:
            for left_dir in root.iterdir():
                if left_dir.is_symlink() and not left_dir.resolve().exists():
                    left_dir.unlink()
        except PermissionError:
            return

    pytest_tmpdir.TempPathFactory.getbasetemp = getbasetemp
    pytest_tmpdir.TempPathFactory.mktemp = mktemp
    pytest_tmpdir.cleanup_dead_symlinks = cleanup_dead_symlinks


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + f"-{os.getpid()}"
    temp_root = RUNTIME_ROOT / run_id
    cache_dir = RUNTIME_ROOT / "cache"

    for directory in (temp_root, cache_dir):
        directory.mkdir(parents=True, exist_ok=True)

    short_temp = _short_path(temp_root)
    os.environ.update(
        {
            "TMP": short_temp,
            "TEMP": short_temp,
            "TMPDIR": short_temp,
            "PYTEST_DEBUG_TEMPROOT": short_temp,
        }
    )
    os.environ.pop("PYTHONUTF8", None)
    os.environ.pop("PYTHONIOENCODING", None)

    _patch_pytest_for_windows()

    import pytest

    args = sys.argv[1:] or ["tests/", "-v"]
    args.extend(["-o", f"cache_dir={_short_path(cache_dir)}"])
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
