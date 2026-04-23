from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import opc_research


def test_main_json_output_is_ascii_safe_and_slim(tmp_path: Path) -> None:
    project_root = tmp_path / "sample-project"
    (project_root / ".opc").mkdir(parents=True)

    fake_result = {
        "query": "增长 飞轮",
        "markdown_path": "C:/项目/research.md",
        "meta_path": "C:/项目/research.meta.json",
        "docs_mirror": "C:/项目/docs/research.md",
        "insights": [{"id": "1"}, {"id": "2"}],
    }

    stdout = io.StringIO()
    argv = [
        "opc_research.py",
        "--cwd",
        str(project_root),
        "--query",
        "增长 飞轮",
        "--json",
    ]

    with patch.object(opc_research, "run_market_research", return_value=fake_result):
        with patch.object(sys, "argv", argv):
            with redirect_stdout(stdout):
                opc_research.main()

    text = stdout.getvalue()
    payload = json.loads(text)

    assert payload["insights_preview"] == 2
    assert "insights" not in payload
    assert "\\u9879\\u76ee" in text
