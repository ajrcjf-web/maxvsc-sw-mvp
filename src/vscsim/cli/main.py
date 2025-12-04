"""
CLI extendida para el simulador RMS VSC-HVDC (ETU v1.3).

Extiende la CLI mínima existente y añade:

- Selección de integrador (euler/rk1/rk2/rk4)
- Parámetros NR configurables
- Logging global (nivel + JSON)
- Exportación de resultados (CSV/Parquet)

NO modifica la ingeniería ni la API existente.
Solo prepara estructuras y delega en api.simulation.run_simulation().
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from vscsim.api.simulation import run_simulation
from vscsim.utils.logger import configure_global_logger_from_config
from vscsim.utils.exporter import (
    export_simulation_csv,
    export_simulation_parquet,
    ExportConfig,
)


# ---------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------
def _load_json(path_str: str) -> dict[str, Any]:
    """Carga un archivo JSON y lo devuelve como dict."""
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _inject_nr_params(params: dict[str, Any], args: argparse.Namespace) -> None:
    """
    Inyecta parámetros NR desde CLI al dict params del escenario.
    NO modifica ingeniería, solo setea claves ya soportadas por NR.
    """
    if args.nr_tol is not None:
        params["nr_tol"] = float(args.nr_tol)
    if args.nr_max_iter is not None:
        params["nr_max_iter"] = int(args.nr_max_iter)
    if args.nr_norm is not None:
        params["nr_norm"] = args.nr_norm
    if args.nr_verbose:
        params["nr_verbose"] = True


# ---------------------------------------------------------------------
# Parser CLI
# ---------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulador RMS VSC-HVDC – CLI extendida (ETU v1.3)"
    )

    # Archivos de entrada (igual que CLI original)
    parser.add_argument("--params", required=True, help="Archivo JSON de parámetros.")
    parser.add_argument("--scenario", required=True, help="Archivo JSON de escenario.")

    # Tiempo / integración
    parser.add_argument("--t-end", type=float, default=1.0, help="Tiempo final.")
    parser.add_argument("--dt", type=float, default=1e-3, help="Paso fijo o dt inicial.")

    # ---------------- Integrador (A2.3.1) ----------------
    parser.add_argument(
        "--integrator",
        type=str,
        choices=["euler", "rk1", "rk2", "rk4"],
        default="euler",
        help="Integrador dinámico.",
    )

    parser.add_argument(
        "--adaptive",
        action="store_true",
        help="Activar dt adaptativo.",
    )

    # --------------------- NR (A2.3.2) ---------------------
    parser.add_argument("--nr-tol", type=float, default=None, help="Tolerancia NR.")
    parser.add_argument("--nr-max-iter", type=int, default=None, help="Máx iter NR.")
    parser.add_argument("--nr-norm", type=str, choices=["max", "l2"], default=None)
    parser.add_argument(
        "--nr-verbose", action="store_true", help="Activar logging interno NR."
    )

    # ------------------- Logging (A2.3.3) ------------------
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["error", "warning", "info", "debug"],
        default="info",
        help="Nivel de logging global.",
    )
    parser.add_argument(
        "--log-json",
        action="store_true",
        help="Emitir logs en formato JSON-lines.",
    )

    # ------------------- Exportación (A2.3.4) ---------------
    parser.add_argument(
        "--export",
        type=str,
        choices=["none", "csv", "parquet"],
        default="none",
        help="Formato de exportación de resultados.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Archivo destino si se usa --export.",
    )

    return parser


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1) Cargar parámetros y escenario
    params_config = _load_json(args.params)
    scenario_config = _load_json(args.scenario)

    # 2) Inyectar NR desde CLI (NO ingeniería)
    _inject_nr_params(params_config, args)

    # 3) Logging global
    configure_global_logger_from_config(
        {
            "log_level": args.log_level,
            "log_json": args.log_json,
        }
    )

    # 4) Ejecutar simulación usando la API existente (sin modificarla)
    results = run_simulation(
        params_config=params_config,
        scenario_config=scenario_config,
        t_end=args.t_end,
        dt=args.dt,
        integrator=args.integrator,
        adaptive=args.adaptive,
    )

    # 5) Export (A2.3.4)
    if args.export != "none":
        if args.output is None:
            parser.error("--output es obligatorio si se usa --export")

        export_cfg = ExportConfig(overwrite=True)

        if args.export == "csv":
            export_simulation_csv(
                results["time"],
                results["x"],
                results["y"],
                args.output,
                config=export_cfg,
            )
        elif args.export == "parquet":
            export_simulation_parquet(
                results["time"],
                results["x"],
                results["y"],
                args.output,
                config=export_cfg,
            )

    return 0


def run():
    import sys

    sys.exit(main())


if __name__ == "__main__":
    run()
