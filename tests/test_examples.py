import io
import os
import runpy
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = tuple(sorted((ROOT / "examples").glob("*.py")))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.name)
def test_example_runs_from_an_isolated_working_directory(example, tmp_path):
    environment = os.environ.copy()
    pythonpath = [str(ROOT), *filter(None, (environment.get("PYTHONPATH"),))]
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath)
    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda example: example.name)
def test_importing_example_has_no_output_or_files(example, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    stdout = io.StringIO()
    stderr = io.StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        runpy.run_path(str(example), run_name="example_import")

    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    assert not tuple(tmp_path.iterdir())
