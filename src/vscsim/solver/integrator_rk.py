"""
vscsim.solver.integrator_rk

Módulo de integradores de Runge-Kutta (RK1/RK2/RK4) para la parte dinámica (x).
Forman parte del framework numérico, no de la ingeniería (modelo/ecuaciones).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Callable, Any, Mapping


class RHSFunction(Protocol):
    """
    Interfaz genérica para la función de derivadas f.

    La firma concreta se alineará con la implementación existente de f(x, y)
    y con la secuencia del solver en simulation.py.
    """

    def __call__(self, state: Mapping[str, float], context: Mapping[str, Any]) -> Mapping[str, float]:
        """
        Calcula x_dot = f(x, y, ...).

        Parameters
        ----------
        state : Mapping[str, float]
            Estados dinámicos actuales x.
        context : Mapping[str, Any]
            Información adicional necesaria (por ejemplo y, parámetros, etc.).

        Returns
        -------
        Mapping[str, float]
            Derivadas x_dot.
        """
        ...


class BaseIntegrator(ABC):
    """
    Clase base abstracta para integradores de estados dinámicos x.

    El integrador se invoca desde la secuencia del solver (simulation.py),
    en el paso de integración de x, respetando la ETU v1.3.
    """

    @abstractmethod
    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        """
        Realiza un paso de integración de tamaño dt.

        La implementación concreta (RK1/RK2/RK4) se definirá posteriormente.

        Parameters
        ----------
        f : RHSFunction
            Función de derivadas x_dot = f(x, y, ...).
        state : Mapping[str, float]
            Estados dinámicos actuales x.
        dt : float
            Paso de integración.
        context : Mapping[str, Any]
            Información adicional necesaria (por ejemplo y, parámetros, etc.).

        Returns
        -------
        Mapping[str, float]
            Nuevos estados x en t + dt.
        """
        raise NotImplementedError


@dataclass
class RK1Integrator(BaseIntegrator):
    """
    Integrador RK1 (equivalente a Euler explícito) dentro del esquema RK.

    Esta implementación reproduce el esquema:
        x_new = x + dt * f(x, ...)

    La equivalencia con el integrador Euler existente debe verificarse
    mediante tests que comparen ambos resultados para el mismo f, x y dt.
    """

    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        """
        Realiza un paso Euler explícito sobre los estados x.

        Parameters
        ----------
        f : RHSFunction
            Función de derivadas x_dot = f(x, y, ...).
        state : Mapping[str, float]
            Estados dinámicos actuales x.
        dt : float
            Paso de integración.
        context : Mapping[str, Any]
            Información adicional necesaria (por ejemplo y, parámetros, etc.).

        Returns
        -------
        Mapping[str, float]
            Nuevos estados x en t + dt, con las mismas claves que `state`.
        """
        # Derivadas en el estado actual
        x_dot = f(state, context)

        # Paso Euler explícito: x_new = x + dt * x_dot
        # Se asume que x_dot contiene las mismas claves que `state`.
        new_state: dict[str, float] = {}

        for key, value in state.items():
            deriv = x_dot.get(key)
            if deriv is None:
                # Si faltara alguna clave, es un error de coherencia del modelo/framework.
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en x_dot")
            new_state[key] = value + dt * deriv

        return new_state


@dataclass
class RK2Integrator(BaseIntegrator):
    """
    Integrador Runge-Kutta de orden 2 (RK2).

    La implementación numérica se añadirá en una fase posterior.
    """

    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        # Implementación pendiente (Track A1.1.2 / A1.1.5)
        raise NotImplementedError


@dataclass
class RK4Integrator(BaseIntegrator):
    """
    Integrador Runge-Kutta de orden 4 (RK4).

    La implementación numérica se añadirá en una fase posterior.
    """

    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        # Implementación pendiente (Track A1.1.3 / A1.1.5)
        raise NotImplementedError
