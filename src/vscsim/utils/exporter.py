# src/vscsim/utils/exporter.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional
import csv
import json

from .config import ExportConfig

try:  # pragma: no cover - entorno sin pandas
    import pandas as _pd  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    _pd = None


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------


def _ensure_parent_dir(path: str | Path) -> Path:
    """Asegura que existe la carpeta padre y devuelve el Path normalizado."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def build_timeseries_rows(
    times: Sequence[float],
    x_history: Sequence[Mapping[str, float]],
    y_history: Optional[Sequence[Mapping[str, float]]] = None,
) -> list[dict[str, Any]]:
    """
    Combina time / x_hist / y_hist en una lista de dicts por instante de tiempo.

    Cada fila es:
        {"t": t_i, **x_history[i], **y_history[i]}
    """
    if y_history is None:
        y_history = []

    if len(times) != len(x_history):
        raise ValueError("len(times) y len(x_history) deben coincidir")

    if y_history and len(times) != len(y_history):
        raise ValueError("len(times) y len(y_history) deben coincidir")

    rows: list[dict[str, Any]] = []
    for i, t in enumerate(times):
        row: dict[str, Any] = {"t": float(t)}
        row.update(x_history[i])
        if y_history:
            row.update(y_history[i])
        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Exportaciones básicas: CSV / JSON / Parquet
# ---------------------------------------------------------------------------


def export_csv(
    rows: Sequence[Mapping[str, Any]],
    path: str | Path,
    config: Optional[ExportConfig] = None,
) -> None:
    """Escribe una lista de filas (dicts) a CSV plano."""
    cfg = config or ExportConfig()
    p = _ensure_parent_dir(path)

    if not cfg.overwrite and p.exists():
        raise FileExistsError(p)

    # Campos = unión de todas las claves en orden estable
    fieldnames: list[str]
    if rows:
        keys: list[str] = []
        for r in rows:
            for k in r.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    else:
        fieldnames = []

    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def export_json(
    rows: Sequence[Mapping[str, Any]],
    path: str | Path,
    config: Optional[ExportConfig] = None,
) -> None:
    """Escribe las filas como lista JSON."""
    cfg = config or ExportConfig()
    p = _ensure_parent_dir(path)

    if not cfg.overwrite and p.exists():
        raise FileExistsError(p)

    with p.open("w", encoding="utf-8") as f:
        json.dump(list(rows), f, indent=2)


def export_parquet(
    rows: Sequence[Mapping[str, Any]],
    path: str | Path,
    config: Optional[ExportConfig] = None,
    engine: Optional[str] = None,
) -> None:
    """
    Escribe Parquet usando pandas.

    - Si pandas no está disponible -> RuntimeError.
    - Si engine es None -> se deja que pandas use el modo 'auto'.
    - Si engine es "pyarrow" o "fastparquet", se pasa explícitamente.
    """
    if _pd is None:
        raise RuntimeError(
            "Parquet export requires pandas to be installed. "
            "Please install pandas (and a Parquet engine such as pyarrow).",
        )

    cfg = config or ExportConfig()
    p = _ensure_parent_dir(path)

    if not cfg.overwrite and p.exists():
        raise FileExistsError(p)

    df = _pd.DataFrame(list(rows))

    kwargs: dict[str, Any] = {}
    if engine is not None:
        kwargs["engine"] = engine

    df.to_parquet(p, **kwargs)


# ---------------------------------------------------------------------------
# API de alto nivel usada por CLI / casos avanzados
# ---------------------------------------------------------------------------


def export_simulation_csv(
    time: Sequence[float],
    x_history: Sequence[Mapping[str, float]],
    y_history: Optional[Sequence[Mapping[str, float]]],
    path: str,
    config: Optional[ExportConfig] = None,
) -> None:
    """
    Helper oficial para exportar una simulación completa a CSV.

    time: lista de tiempos
    x_history: lista de snapshots de estados (dicts)
    y_history: lista opcional de snapshots de algebraicas (dicts)
    """
    rows = build_timeseries_rows(time, x_history, y_history)
    export_csv(rows, path, config=config)


def export_simulation_parquet(
    time: Sequence[float],
    x_history: Sequence[Mapping[str, float]],
    y_history: Optional[Sequence[Mapping[str, float]]],
    path: str,
    config: Optional[ExportConfig] = None,
    engine: Optional[str] = None,
) -> None:
    """
    Helper oficial para exportar una simulación completa a Parquet.

    Se apoya en export_parquet y acepta engine=None / "pyarrow".
    """
    rows = build_timeseries_rows(time, x_history, y_history)
    export_parquet(rows, path, config=config, engine=engine)


__all__ = [
    "ExportConfig",
    "build_timeseries_rows",
    "export_csv",
    "export_json",
    "export_parquet",
    "export_simulation_csv",
    "export_simulation_parquet",
]
