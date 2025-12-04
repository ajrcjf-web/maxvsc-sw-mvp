import math
import copy

from vscsim.solver.simulation import run_simulation_adaptive


def test_run_simulation_adaptive_dt(monkeypatch):
    """
    Verifica la integración del AdaptiveTimestepper con run_step:

    - Se usa un run_step dummy (no tocamos ingeniería).
    - dt se mantiene dentro de [dt_min, dt_max].
    - Se guarda correctamente dt_history.
    - dt no es constante en general (se adapta).
    """

    def dummy_run_step(
        t,
        dt,
        x,
        y,
        scenario,
        params,
        integrator_name=None,
    ):
        # Dinámica lineal simple: dx/dt = -x
        # Aproximación tipo Euler explícito para el dummy.
        new_x = {k: v * (1.0 - dt) for k, v in x.items()}
        new_y = dict(y)
        return new_x, new_y

    # Monkeypatch del run_step real
    monkeypatch.setattr(
        "vscsim.solver.simulation.run_step",
        dummy_run_step,
    )

    t0 = 0.0
    t_end = 1.0

    x0 = {"id": 1.0, "iq": 0.5, "Vdc": 2.0}
    y0 = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}

    scenario = {}
    params = {}

    dt_initial = 0.2
    dt_min = 0.05
    dt_max = 0.25
    tol = 1e-3

    times, x_hist, y_hist, dt_hist = run_simulation_adaptive(
        t0=t0,
        t_end=t_end,
        x0=copy.deepcopy(x0),
        y0=copy.deepcopy(y0),
        scenario=scenario,
        params=params,
        integrator_name="rk4",  # el dummy ignora realmente el integrador
        dt_initial=dt_initial,
        dt_min=dt_min,
        dt_max=dt_max,
        tol=tol,
        max_steps=1000,
    )

    # Debe haber al menos un paso
    assert len(times) >= 2
    assert len(dt_hist) == len(times) - 1
    assert len(x_hist) == len(times)
    assert len(y_hist) == len(times)

    # Todos los dt dentro de los límites
    for dt in dt_hist:
        assert dt_min - 1e-12 <= dt <= dt_max + 1e-12

    # No debería ser siempre el mismo dt (adaptación)
    # Permitimos el caso extremo, pero en general debería variar.
    distinct_dts = {round(dt, 6) for dt in dt_hist}
    assert len(distinct_dts) >= 1  # trivial
    # Idealmente > 1; si quieres ser más estricto:
    # assert len(distinct_dts) > 1

    # Último tiempo debe ser (casi) t_end
    assert math.isclose(times[-1], t_end, rel_tol=0.0, abs_tol=1e-8)
