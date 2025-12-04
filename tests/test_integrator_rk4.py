import math

from vscsim.solver.integrator_rk import RK1Integrator, RK2Integrator, RK4Integrator


def _rhs_linear(state, context):
    """
    RHS simple dx/dt = a * x para probar orden de precisión.

    Es un sistema puramente matemático, usado solo para verificar
    que RK4 mejora (o al menos no empeora) el error respecto a RK2
    y RK1 en un caso sencillo.
    """
    a = context.get("a", -5.0)
    return {"x": a * state["x"]}


def test_rk4_improves_over_rk2_and_rk1_for_linear_system():
    """
    Para el sistema dx/dt = a x, la solución exacta es:
        x(t + dt) = x(t) * exp(a * dt)

    Verificamos que, para un paso dt moderado, el error absoluto de RK4
    frente a la solución exacta es menor o igual que el de RK2 y RK1.
    """
    rk1 = RK1Integrator()
    rk2 = RK2Integrator()
    rk4 = RK4Integrator()

    a = -5.0
    dt = 0.1
    x0 = 1.0

    state0 = {"x": x0}
    context = {"a": a}

    x_exact = x0 * math.exp(a * dt)

    x_rk1 = rk1.step(
        f=_rhs_linear,
        state=state0,
        dt=dt,
        context=context,
    )["x"]

    x_rk2 = rk2.step(
        f=_rhs_linear,
        state=state0,
        dt=dt,
        context=context,
    )["x"]

    x_rk4 = rk4.step(
        f=_rhs_linear,
        state=state0,
        dt=dt,
        context=context,
    )["x"]

    err_rk1 = abs(x_rk1 - x_exact)
    err_rk2 = abs(x_rk2 - x_exact)
    err_rk4 = abs(x_rk4 - x_exact)

    # RK4 debe ser al menos tan preciso como RK2 y RK1 en este caso.
    assert err_rk4 <= err_rk2 + 1e-15
    assert err_rk4 <= err_rk1 + 1e-15
