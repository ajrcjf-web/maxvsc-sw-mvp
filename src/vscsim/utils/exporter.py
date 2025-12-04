"""
vscsim.utils.exporter

Utilidades de exportación de resultados de simulación a formatos estándar.

Este módulo es puramente de I/O:
- No depende de la ingeniería del modelo.
- No modifica el solver ni la secuencia de simulación.

Formatos soportados:
- CSV (siempre, usando la librería estándar de Python)
- Parquet (si hay pandas disponible en el entorno)

Además incluye helpers para exportar directamente resultados de simulación
(t, x_history, y_history) producidos por la API de simulación.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

try:
    import pandas as _pd  # type: ignore[import]
except Exception:
    _pd = None


@dataclass
class ExportConfig:
    """
    Configuración básica para exportación.

    Parameters
    ----------
    overwrite : bool
        Si False y el archivo ya existe, se lanza un error.
    """

    overwrite: bool = False


def _ensure_can_write(path: str, cfg: ExportConfig) -> None:
    """
    Verifica si el archivo de salida se puede escribir según la configuración.
    """
    if os.path.exists(path) and not cfg.overwrite:
        raise FileExistsError(
            f"Output file already exists and overwrite=False: {path!r}"
        )


def _normalize_rows(data: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """
    Normaliza una colección de filas en una lista de dicts.

    Cada elemento de `data` debe ser un Mapping (por ejemplo dict) que
    representa una fila. Las claves se usan como nombres de columna.
    """
    rows: list[dict[str, Any]] = []
    for row in data:
        rows.append(dict(row))
    return rows


# ---------------------------------------------------------------------
# Exportación CSV
# ---------------------------------------------------------------------


def export_csv(
    data: Iterable[Mapping[str, Any]],
    path: str,
    config: ExportConfig | None = None,
) -> None:
    """
    Exporta una colección de filas a CSV.

    Parameters
    ----------
    data :
        Iterable de mappings (por ejemplo, list[dict[str, Any]]), una fila por elemento.
    path :
        Ruta del archivo de salida CSV.
    config :
        Configuración de export (sobrescritura, etc.).

    Notes
    -----
    - Si `config.overwrite` es False y el archivo ya existe, se lanza FileExistsError.
    - El orden de las columnas se deduce de la primera fila.
    """
    cfg = config or ExportConfig()
    _ensure_can_write(path, cfg)

    rows = _normalize_rows(data)
    if not rows:
        # Crear CSV vacío sin cabecera
        with open(path, "w", newline="", encoding="utf-8") as f:
            pass
        return

    fieldnames = list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ---------------------------------------------------------------------
# Exportación Parquet
# ---------------------------------------------------------------------


def _ensure_pandas_for_parquet() -> None:
    """
    Verifica que pandas está disponible para exportar Parquet.

    La decisión de depender de pyarrow/fastparquet queda delegada a pandas
    y a la configuración del entorno.
    """
    if _pd is None:
        raise RuntimeError(
            "Parquet export requires pandas to be installed. "
            "Please install pandas (and a Parquet engine such as pyarrow)."
        )


def export_parquet(
    data: Iterable[Mapping[str, Any]],
    path: str,
    config: ExportConfig | None = None,
    *,
    engine: str | None = None,
) -> None:
    """
    Exporta una colección de filas a Parquet usando pandas, si está disponible.

    Parameters
    ----------
    data :
        Iterable de mappings (por ejemplo, list[dict[str, Any]]), una fila por elemento.
    path :
        Ruta del archivo de salida Parquet.
    config :
        Configuración de export (sobrescritura, etc.).
    engine :
        Motor Parquet a usar (por ejemplo "pyarrow" o "fastparquet").
        Si es None, pandas elegirá el motor por defecto.

    Notes
    -----
    - Si pandas no está disponible, se lanza RuntimeError.
    - Si `config.overwrite` es False y el archivo ya existe, se lanza FileExistsError.
    """
    _ensure_pandas_for_parquet()

    cfg = config or ExportConfig()
    _ensure_can_write(path, cfg)

    rows = _normalize_rows(data)
    df = _pd.DataFrame(rows)  # type: ignore[attr-defined]

    df.to_parquet(path, engine=engine)


# ---------------------------------------------------------------------
# Helpers de integración con la API de simulación
# ---------------------------------------------------------------------


def build_timeseries_rows(
    times: Sequence[float],
    x_history: Sequence[Mapping[str, float]],
    y_history: Sequence[Mapping[str, float]] | None = None,
) -> list[dict[str, Any]]:
    """
    Construye filas "planas" a partir de los resultados de simulación.

    Parameters
    ----------
    times :
        Secuencia de instantes t[k].
    x_history :
        Secuencia de estados dinámicos x[k] (dicts).
    y_history :
        Secuencia de variables algebraicas y[k] (dicts) o None.

    Returns
    -------
    list[dict[str, Any]]
        Lista de filas, cada una con la forma:

            {
                "t": ...,
                "<x_key>": ...,
                "<y_key>": ... (si y_history no es None)
            }

    Notas
    -----
    - Se asume que len(times) == len(x_history) y, si y_history no es None,
      también len(y_history) == len(times).
    """
    n = len(times)
    if len(x_history) != n:
        raise ValueError("len(times) y len(x_history) deben coincidir")
    if y_history is not None and len(y_history) != n:
        raise ValueError("len(times) y len(y_history) deben coincidir")

    rows: list[dict[str, Any]] = []
    for idx in range(n):
        t = times[idx]
        x = x_history[idx]
        row: dict[str, Any] = {"t": float(t)}

        # Estados dinámicos: se aplanan con sus claves originales (id, iq, Vdc, ...)
        for k, v in x.items():
            row[str(k)] = float(v)

        if y_history is not None:
            y = y_history[idx]
            for k, v in y.items():
                # Si hay colisión de nombres, la clave de y sobrescribirá la de x.
                # Esto es aceptable mientras las claves del modelo sean disjuntas.
                row[str(k)] = float(v)

        rows.append(row)

    return rows


def export_simulation_csv(
    times: Sequence[float],
    x_history: Sequence[Mapping[str, float]],
    y_history: Sequence[Mapping[str, float]] | None,
    path: str,
    config: ExportConfig | None = None,
) -> None:
    """
    Exporta resultados de simulación (times, x_history, y_history) a CSV.

    Esta función actúa como integración de alto nivel para la API de simulación.
    """
    rows = build_timeseries_rows(times, x_history, y_history)
    export_csv(rows, path, config=config)


def export_simulation_parquet(
    times: Sequence[float],
    x_history: Sequence[Mapping[str, float]],
    y_history: Sequence[Mapping[str, float]] | None,
    path: str,
    config: ExportConfig | None = None,
    *,
    engine: str | None = None,
) -> None:
    """
    Exporta resultados de simulación (times, x_history, y_history) a Parquet.

    Esta función actúa como integración de alto nivel para la API de simulación.
    """
    rows = build_timeseries_rows(times, x_history, y_history)
    export_parquet(rows, path, config=config, engine=engine)
