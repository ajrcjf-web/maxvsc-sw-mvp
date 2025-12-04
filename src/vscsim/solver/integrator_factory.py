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

IntegratorName = Literal["euler", "rk1", "rk2", "rk4"]


def get_integrator(
    name: IntegratorName,
    config: Mapping[str, Any] | None = None,
) -> BaseIntegrator:
    """
    Devuelve una instancia de integrador acorde al nombre solicitado.

    Parameters
    ----------
    name : {"euler", "rk1", "rk2", "rk4"}
        Nombre del integrador a utilizar. El alias "euler" apunta a RK1.
    config : Mapping[str, Any], optional
        Configuración adicional específica del integrador (reservado para uso futuro).

    Returns
    -------
    BaseIntegrator
        Instancia del integrador seleccionado.
    """
    if name in ("euler", "rk1"):
        return RK1Integrator()
    if name == "rk2":
        return RK2Integrator()
    if name == "rk4":
        return RK4Integrator()

    raise ValueError(f"Integrador no soportado: {name!r}")
