# tests/test_cli_main.py
"""
Smoke test de la CLI.

Ejecuta el comando:

    python -m vscsim.cli.main ...

usando archivos JSON de ejemplo en tests/data/.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_cli_main_smoke():
    repo_root = Path(__file__).resolve().parents[1]
    params = repo_root / "tests" / "data" / "params.json"
    scenario = repo_root / "tests" / "data" / "scenario.json"

    # Asegurar que 'src' está en PYTHONPATH para que 'vscsim' sea importable
    env = os.environ.copy()
    src = repo_root / "src"
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        sys.executable,
        "-m",
        "vscsim.cli.main",
        "--params",
        str(params),
        "--scenario",
        str(scenario),
        "--t-end",
        "0.01",
        "--dt",
        "0.01",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    assert proc.returncode == 0
    assert "Simulación completada" in proc.stdout

    print(
        "[SUMMARY] test_cli_main_smoke: "
        f"returncode={proc.returncode}, stdout_snippet={proc.stdout[:200]}"
    )
