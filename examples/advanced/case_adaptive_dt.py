"""
Caso avanzado: dt adaptativo vs dt fijo.

Escenario:
- Se simula el mismo caso base dos veces:
    1) Integración con dt fijo.
    2) Integración con dt adaptativo.
- Se comparan las corrientes, Vdc y el historial de pasos de tiempo.

Notas:
- Este script detecta automáticamente si la API pública `run_simulation`
  soporta el parámetro keyword `adaptive`. Si no existe, activa el modo
  adaptativo vía params_config["adaptive"] = True.
- No se modifica la ingeniería del modelo; solo se configuran las
  opciones del solver desde fuera.
"""

from __future__ import annotations

import json
import inspect
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

# Detectamos si run_simulation tiene kwarg "adaptive"
_RUN_SIM_HAS_ADAPTIVE = "adaptive" in inspect.signature(run_simulation).parameters


# ---------------------------------------------------------------------------
# Utilidades de carga
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_project_root() -> Path:
    """
    Asumimos este archivo en: examples/advanced/case_adaptive_dt.py
    -> raíz del proyecto está dos niveles arriba.
    """
    return Path(__file__).resolve().parents[2]


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
# Simulación: dt fijo vs dt adaptativo
# ---------------------------------------------------------------------------


def run_case_adaptive_dt(
    t_end: float = 0.5,
    dt_fixed: float = 1e-3,
    dt_initial_adaptive: float = 5e-3,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Ejecuta el caso avanzado dt fijo vs dt adaptativo.

    Devuelve:
    - results_fixed:     resultados con dt fijo.
    - results_adaptive:  resultados con dt adaptativo.
    """
    root = _get_project_root()
    params_path = root / "tests" / "data" / "params.json"
    scenario_path = root / "tests" / "data" / "scenario.json"

    params_base = _load_json(params_path)
    scenario_base = _load_json(scenario_path)

    # Copias base
    params_fixed = dict(params_base)
    params_adapt = dict(params_base)
    scenario_config = dict(scenario_base)

    # Limpieza defensiva de NR (por si en los JSON hubiera strings)
    for cfg in (params_fixed, params_adapt):
        for k in ("nr_norm", "nr_verbose"):
            v = cfg.get(k)
            if isinstance(v, str):
                cfg.pop(k, None)

    # --- Simulación con dt fijo ---
    results_fixed = run_simulation(
        params_config=params_fixed,
        scenario_config=scenario_config,
        t_end=t_end,
        dt=dt_fixed,
        # adaptive implícitamente False (por defecto)
    )

    # --- Simulación con dt adaptativo ---
    if _RUN_SIM_HAS_ADAPTIVE:
        # La API soporta kwarg adaptive
        results_adaptive = run_simulation(
            params_config=params_adapt,
            scenario_config=scenario_config,
            t_end=t_end,
            dt=dt_initial_adaptive,  # dt inicial / máximo, según implementación
            adaptive=True,
        )
    else:
        # Activamos modo adaptativo vía params_config
        params_adapt["adaptive"] = True
        results_adaptive = run_simulation(
            params_config=params_adapt,
            scenario_config=scenario_config,
            t_end=t_end,
            dt=dt_initial_adaptive,
        )

    return results_fixed, results_adaptive


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


def _compute_dt_series(times: Sequence[float]) -> List[float]:
    if len(times) < 2:
        return []
    return [times[i + 1] - times[i] for i in range(len(times) - 1)]


def plot_results(results_fixed: Dict[str, Any],
                 results_adaptive: Dict[str, Any],
                 t_end: float,
                 title_suffix: str = "") -> None:
    # Datos fijos
    t_fix = results_fixed["time"]
    x_fix = results_fixed["x"]
    y_fix = results_fixed.get("y", {})

    # Datos adaptativos
    t_ad = results_adaptive["time"]
    x_ad = results_adaptive["x"]
    y_ad = results_adaptive.get("y", {})

    # Series básicas
    id_fix = _extract_series(x_fix, "id")
    iq_fix = _extract_series(x_fix, "iq")
    vdc_fix = _extract_series(x_fix, "Vdc")
    p_fix = _extract_series(y_fix, "P_ac")
    q_fix = _extract_series(y_fix, "Q_ac")

    id_ad = _extract_series(x_ad, "id")
    iq_ad = _extract_series(x_ad, "iq")
    vdc_ad = _extract_series(x_ad, "Vdc")
    p_ad = _extract_series(y_ad, "P_ac")
    q_ad = _extract_series(y_ad, "Q_ac")

    # dt(t)
    dt_fix = _compute_dt_series(t_fix)
    dt_ad = _compute_dt_series(t_ad)
    t_fix_mid = t_fix[1:]
    t_ad_mid = t_ad[1:]

    # Corrientes
    plt.figure()
    plt.plot(t_fix, id_fix, label="id (dt fijo)")
    plt.plot(t_fix, iq_fix, label="iq (dt fijo)")
    plt.plot(t_ad, id_ad, "--", label="id (dt adaptativo)")
    plt.plot(t_ad, iq_ad, "--", label="iq (dt adaptativo)")
    plt.xlabel("t [s]")
    plt.ylabel("Corriente [pu]")
    plt.title(f"Corrientes dq {title_suffix}")
    plt.grid(True)
    plt.legend()

    # Vdc
    plt.figure()
    plt.plot(t_fix, vdc_fix, label="Vdc (dt fijo)")
    plt.plot(t_ad, vdc_ad, "--", label="Vdc (dt adaptativo)")
    plt.xlabel("t [s]")
    plt.ylabel("Vdc [pu]")
    plt.title(f"Tensión DC {title_suffix}")
    plt.grid(True)
    plt.legend()

    # Potencias
    if any(p_fix) or any(p_ad) or any(q_fix) or any(q_ad):
        plt.figure()
        if any(p_fix):
            plt.plot(t_fix, p_fix, label="P_ac (dt fijo)")
        if any(p_ad):
            plt.plot(t_ad, p_ad, "--", label="P_ac (dt adaptativo)")
        if any(q_fix):
            plt.plot(t_fix, q_fix, label="Q_ac (dt fijo)")
        if any(q_ad):
            plt.plot(t_ad, q_ad, "--", label="Q_ac (dt adaptativo)")
        plt.xlabel("t [s]")
        plt.ylabel("Potencias [pu]")
        plt.title(f"P_ac / Q_ac {title_suffix}")
        plt.grid(True)
        plt.legend()

    # Historial de dt
    plt.figure()
    if dt_fix:
        plt.step(t_fix_mid, dt_fix, where="post", label="dt fijo")
    if dt_ad:
        plt.step(t_ad_mid, dt_ad, where="post", label="dt adaptativo")
    plt.xlabel("t [s]")
    plt.ylabel("dt [s]")
    plt.title("Historial de pasos de tiempo")
    plt.grid(True)
    plt.legend()

    plt.show()


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------


def export_results(results_fixed: Dict[str, Any],
                   results_adaptive: Dict[str, Any],
                   name: str = "adaptive_dt") -> None:
    """
    Exporta ambos casos usando la API oficial de exportación,
    normalizando x/y al formato lista-de-dicts que espera exporter.
    """
    root = _get_project_root()
    out_dir = root / "outputs" / "advanced"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = ExportConfig(overwrite=True)

    # Caso dt fijo
    t_fix = results_fixed["time"]
    x_fix_raw = results_fixed["x"]
    y_fix_raw = results_fixed.get("y", {})

    x_fix_norm, y_fix_norm = _history_to_snapshots(t_fix, x_fix_raw, y_fix_raw)

    csv_path_fix = out_dir / f"{name}_fixed.csv"
    parquet_path_fix = out_dir / f"{name}_fixed.parquet"

    export_simulation_csv(t_fix, x_fix_norm, y_fix_norm, str(csv_path_fix), config=cfg)
    print(f"CSV (dt fijo) escrito en: {csv_path_fix}")

    try:
        export_simulation_parquet(
            t_fix, x_fix_norm, y_fix_norm, str(parquet_path_fix), config=cfg
        )
        print(f"Parquet (dt fijo) escrito en: {parquet_path_fix}")
    except Exception as exc:
        print(f"No se pudo escribir Parquet dt fijo ({exc}).")

    # Caso dt adaptativo
    t_ad = results_adaptive["time"]
    x_ad_raw = results_adaptive["x"]
    y_ad_raw = results_adaptive.get("y", {})

    x_ad_norm, y_ad_norm = _history_to_snapshots(t_ad, x_ad_raw, y_ad_raw)

    csv_path_ad = out_dir / f"{name}_adaptive.csv"
    parquet_path_ad = out_dir / f"{name}_adaptive.parquet"

    export_simulation_csv(t_ad, x_ad_norm, y_ad_norm, str(csv_path_ad), config=cfg)
    print(f"CSV (dt adaptativo) escrito en: {csv_path_ad}")

    try:
        export_simulation_parquet(
            t_ad, x_ad_norm, y_ad_norm, str(parquet_path_ad), config=cfg
        )
        print(f"Parquet (dt adaptativo) escrito en: {parquet_path_ad}")
    except Exception as exc:
        print(f"No se pudo escribir Parquet dt adaptativo ({exc}).")


# ---------------------------------------------------------------------------
# Punto de entrada de script
# ---------------------------------------------------------------------------


def main() -> None:
    configure_global_logger_from_config({"log_level": "warning", "log_json": False})

    t_end = 0.5
    dt_fixed = 1e-3
    dt_initial_adaptive = 5e-3

    res_fix, res_ad = run_case_adaptive_dt(
        t_end=t_end,
        dt_fixed=dt_fixed,
        dt_initial_adaptive=dt_initial_adaptive,
    )

    plot_results(
        res_fix,
        res_ad,
        t_end=t_end,
        title_suffix=f"(dt fijo={dt_fixed}, dt_ini_adapt={dt_initial_adaptive})",
    )
    export_results(res_fix, res_ad, name="adaptive_dt")


if __name__ == "__main__":
    main()
