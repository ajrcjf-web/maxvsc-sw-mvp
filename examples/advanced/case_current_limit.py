"""
Caso avanzado: límite de corriente (comparación P_ref nominal vs forzado).

Escenario:
- Caso nominal:   P_ref = P_nominal
- Caso forzado:   P_ref = P_alto  (pensado para empujar la corriente al límite)
- Q_ref se mantiene constante (el que venga en el JSON).

Notas:
- Este script NO implementa el límite de corriente; solo prepara un caso
  que hace trabajar al convertidor a alta potencia. Cuando el modelo
  incluya la limitación física, se debería ver la saturación reflejada
  en las corrientes y/o potencias.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Mapping, Sequence

import math
import matplotlib.pyplot as plt

from vscsim.api.simulation import run_simulation
from vscsim.utils.logger import configure_global_logger_from_config
from vscsim.utils.exporter import (
    export_simulation_csv,
    export_simulation_parquet,
    ExportConfig,
)


# ---------------------------------------------------------------------------
# Utilidades de carga
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_project_root() -> Path:
    """
    Asumimos este archivo en: examples/advanced/case_current_limit.py
    -> raíz del proyecto está dos niveles arriba.
    """
    return Path(__file__).resolve().parents[2]


def _set_pref(params_config: Dict[str, Any],
              scenario_config: Dict[str, Any],
              P_ref: float) -> None:
    """
    Coloca P_ref en params_config o scenario_config según exista la clave.
    No crea claves nuevas, solo actualiza si ya están.
    """
    if "P_ref" in params_config:
        params_config["P_ref"] = float(P_ref)
    elif "P_ref" in scenario_config:
        scenario_config["P_ref"] = float(P_ref)


# ---------------------------------------------------------------------------
# Conversión para exportación: dict-de-listas -> lista-de-dicts
# ---------------------------------------------------------------------------


def _history_to_snapshots(
    times: Sequence[float],
    x_hist: Any,
    y_hist: Any,
) -> Tuple[List[Mapping[str, float]], List[Mapping[str, float]]]:
    """
    Normaliza x_hist / y_hist al formato esperado por export_simulation_*:

        Sequence[Mapping[str, float]]

    Soporta:

    - lista de dicts (se deja tal cual)
    - dict de listas (lo convertimos a lista de dicts)
    """
    n = len(times)

    def _convert(d: Any) -> List[Mapping[str, float]]:
        if not d:
            return []

        # Caso 1: ya es lista de dicts
        if isinstance(d, Sequence) and not isinstance(d, (str, bytes)):
            if d and isinstance(d[0], Mapping):
                return list(d)

        # Caso 2: dict de listas -> lo expandimos a snapshots
        if isinstance(d, dict):
            return [
                {k: (v[i] if i < len(v) else None) for k, v in d.items()}
                for i in range(n)
            ]

        raise TypeError(f"Estructura de historial no soportada: {type(d)}")

    return _convert(x_hist), _convert(y_hist)


# ---------------------------------------------------------------------------
# Simulación de los dos casos
# ---------------------------------------------------------------------------


def run_case_current_limit(
    P_nominal: float = 0.5,
    P_alto: float = 1.5,
    t_end: float = 0.5,
    dt: float = 1e-3,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Ejecuta el caso avanzado de límite de corriente.

    Devuelve:
    - results_nominal: resultados con P_ref = P_nominal
    - results_alto:    resultados con P_ref = P_alto
    """
    root = _get_project_root()
    params_path = root / "tests" / "data" / "params.json"
    scenario_path = root / "tests" / "data" / "scenario.json"

    params_base = _load_json(params_path)
    scenario_base = _load_json(scenario_path)

    # Config nominal
    params_nom = dict(params_base)
    scen_nom = dict(scenario_base)

    # Config forzada
    params_hi = dict(params_base)
    scen_hi = dict(scenario_base)

    # Limpieza defensiva de NR (por si en los JSON hubiera strings)
    for cfg in (params_nom, params_hi):
        for k in ("nr_norm", "nr_verbose"):
            v = cfg.get(k)
            if isinstance(v, str):
                cfg.pop(k, None)

    # Caso nominal
    _set_pref(params_nom, scen_nom, P_nominal)
    results_nominal = run_simulation(
        params_config=params_nom,
        scenario_config=scen_nom,
        t_end=t_end,
        dt=dt,
    )

    # Caso forzado
    _set_pref(params_hi, scen_hi, P_alto)
    results_alto = run_simulation(
        params_config=params_hi,
        scenario_config=scen_hi,
        t_end=t_end,
        dt=dt,
    )

    return results_nominal, results_alto


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------


def _extract_series(hist, key):
    # Soporta lista-de-dicts y dict-de-listas
    try:
        # lista de snapshots
        return [s.get(key) for s in hist]
    except AttributeError:
        # dict de listas
        return list(hist.get(key, []))


def plot_results(results_nominal: Dict[str, Any],
                 results_alto: Dict[str, Any],
                 P_nominal: float,
                 P_alto: float,
                 title_suffix: str = "") -> None:
    t1 = results_nominal["time"]
    x1 = results_nominal["x"]
    y1 = results_nominal.get("y", {})

    t2 = results_alto["time"]
    x2 = results_alto["x"]
    y2 = results_alto.get("y", {})

    id1 = _extract_series(x1, "id")
    iq1 = _extract_series(x1, "iq")
    vdc1 = _extract_series(x1, "Vdc")
    p1 = _extract_series(y1, "P_ac")
    q1 = _extract_series(y1, "Q_ac")

    id2 = _extract_series(x2, "id")
    iq2 = _extract_series(x2, "iq")
    vdc2 = _extract_series(x2, "Vdc")
    p2 = _extract_series(y2, "P_ac")
    q2 = _extract_series(y2, "Q_ac")

    # Módulo de corriente |I| si hay id, iq
    def _norm_i(id_series, iq_series):
        if not id_series or not iq_series:
            return []
        return [math.sqrt((id_series[i] or 0.0) ** 2 + (iq_series[i] or 0.0) ** 2)
                for i in range(min(len(id_series), len(iq_series)))]

    in1 = _norm_i(id1, iq1)
    in2 = _norm_i(id2, iq2)

    # Corrientes dq
    plt.figure()
    plt.plot(t1, id1, label=f"id (P={P_nominal})")
    plt.plot(t1, iq1, label=f"iq (P={P_nominal})")
    plt.plot(t2, id2, "--", label=f"id (P={P_alto})")
    plt.plot(t2, iq2, "--", label=f"iq (P={P_alto})")
    plt.xlabel("t [s]")
    plt.ylabel("Corriente [pu]")
    plt.title(f"Corrientes dq {title_suffix}")
    plt.grid(True)
    plt.legend()

    # Módulo de corriente
    if in1 or in2:
        plt.figure()
        if in1:
            plt.plot(t1[: len(in1)], in1, label=f"|I| (P={P_nominal})")
        if in2:
            plt.plot(t2[: len(in2)], in2, "--", label=f"|I| (P={P_alto})")
        plt.xlabel("t [s]")
        plt.ylabel("|I| [pu]")
        plt.title(f"Módulo de corriente {title_suffix}")
        plt.grid(True)
        plt.legend()

    # Vdc
    plt.figure()
    plt.plot(t1, vdc1, label=f"Vdc (P={P_nominal})")
    plt.plot(t2, vdc2, "--", label=f"Vdc (P={P_alto})")
    plt.xlabel("t [s]")
    plt.ylabel("Vdc [pu]")
    plt.title(f"Tensión DC {title_suffix}")
    plt.grid(True)
    plt.legend()

    # Potencias
    if any(p1) or any(p2) or any(q1) or any(q2):
        plt.figure()
        if any(p1):
            plt.plot(t1, p1, label=f"P_ac (P={P_nominal})")
        if any(p2):
            plt.plot(t2, p2, "--", label=f"P_ac (P={P_alto})")
        if any(q1):
            plt.plot(t1, q1, label=f"Q_ac (P={P_nominal})")
        if any(q2):
            plt.plot(t2, q2, "--", label=f"Q_ac (P={P_alto})")
        plt.xlabel("t [s]")
        plt.ylabel("Potencias [pu]")
        plt.title(f"P_ac / Q_ac {title_suffix}")
        plt.grid(True)
        plt.legend()

    plt.show()


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------


def export_results(results_nominal: Dict[str, Any],
                   results_alto: Dict[str, Any],
                   name: str = "current_limit") -> None:
    """
    Exporta ambos casos usando la API oficial de exportación,
    normalizando x/y al formato lista-de-dicts que espera exporter.
    """
    root = _get_project_root()
    out_dir = root / "outputs" / "advanced"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = ExportConfig(overwrite=True)

    # Caso nominal
    t1 = results_nominal["time"]
    x1_raw = results_nominal["x"]
    y1_raw = results_nominal.get("y", {})

    x1_norm, y1_norm = _history_to_snapshots(t1, x1_raw, y1_raw)

    csv_path_1 = out_dir / f"{name}_nominal.csv"
    parquet_path_1 = out_dir / f"{name}_nominal.parquet"

    export_simulation_csv(t1, x1_norm, y1_norm, str(csv_path_1), config=cfg)
    print(f"CSV (nominal) escrito en: {csv_path_1}")

    try:
        export_simulation_parquet(t1, x1_norm, y1_norm, str(parquet_path_1), config=cfg)
        print(f"Parquet (nominal) escrito en: {parquet_path_1}")
    except Exception as exc:
        print(f"No se pudo escribir Parquet nominal ({exc}).")

    # Caso forzado
    t2 = results_alto["time"]
    x2_raw = results_alto["x"]
    y2_raw = results_alto.get("y", {})

    x2_norm, y2_norm = _history_to_snapshots(t2, x2_raw, y2_raw)

    csv_path_2 = out_dir / f"{name}_alto.csv"
    parquet_path_2 = out_dir / f"{name}_alto.parquet"

    export_simulation_csv(t2, x2_norm, y2_norm, str(csv_path_2), config=cfg)
    print(f"CSV (alto) escrito en: {csv_path_2}")

    try:
        export_simulation_parquet(t2, x2_norm, y2_norm, str(parquet_path_2), config=cfg)
        print(f"Parquet (alto) escrito en: {parquet_path_2}")
    except Exception as exc:
        print(f"No se pudo escribir Parquet alto ({exc}).")


# ---------------------------------------------------------------------------
# Punto de entrada de script
# ---------------------------------------------------------------------------


def main() -> None:
    configure_global_logger_from_config({"log_level": "warning", "log_json": False})

    P_nominal = 0.5
    P_alto = 1.5
    t_end = 0.5
    dt = 1e-3

    res_nom, res_hi = run_case_current_limit(
        P_nominal=P_nominal,
        P_alto=P_alto,
        t_end=t_end,
        dt=dt,
    )

    plot_results(
        res_nom,
        res_hi,
        P_nominal=P_nominal,
        P_alto=P_alto,
        title_suffix=f"(P_ref: {P_nominal} vs {P_alto})",
    )
    export_results(res_nom, res_hi, name="current_limit")


if __name__ == "__main__":
    main()
