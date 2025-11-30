# tests/conftest.py
"""
Configuración común para los tests.

Añade la carpeta 'src' al sys.path para que el paquete 'vscsim'
sea importable como:

    import vscsim...

Esto no afecta al modelo ni a la ingeniería, solo al entorno de tests.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # raíz del repo (maxvsc-sw)
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
