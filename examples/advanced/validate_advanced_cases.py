"""
Validación rápida de casos avanzados.

Este script ejecuta todos los casos de `examples.advanced` como módulos:

    - case_step_pref
    - case_vary_vdc
    - case_current_limit
    - case_adaptive_dt

Objetivo:
- Verificar que todos los scripts se ejecutan sin errores.
- Comprobar que la exportación a CSV/Parquet no rompe la ejecución.

Uso (desde la raíz del repositorio):

    python -m examples.advanced.validate_advanced_cases
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List


# Lista de módulos de casos avanzados a validar
ADVANCED_CASES: List[str] = [
    "case_step_pref",
    "case_vary_vdc",
    "case_current_limit",
    "case_adaptive_dt",
]


def _get_repo_root() -> Path:
    """
    Asumimos este archivo en: examples/advanced/validate_advanced_cases.py
    -> raíz del proyecto está dos niveles arriba.
    """
    return Path(__file__).resolve().parents[2]


def run_case(module_name: str) -> None:
    """
    Ejecuta un caso avanzado como módulo:

        python -m examples.advanced.<module_name>

    Forzamos PYTHONPATH para que incluya `<raiz_repo>/src` y así
    los scripts usen siempre el código local de desarrollo.
    """
    repo_root = _get_repo_root()
    full_module = f"examples.advanced.{module_name}"
    cmd = ["python", "-m", full_module]

    print(f"\n=== Ejecutando {full_module} ===")

    # Entorno heredado + PYTHONPATH con src
    env = os.environ.copy()
    src_path = str(repo_root / "src")
    old_pp = env.get("PYTHONPATH", "")
    if old_pp:
        env["PYTHONPATH"] = src_path + os.pathsep + old_pp
    else:
        env["PYTHONPATH"] = src_path

    # Ejecutamos el módulo como un proceso hijo
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        text=True,
        capture_output=True,
        env=env,
    )

    if result.returncode != 0:
        print(f"❌ ERROR en {full_module}")
        print("----- STDOUT -----")
        print(result.stdout)
        print("----- STDERR -----")
        print(result.stderr)
        raise RuntimeError(f"Validación falló para {full_module}")

    print(f"✔ OK {full_module}")
    # Si quieres ver la salida normal, descomenta:
    # print(result.stdout)


def main() -> None:
    print("========================================")
    print(" Validación rápida de casos avanzados")
    print("========================================")

    for case in ADVANCED_CASES:
        run_case(case)

    print("\n========================================")
    print(" Todos los casos avanzados finalizaron OK")
    print("========================================")


if __name__ == "__main__":
    main()
