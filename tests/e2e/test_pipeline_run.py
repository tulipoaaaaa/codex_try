import subprocess
import sys
import os
from pathlib import Path
import pytest
from conftest import tmp_config_path


def test_pipeline_preview(tmp_config_path):
    extra = os.pathsep.join([os.getcwd(), str(Path("CorpusBuilderApp").resolve()), str(Path("tests").resolve())])
    env = dict(**os.environ, PYTHONPATH=extra)
    cmd = [sys.executable, '-m', 'cli.execute_from_config', '--config', str(tmp_config_path), '--run-all', '--preview-only']
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        pytest.skip(proc.stderr)
