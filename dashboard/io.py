from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .config import ensure_data_dir

# Soporte opcional de Parquet vía pandas
try:  # pragma: no cover - import opcional
    import pandas as pd  # type: ignore

    HAS_PANDAS = True
except Exception:  # pragma: no cover - entorno sin pandas
    pd = None  # type: ignore
    HAS_PANDAS = False


# ---------------------------------------------------------------------------
# Descubrimiento de ficheros
# ---------------------------------------------------------------------------


def iter_csv_files() -> Iterable[Path]:
    """Itera sobre todos los CSV bajo DATA_DIR (recursivo)."""
    root = ensure_data_dir()
    return root.rglob("*.csv")


def iter_parquet_files() -> Iterable[Path]:
    """Itera sobre todos los Parquet bajo DATA_DIR (recursivo)."""
    root = ensure_data_dir()
    return root.rglob("*.parquet")


def build_run_id(path: Path) -> str:
    """
    Construye un id lógico a partir del nombre del fichero (sin ruta).

    Ejemplo:
        outputs/advanced/sample_case.csv -> "sample_case"
        outputs/advanced/sample_case.parquet -> "sample_case"
    """
    return path.stem.replace(" ", "_").lower()


def list_runs() -> List[Tuple[str, Path]]:
    """
    Devuelve lista de (run_id, path_file).

    Si existen CSV y Parquet con el mismo nombre base, se mantiene el primero
    que se encuentre. Priorizamos CSV para mantener compatibilidad con tests.
    """
    runs: Dict[str, Path] = {}

    # Primero CSV
    for path in iter_csv_files():
        run_id = build_run_id(path)
        runs.setdefault(run_id, path)

    # Luego Parquet (solo si hay pandas); sin sobrescribir CSV existentes
    if HAS_PANDAS:
        for path in iter_parquet_files():
            run_id = build_run_id(path)
            runs.setdefault(run_id, path)

    return sorted(runs.items(), key=lambda t: t[0])


def find_run_file(run_id: str) -> Path:
    """
    Localiza el fichero asociado a un run_id.

    Estrategia:
    - Buscar por nombre base (stem) en CSV.
    - Si no se encuentra y hay pandas, buscar en Parquet.
    """
    # CSV
    for path in iter_csv_files():
        if build_run_id(path) == run_id:
            return path

    # Parquet
    if HAS_PANDAS:
        for path in iter_parquet_files():
            if build_run_id(path) == run_id:
                return path

    raise FileNotFoundError(f"No se encontró fichero para run_id={run_id!r}")


# Alias para mantener compatibilidad con código previo
def find_run_csv(run_id: str) -> Path:
    """
    Compat: mantiene el nombre antiguo, pero puede devolver CSV o Parquet.
    """
    return find_run_file(run_id)


# ---------------------------------------------------------------------------
# Lectura de series temporales
# ---------------------------------------------------------------------------


def load_csv_timeseries(
    path: Path,
    time_column: str = "time",
) -> Tuple[List[float], Dict[str, List[float]]]:
    """
    Carga un CSV en forma de:
        time: [t0, t1, ...]
        signals: {col: [v0, v1, ...], ...} (excluyendo time_column)

    Intenta convertir a float. Si falla, deja None.
    """
    times: List[float] = []
    signals: Dict[str, List[float]] = {}

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return times, signals

        cols = reader.fieldnames
        other_cols = [c for c in cols if c != time_column]

        for c in other_cols:
            signals[c] = []

        for row in reader:
            # tiempo
            t_raw = row.get(time_column, "")
            try:
                t_val = float(t_raw)
            except (TypeError, ValueError):
                # si no se puede convertir, saltamos la fila
                continue
            times.append(t_val)

            # resto de columnas
            for c in other_cols:
                v_raw = row.get(c, "")
                if v_raw == "" or v_raw is None:
                    signals[c].append(None)
                    continue
                try:
                    v_val = float(v_raw)
                except (TypeError, ValueError):
                    v_val = None
                signals[c].append(v_val)

    return times, signals


def load_parquet_timeseries(
    path: Path,
    time_column: str = "time",
) -> Tuple[List[float], Dict[str, List[float]]]:
    """
    Carga un Parquet en la misma estructura que load_csv_timeseries.

    Requiere pandas + motor Parquet (pyarrow normalmente).
    """
    if not HAS_PANDAS:
        raise RuntimeError(
            "La lectura de Parquet requiere pandas instalado "
            "(y un motor Parquet como pyarrow)."
        )

    df = pd.read_parquet(path)  # type: ignore[arg-type]

    if time_column not in df.columns:
        raise ValueError(f"Columna de tiempo '{time_column}' no encontrada en {path}")

    # Extraemos time
    times = df[time_column].astype(float).tolist()

    signals: Dict[str, List[float]] = {}
    for col in df.columns:
        if col == time_column:
            continue
        # Convertimos a float; NaN se mantendrá como float('nan')
        signals[col] = df[col].astype(float).tolist()

    return times, signals


def load_timeseries(
    path: Path,
    time_column: str = "time",
) -> Tuple[List[float], Dict[str, List[float]]]:
    """
    Wrapper genérico que decide CSV vs Parquet según la extensión.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv_timeseries(path, time_column=time_column)
    if suffix in {".parquet", ".pq"}:
        return load_parquet_timeseries(path, time_column=time_column)

    raise ValueError(f"Extensión de fichero no soportada: {path.name!r}")


def list_signals_from_csv(path: Path, time_column: str = "time") -> List[str]:
    """Lee solo el header de un CSV y devuelve las señales (excepto time_column)."""
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
    if not header:
        return []
    return [c for c in header if c != time_column]


def list_signals_from_parquet(path: Path, time_column: str = "time") -> List[str]:
    """Lista las columnas de un Parquet (excepto la columna de tiempo)."""
    if not HAS_PANDAS:
        raise RuntimeError(
            "La lectura de Parquet requiere pandas instalado "
            "(y un motor Parquet como pyarrow)."
        )

    df = pd.read_parquet(path, nrows=1)  # type: ignore[arg-type]
    return [c for c in df.columns if c != time_column]


def list_signals(path: Path, time_column: str = "time") -> List[str]:
    """Lista señales de un fichero CSV o Parquet."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return list_signals_from_csv(path, time_column=time_column)
    if suffix in {".parquet", ".pq"}:
        return list_signals_from_parquet(path, time_column=time_column)

    raise ValueError(f"Extensión de fichero no soportada: {path.name!r}")
