import math

from vscsim.solver.integrator_rk import RK1Integrator, RK2Integrator


def _rhs_linear(state, context):
    """
    RHS simple dx/dt = a * x para probar orden de precisión.

    Es un sistema puramente matemático, sin relación directa con el modelo RMS,
    usado solo para verificar que RK2 mejora el error respecto a RK1.
    """
    a = context.get("a", -5.0)
    return {"x": a * state["x"]}


def test_rk2_improves_over_rk1_for_linear_system():
    """
    Para el sistema dx/dt = a x, la solución exacta es:
        x(t + dt) = x(t) * exp(a * dt)

    Verificamos que, para un paso moderado dt, el error absoluto de RK2
    frente a la solución exacta es menor o igual que el de RK1 (Euler).
    """
    rk1 = RK1Integrator()
    rk2 = RK2Integrator()

    a = -5.0
    dt = 0.1
    x0 = 1.0

    state0 = {"x": x0}
    context = {"a": a}

    # Solución exacta
    x_exact = x0 * math.exp(a * dt)

    # Un paso con RK1 (Euler)
    x_rk1 = rk1.step(
        f=_rhs_linear,
        state=state0,
        dt=dt,
        context=context,
    )["x"]

    # Un paso con RK2
    x_rk2 = rk2.step(
        f=_rhs_linear,
        state=state0,
        dt=dt,
        context=context,
    )["x"]

    err_rk1 = abs(x_rk1 - x_exact)
    err_rk2 = abs(x_rk2 - x_exact)

    # RK2 debe ser al menos tan preciso como RK1 en este caso.
    assert err_rk2 <= err_rk1 + 1e-15
