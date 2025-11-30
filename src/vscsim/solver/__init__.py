"""
Paquete de solver del simulador RMS VSC-HVDC.

Incluye:
- Newton–Raphson para las algebraicas.
- Integrador de los estados.
- Secuencia de simulación (paso run_step).

Este archivo solo reexporta funciones ya definidas; no introduce
ingeniería nueva.
"""

from .nr import newton_raphson
from .integrator import step_forward
from .simulation import run_step

__all__ = [
    "newton_raphson",
    "step_forward",
    "run_step",
]
