"""
Caso avanzado: escalón en P_ref (modo P/Q).

Escenario:
- P_ref = P0 en el primer tramo.
- P_ref = P1 en el segundo tramo.
- Q_ref se mantiene constante (el que venga en el JSON).

Implementación:
- Se cargan params.json y scenario.json (tests/data).
- Se ejecutan dos simulaciones independientes usando run_simulation:
    1) Segmento 1: [0, t_step] con P_ref = P0
    2) Segmento 2: [0, t_end - t_step] con P_ref = P1
- Para la exportación y trazado se respetan los resultados devueltos
  por run_simulation, con una conversión mínima a snapshots cuando
  se exporta (dict-de-listas -> lista-de-dicts).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Mapping, Sequence

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
    Asumimos este archivo en: examples/advanced/case_step_pref.py
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
# Simulación de los dos segmentos
# ---------------------------------------------------------------------------


def run_case_step_pref(
    P0: float = 0.5,
    P1: float = 1.0,
    t_step: float = 0.25,
    t_end: float = 0.5,
    dt: float = 1e-3,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Ejecuta el caso avanzado de escalón en P_ref.

    Devuelve:
    - results_seg1: resultados de run_simulation con P_ref = P0, [0, t_step]
    - results_seg2: resultados de run_simulation con P_ref = P1, [0, t_end - t_step]
    """
    root = _get_project_root()
    params_path = root / "tests" / "data" / "params.json"
    scenario_path = root / "tests" / "data" / "scenario.json"

    params_base = _load_json(params_path)
    scenario_base = _load_json(scenario_path)

    # Copias base
    params_config_1 = dict(params_base)
    scenario_config_1 = dict(scenario_base)

    params_config_2 = dict(params_base)
    scenario_config_2 = dict(scenario_base)

    # Limpieza defensiva de NR (por si en los JSON hubiera strings)
    for cfg in (params_config_1, params_config_2):
        for k in ("nr_norm", "nr_verbose"):
            v = cfg.get(k)
            if isinstance(v, str):
                cfg.pop(k, None)

    # --- Segmento 1: P_ref = P0, [0, t_step] ---
    _set_pref(params_config_1, scenario_config_1, P0)

    results_seg1 = run_simulation(
        params_config=params_config_1,
        scenario_config=scenario_config_1,
        t_end=t_step,
        dt=dt,
    )

    # --- Segmento 2: P_ref = P1, [0, t_end - t_step] ---
    _set_pref(params_config_2, scenario_config_2, P1)

    results_seg2 = run_simulation(
        params_config=params_config_2,
        scenario_config=scenario_config_2,
        t_end=max(t_end - t_step, 0.0),
        dt=dt,
    )

    return results_seg1, results_seg2


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------


def plot_results(results_seg1: Dict[str, Any],
                 results_seg2: Dict[str, Any],
                 t_step: float,
                 title_suffix: str = "") -> None:
    # Segmento 1
    t1 = results_seg1["time"]
    x1 = results_seg1["x"]
    y1 = results_seg1.get("y", {})

    # Segmento 2 (desplazamos tiempos en +t_step para que se vea continuo)
    t2 = [t_step + t for t in results_seg2["time"]]
    x2 = results_seg2["x"]
    y2 = results_seg2.get("y", {})

    def _extract_series(hist, key):
        # Soporta lista-de-dicts y dict-de-listas
        try:
            return [s.get(key) for s in hist]
        except AttributeError:
            return list(hist.get(key, []))

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

    # Corrientes
    plt.figure()
    plt.plot(t1, id1, label="id (P0)")
    plt.plot(t1, iq1, label="iq (P0)")
    plt.plot(t2, id2, "--", label="id (P1)")
    plt.plot(t2, iq2, "--", label="iq (P1)")
    plt.xlabel("t [s]")
    plt.ylabel("Corriente [pu]")
    plt.title(f"Corrientes dq {title_suffix}")
    plt.grid(True)
    plt.legend()

    # Vdc
    plt.figure()
    plt.plot(t1, vdc1, label="Vdc (P0)")
    plt.plot(t2, vdc2, "--", label="Vdc (P1)")
    plt.xlabel("t [s]")
    plt.ylabel("Vdc [pu]")
    plt.title(f"Tensión DC {title_suffix}")
    plt.grid(True)
    plt.legend()

    # Potencias
    if any(p1) or any(p2) or any(q1) or any(q2):
        plt.figure()
        if any(p1):
            plt.plot(t1, p1, label="P_ac (P0)")
        if any(p2):
            plt.plot(t2, p2, "--", label="P_ac (P1)")
        if any(q1):
            plt.plot(t1, q1, label="Q_ac (P0)")
        if any(q2):
            plt.plot(t2, q2, "--", label="Q_ac (P1)")
        plt.xlabel("t [s]")
        plt.ylabel("Potencias [pu]")
        plt.title(f"P_ac / Q_ac {title_suffix}")
        plt.grid(True)
        plt.legend()

    plt.show()


# ---------------------------------------------------------------------------
# Exportación (ya normalizada para el exporter)
# ---------------------------------------------------------------------------


def export_results(results_seg1: Dict[str, Any],
                   results_seg2: Dict[str, Any],
                   name: str = "step_pref") -> None:
    """
    Exporta ambos segmentos usando la API oficial de exportación,
    normalizando x/y al formato lista-de-dicts que espera exporter.
    """
    root = _get_project_root()
    out_dir = root / "outputs" / "advanced"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = ExportConfig(overwrite=True)

    # Segmento 1
    t1 = results_seg1["time"]
    x1_raw = results_seg1["x"]
    y1_raw = results_seg1.get("y", {})

    x1_norm, y1_norm = _history_to_snapshots(t1, x1_raw, y1_raw)

    csv_path_1 = out_dir / f"{name}_seg1.csv"
    parquet_path_1 = out_dir / f"{name}_seg1.parquet"

    export_simulation_csv(t1, x1_norm, y1_norm, str(csv_path_1), config=cfg)
    print(f"CSV (seg1) escrito en: {csv_path_1}")

    try:
        export_simulation_parquet(t1, x1_norm, y1_norm, str(parquet_path_1), config=cfg)
        print(f"Parquet (seg1) escrito en: {parquet_path_1}")
    except Exception as exc:
        print(f"No se pudo escribir Parquet seg1 ({exc}).")

    # Segmento 2
    t2 = results_seg2["time"]
    x2_raw = results_seg2["x"]
    y2_raw = results_seg2.get("y", {})

    x2_norm, y2_norm = _history_to_snapshots(t2, x2_raw, y2_raw)

    csv_path_2 = out_dir / f"{name}_seg2.csv"
    parquet_path_2 = out_dir / f"{name}_seg2.parquet"

    export_simulation_csv(t2, x2_norm, y2_norm, str(csv_path_2), config=cfg)
    print(f"CSV (seg2) escrito en: {csv_path_2}")

    try:
        export_simulation_parquet(t2, x2_norm, y2_norm, str(parquet_path_2), config=cfg)
        print(f"Parquet (seg2) escrito en: {parquet_path_2}")
    except Exception as exc:
        print(f"No se pudo escribir Parquet seg2 ({exc}).")


# ---------------------------------------------------------------------------
# Punto de entrada de script
# ---------------------------------------------------------------------------


def main() -> None:
    configure_global_logger_from_config({"log_level": "warning", "log_json": False})

    P0 = 0.5
    P1 = 1.0
    t_step = 0.25
    t_end = 0.5
    dt = 1e-3

    res1, res2 = run_case_step_pref(P0=P0, P1=P1, t_step=t_step, t_end=t_end, dt=dt)

    plot_results(res1, res2, t_step=t_step,
                 title_suffix=f"(P_ref: {P0} -> {P1} en t={t_step}s)")
    export_results(res1, res2, name="step_pref")


if __name__ == "__main__":
    main()
