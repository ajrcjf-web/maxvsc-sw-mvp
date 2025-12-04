"""
Funciones de exportación estándar para casos avanzados.
Convierte cualquier results{} al formato CSV / Parquet esperado.
"""

from pathlib import Path
from typing import Dict, Any, Sequence, Mapping, List
from vscsim.utils.exporter import export_simulation_csv, export_simulation_parquet, ExportConfig

def normalize_history(times, x_hist, y_hist):
    """
    Normaliza x_hist / y_hist a lista-de-dicts para exporter.
    """
    n = len(times)

    def _convert(d):
        if isinstance(d, list):
            return d
        if isinstance(d, dict):
            return [
                {k: d[k][i] if i < len(d[k]) else None for k in d}
                for i in range(n)
            ]
        raise TypeError("Formato no soportado")

    return _convert(x_hist), _convert(y_hist)


def export_results(results: Dict[str, Any], name: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = ExportConfig(overwrite=True)

    t = results["time"]
    x_norm, y_norm = normalize_history(t, results["x"], results.get("y", {}))

    out_csv = output_dir / f"{name}.csv"
    out_parquet = output_dir / f"{name}.parquet"

    export_simulation_csv(t, x_norm, y_norm, str(out_csv), config=cfg)
    print(f"CSV escrito en: {out_csv}")

    try:
        export_simulation_parquet(t, x_norm, y_norm, str(out_parquet), config=cfg)
        print(f"Parquet escrito en: {out_parquet}")
    except Exception as exc:
        print(f"No se pudo exportar Parquet ({exc})")
