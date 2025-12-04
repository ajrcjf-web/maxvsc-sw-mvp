import copy

from vscsim.solver.simulation import run_step


def test_run_step_integrator_selection(monkeypatch):
    """
    Verifica que:

    - integrator_name=None  → usa el camino legacy (step_forward).
    - integrator_name="euler" y "rk1" → dan exactamente el mismo resultado
      que el camino legacy (porque ambos usan Euler explícito).
    - integrator_name="rk2" y "rk4" → funcionan y devuelven estados con las
      mismas claves, sin romper la secuencia 5.2.

    Se hace con un modelo DAE "dummy" mediante monkeypatch, sin tocar
    la ingeniería real.
    """

    # ------------------------
    # Dummies para la cadena de control y modelo
    # ------------------------

    def dummy_compute_current_references(t, x, y, scenario, params):
        # No usamos realmente las referencias en este test;
        # solo devolvemos algo consistente.
        return {"id_ref": 0.0, "iq_ref": 0.0}

    def dummy_compute_converter_voltage_references(id_ref, iq_ref, x, params, controller_state=None):
        # Devolvemos tensiones de referencia constantes y sin estado interno.
        return {"v_conv_d_ref": 1.0, "v_conv_q_ref": 0.0}, controller_state

    def dummy_apply_voltage_saturation(v_conv_d_ref, v_conv_q_ref, v_max):
        # Identidad (sin saturar) para el test.
        return v_conv_d_ref, v_conv_q_ref

    def dummy_newton_raphson(x, y0, residual, jacobian, params, inputs):
        # Devolvemos y tal cual, simulando convergencia inmediata.
        return dict(y0), {"converged": True, "iterations": 0}

    def dummy_f_rhs(x, y, params, inputs):
        # RHS simple: dx/dt = a * x (mismo 'a' para todas las variables).
        a = -1.0
        return {k: a * v for k, v in x.items()}

    # ------------------------
    # Monkeypatch sobre el módulo simulation
    # ------------------------

    monkeypatch.setattr(
        "vscsim.solver.simulation.compute_current_references",
        dummy_compute_current_references,
    )
    monkeypatch.setattr(
        "vscsim.solver.simulation.compute_converter_voltage_references",
        dummy_compute_converter_voltage_references,
    )
    monkeypatch.setattr(
        "vscsim.solver.simulation.apply_voltage_saturation",
        dummy_apply_voltage_saturation,
    )
    monkeypatch.setattr(
        "vscsim.solver.simulation.newton_raphson",
        dummy_newton_raphson,
    )
    monkeypatch.setattr(
        "vscsim.solver.simulation.f_rhs",
        dummy_f_rhs,
    )

    # ------------------------
    # Datos iniciales sencillos
    # ------------------------

    x0 = {"id": 1.0, "iq": -0.5, "Vdc": 2.0}
    y0 = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}

    scenario = {}
    params = {}
    t = 0.0
    dt = 0.1

    # Copias por seguridad
    x0_legacy = copy.deepcopy(x0)
    y0_legacy = copy.deepcopy(y0)

    # ------------------------
    # Camino legacy (None) vs "euler" vs "rk1"
    # ------------------------

    x_legacy, y_legacy = run_step(
        t=t,
        dt=dt,
        x=x0_legacy,
        y=y0_legacy,
        scenario=scenario,
        params=params,
        integrator_name=None,  # step_forward (ENG-1.0)
    )

    x_euler, y_euler = run_step(
        t=t,
        dt=dt,
        x=copy.deepcopy(x0),
        y=copy.deepcopy(y0),
        scenario=scenario,
        params=params,
        integrator_name="euler",  # RK1 (Euler explícito)
    )

    x_rk1, y_rk1 = run_step(
        t=t,
        dt=dt,
        x=copy.deepcopy(x0),
        y=copy.deepcopy(y0),
        scenario=scenario,
        params=params,
        integrator_name="rk1",  # alias de "euler"
    )

    # Deben ser exactamente iguales en este escenario controlado
    assert x_legacy == x_euler == x_rk1
    assert y_legacy == y_euler == y_rk1

    # ------------------------
    # Camino RK2 y RK4: solo comprobamos que funcionan y respetan claves
    # ------------------------

    x_rk2, y_rk2 = run_step(
        t=t,
        dt=dt,
        x=copy.deepcopy(x0),
        y=copy.deepcopy(y0),
        scenario=scenario,
        params=params,
        integrator_name="rk2",
    )

    x_rk4, y_rk4 = run_step(
        t=t,
        dt=dt,
        x=copy.deepcopy(x0),
        y=copy.deepcopy(y0),
        scenario=scenario,
        params=params,
        integrator_name="rk4",
    )

    # Mismas claves de estado y algebraicas
    assert set(x_rk2.keys()) == set(x0.keys())
    assert set(x_rk4.keys()) == set(x0.keys())
    assert set(y_rk2.keys()) == set(y0.keys())
    assert set(y_rk4.keys()) == set(y0.keys())
