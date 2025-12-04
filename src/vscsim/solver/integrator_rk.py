"""
vscsim.solver.integrator_rk

Módulo de integradores de Runge-Kutta (RK1/RK2/RK4) para la parte dinámica (x).
Forman parte del framework numérico, no de la ingeniería (modelo/ecuaciones).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, Any, Mapping

from vscsim.utils.logger import global_log


class RHSFunction(Protocol):
    """
    Interfaz genérica para la función de derivadas f.

    La firma concreta se alinea con la implementación existente de f(x, y)
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


def _dict_norm(d: Mapping[str, float]) -> float:
    """Norma infinito de un dict numérico (max |v|)."""
    if not d:
        return 0.0
    return max(abs(float(v)) for v in d.values())


@dataclass
class RK1Integrator(BaseIntegrator):
    """
    Integrador RK1 (equivalente a Euler explícito) dentro del esquema RK.

    Esquema:
        x_new = x + dt * f(x, ...)
    """

    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        # k1 = f(x_n, ...)
        k1 = f(state, context)

        # Logging opcional (no afecta a la integración)
        global_log(
            "debug",
            "rk_step",
            method="rk1",
            dt=dt,
            k1_norm=_dict_norm(k1),
        )

        # x_{n+1} = x_n + dt * k1
        new_state: dict[str, float] = {}
        for key, value in state.items():
            deriv = k1.get(key)
            if deriv is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k1")
            new_state[key] = value + dt * deriv

        return new_state


@dataclass
class RK2Integrator(BaseIntegrator):
    """
    Integrador Runge-Kutta de orden 2 (RK2, esquema del punto medio).

    Esquema:

        k1 = f(x_n, ...)
        x_mid = x_n + (dt/2) * k1
        k2 = f(x_mid, ...)
        x_{n+1} = x_n + dt * k2
    """

    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        # k1 = f(x_n, ...)
        k1 = f(state, context)

        # x_mid = x_n + (dt/2) * k1
        mid_state: dict[str, float] = {}
        for key, value in state.items():
            deriv = k1.get(key)
            if deriv is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k1")
            mid_state[key] = value + 0.5 * dt * deriv

        # k2 = f(x_mid, ...)
        k2 = f(mid_state, context)

        # Logging opcional
        global_log(
            "debug",
            "rk_step",
            method="rk2",
            dt=dt,
            k1_norm=_dict_norm(k1),
            k2_norm=_dict_norm(k2),
        )

        # x_{n+1} = x_n + dt * k2
        new_state: dict[str, float] = {}
        for key, value in state.items():
            deriv = k2.get(key)
            if deriv is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k2")
            new_state[key] = value + dt * deriv

        return new_state


@dataclass
class RK4Integrator(BaseIntegrator):
    """
    Integrador Runge-Kutta de orden 4 (RK4).

    Esquema clásico:

        k1 = f(x_n, ...)
        x2 = x_n + (dt/2) * k1
        k2 = f(x2, ...)
        x3 = x_n + (dt/2) * k2
        k3 = f(x3, ...)
        x4 = x_n + dt * k3
        k4 = f(x4, ...)

        x_{n+1} = x_n + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
    """

    def step(
        self,
        f: RHSFunction,
        state: Mapping[str, float],
        dt: float,
        context: Mapping[str, Any],
    ) -> Mapping[str, float]:
        # k1 = f(x_n, ...)
        k1 = f(state, context)

        # x2 = x_n + (dt/2) * k1
        state_k2: dict[str, float] = {}
        for key, value in state.items():
            deriv = k1.get(key)
            if deriv is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k1")
            state_k2[key] = value + 0.5 * dt * deriv

        # k2 = f(x2, ...)
        k2 = f(state_k2, context)

        # x3 = x_n + (dt/2) * k2
        state_k3: dict[str, float] = {}
        for key, value in state.items():
            deriv = k2.get(key)
            if deriv is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k2")
            state_k3[key] = value + 0.5 * dt * deriv

        # k3 = f(x3, ...)
        k3 = f(state_k3, context)

        # x4 = x_n + dt * k3
        state_k4: dict[str, float] = {}
        for key, value in state.items():
            deriv = k3.get(key)
            if deriv is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k3")
            state_k4[key] = value + dt * deriv

        # k4 = f(x4, ...)
        k4 = f(state_k4, context)

        # Logging opcional
        global_log(
            "debug",
            "rk_step",
            method="rk4",
            dt=dt,
            k1_norm=_dict_norm(k1),
            k2_norm=_dict_norm(k2),
            k3_norm=_dict_norm(k3),
            k4_norm=_dict_norm(k4),
        )

        # x_{n+1} = x_n + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        new_state: dict[str, float] = {}
        for key, value in state.items():
            d1 = k1.get(key)
            d2 = k2.get(key)
            d3 = k3.get(key)
            d4 = k4.get(key)
            if d1 is None or d2 is None or d3 is None or d4 is None:
                raise KeyError(f"Falta derivada para la variable de estado {key!r} en k1/k2/k3/k4")
            new_state[key] = value + (dt / 6.0) * (d1 + 2.0 * d2 + 2.0 * d3 + d4)

        return new_state
