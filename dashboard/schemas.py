# dashboard/schemas.py
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


class RunInfo(BaseModel):
    """Información mínima de un 'run' (un fichero CSV/parquet)."""

    id: str     # identificador lógico (p.ej. "advanced/step_pref_seg1")
    name: str   # nombre amigable (normalmente el nombre del fichero)
    path: str   # ruta relativa al DATA_DIR


class SignalList(BaseModel):
    """Lista de señales disponibles en un run."""

    time_column: str
    signals: List[str]


class TimeSeriesResponse(BaseModel):
    """Serie temporal de varias señales."""

    time: List[float]
    signals: Dict[str, List[float]]
