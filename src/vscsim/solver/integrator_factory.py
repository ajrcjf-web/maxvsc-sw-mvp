"""
vscsim.solver.integrator_factory

Fábrica de integradores para seleccionar entre RK1/RK2/RK4
u otros integradores disponibles en el framework numérico.

No modifica la ingeniería ni la secuencia del solver definida en la ETU v1.3:
solo elige qué esquema de integración usar en el paso de integración de x.
"""

from __future__ import annotations

from typing import Literal, Mapping, Any

from .integrator_rk import BaseIntegrator, RK1Integrator, RK2Integrator, RK4Integrator

IntegratorName = Literal["rk1", "rk2", "rk4", "euler"]


def get_integrator(
    name: IntegratorName,
    config: Mapping[str, Any] | None = None,
) -> BaseIntegrator:
    """
    Devuelve una instancia de integrador acorde al nombre solicitado.

    Parameters
    ----------
    name : {"rk1", "rk2", "rk4", "euler"}
        Nombre del integrador a utilizar. El alias "euler" apunta a RK1.
    config : Mapping[str, Any], optional
        Configuración adicional específica del integrador (reservado para uso futuro).

    Returns
    -------
    BaseIntegrator
        Instancia del integrador seleccionado.

    Notes
    -----
    La integración con simulation.py y step_forward se hará en A1.1.4/A1.1.5.
    """
    # Por ahora solo es un esqueleto; no se aplica ninguna lógica adicional.
    if name in ("rk1", "euler"):
        return RK1Integrator()
    if name == "rk2":
        return RK2Integrator()
    if name == "rk4":
        return RK4Integrator()

    # En versiones futuras se podría añadir validación más estricta o errores específicos.
    raise ValueError(f"Integrador no soportado: {name!r}")
