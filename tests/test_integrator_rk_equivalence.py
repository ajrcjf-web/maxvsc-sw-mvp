import copy

import pytest

from vscsim.solver.integrator import step_forward
from vscsim.solver.integrator_rk import RK1Integrator


def _dummy_rhs(state, context):
    """
    RHS de prueba para comparar integradores.

    No representa el modelo físico real; solo sirve para verificar
    que RK1 aplica exactamente el mismo esquema numérico que el
    integrador Euler explícito (step_forward).
    """
    # Dinámica lineal simple sobre las tres variables de estado típicas: id, iq, Vdc.
    return {
        "id": 0.1 * state["id"] - 0.05 * state["iq"],
        "iq": -0.02 * state["id"] + 0.03 * state["iq"],
        "Vdc": 0.01 * state["Vdc"],
    }


def test_rk1_matches_euler_single_step():
    """
    Verifica que RK1Integrator es numéricamente equivalente al integrador Euler
    existente (step_forward) para un único paso de integración, usando la misma
    función de derivadas, el mismo estado inicial y el mismo dt.

    Criterio: para cada variable de estado, la diferencia debe ser ≈ 0
    dentro de una tolerancia numérica muy pequeña.
    """
    rk1 = RK1Integrator()

    # Estado inicial de prueba (coherente con claves típicas del modelo RMS).
    state0 = {
        "id": 100.0,
        "iq": -50.0,
        "Vdc": 400.0,
    }
    context = {}

    dt = 1e-3

    # Copias independientes por seguridad (por si algún integrador modificara in-place).
    state_for_euler = copy.deepcopy(state0)
    state_for_rk1 = copy.deepcopy(state0)

    # Derivadas en el estado inicial, comunes a ambos integradores.
    x_dot = _dummy_rhs(state0, context)

    # Integrador Euler legacy (ENG-1.0): step_forward(x, x_dot, dt)
    x_euler = step_forward(
        x=state_for_euler,
        x_dot=x_dot,
        dt=dt,
    )

    # Integrador RK1 (nuevo framework): calcula internamente x_dot = f(x, ...)
    x_rk1 = rk1.step(
        f=_dummy_rhs,
        state=state_for_rk1,
        dt=dt,
        context=context,
    )

    # Comprobamos que las claves son las mismas
    assert set(x_euler.keys()) == set(x_rk1.keys()) == set(state0.keys())

    # Comparación numérica variable a variable
    for key in state0.keys():
        assert x_euler[key] == pytest.approx(x_rk1[key], rel=0.0, abs=1e-12)
