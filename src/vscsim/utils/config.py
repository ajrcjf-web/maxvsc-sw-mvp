# src/vscsim/utils/config.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExportConfig:
    """
    Configuración mínima para funciones de exportación.

    overwrite:
        Si False (por defecto), lanzar FileExistsError si el fichero ya existe.
        Si True, se sobrescribe.
    """
    overwrite: bool = False
