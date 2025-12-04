# dashboard/config.py
from __future__ import annotations

import os
from pathlib import Path

# Directorio base de datos de resultados.
# Por defecto: ./outputs
# Se puede sobreescribir con la variable:
#   MAXVSC_DASHBOARD_DATA_DIR
DATA_DIR = Path(
    os.environ.get("MAXVSC_DASHBOARD_DATA_DIR", "outputs")
).resolve()


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
