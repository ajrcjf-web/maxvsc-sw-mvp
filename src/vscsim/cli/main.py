"""
CLI mínima para el simulador RMS VSC-HVDC.

Permite:
- Cargar parámetros desde un archivo JSON.
- Cargar escenario desde un archivo JSON.
- Ejecutar una simulación básica usando la API run_simulation.
- Imprimir un resumen de resultados.

Esta CLI no altera el modelo RMS, la DAE, el solver ni el control.
Solo llama a:

- api.simulation.run_simulation

Implementación conforme a ENG-1.0.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from vscsim.api.simulation import run_simulation


def _load_json(path_str: str) -> dict[str, Any]:
    """Carga un archivo JSON y lo devuelve como dict."""
    path = Path(path_str)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    """
    Punto de entrada CLI.

    Ejemplo de uso:

        python -m vscsim.cli.main \\
            --params params.json \\
            --scenario scenario.json \\
            --t-end 1.0 \\
            --dt 0.01

    donde:
    - params.json contiene los parámetros para load_parameters.
    - scenario.json contiene el escenario para load_scenario y, dentro
      de él, opcionalmente:
          "initial_conditions": { ... }

    Este comando no modifica la ingeniería del simulador; solo encadena
    la carga de datos y la llamada a run_simulation.
    """
    parser = argparse.ArgumentParser(
        description="Simulador RMS VSC-HVDC (ENG-1.0, ETU v1.3)."
    )
    parser.add_argument(
        "--params",
        required=True,
        help="Ruta al archivo JSON con la configuración de parámetros.",
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Ruta al archivo JSON con la configuración del escenario.",
    )
    parser.add_argument(
        "--t-end",
        type=float,
        default=1.0,
        help="Tiempo final de simulación (segundos).",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.01,
        help="Paso de integración (segundos).",
    )

    args = parser.parse_args(argv)

    # Cargar configuración de parámetros y escenario
    params_config = _load_json(args.params)
    scenario_config = _load_json(args.scenario)

    # Ejecutar la simulación usando la API
    results = run_simulation(
        params_config=params_config,
        scenario_config=scenario_config,
        t_end=args.t_end,
        dt=args.dt,
    )

    # Resumen simple en stdout: estado final
    time = results["time"]
    x_hist = results["x"]
    y_hist = results["y"]

    if time:
        t_final = time[-1]
        id_final = x_hist["id"][-1]
        iq_final = x_hist["iq"][-1]
        Vdc_final = x_hist["Vdc"][-1]
        Idc_final = y_hist["Idc"][-1]
        P_ac_final = y_hist["P_ac"][-1]
        Q_ac_final = y_hist["Q_ac"][-1]

        print(f"Simulación completada hasta t = {t_final:.6f} s")
        print("Estado final:")
        print(f"  id   = {id_final:.6g}")
        print(f"  iq   = {iq_final:.6g}")
        print(f"  Vdc  = {Vdc_final:.6g}")
        print("Variables algebraicas finales:")
        print(f"  Idc  = {Idc_final:.6g}")
        print(f"  P_ac = {P_ac_final:.6g}")
        print(f"  Q_ac = {Q_ac_final:.6g}")
    else:
        print("Simulación sin resultados (lista de tiempos vacía).")

    return 0


def run():
    import sys

    sys.exit(main())


if __name__ == "__main__":
    run()
