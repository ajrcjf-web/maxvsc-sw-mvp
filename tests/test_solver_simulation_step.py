# tests/test_solver_simulation_step.py
"""
Pruebas de la secuencia 5.2 vía solver.simulation.run_step.
"""

from vscsim.solver.simulation import run_step


def test_run_step_basic_pq_zero_power():
    # Escenario sencillo: potencias de referencia cero, estado inicial en cero.
    params = {
        "L": 0.1,
        "R": 0.01,
        "Cdc": 0.01,
        "omega": 1.0,
        "V_max": 1.0,
        "Kp_id": 0.0,
        "Kp_iq": 0.0,
    }

    scenario = {
        "control_mode": "PQ",
        "P_ref": 0.0,
        "Q_ref": 0.0,
        "v_pcc_d": 1.0,
        "v_pcc_q": 0.0,
    }

    x = {"id": 0.0, "iq": 0.0, "Vdc": 1.0}
    y = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}

    t = 0.0
    dt = 0.01

    x_next, y_next = run_step(t, dt, x, y, scenario, params)

    # Verificar que las claves se mantienen y no hay errores
    for key in x.keys():
        assert key in x_next
    for key in y.keys():
        assert key in y_next

    print("[SUMMARY] test_run_step_basic_pq_zero_power: "
          f"x_next={x_next}, y_next={y_next}")
