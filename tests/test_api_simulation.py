# tests/test_api_simulation.py
"""
Pruebas de la API de simulación de alto nivel.
"""

import math

from vscsim.api.simulation import run_simulation


def test_run_simulation_basic_pq_zero_power():
    params_config = {
        "L": 0.1,
        "R": 0.01,
        "Cdc": 0.01,
        "omega": 2 * math.pi * 50.0,
        "V_max": 1.0,
        "Kp_id": 0.0,
        "Kp_iq": 0.0,
    }

    scenario_config = {
        "control_mode": "PQ",
        "P_ref": 0.0,
        "Q_ref": 0.0,
        "v_pcc_d": 1.0,
        "v_pcc_q": 0.0,
        "initial_conditions": {
            "id": 0.0,
            "iq": 0.0,
            "Vdc": 1.0,
        },
    }

    t_end = 0.05
    dt = 0.01

    results = run_simulation(params_config, scenario_config, t_end, dt)

    time = results["time"]
    x_hist = results["x"]
    y_hist = results["y"]

    assert len(time) == len(x_hist["id"]) == len(y_hist["Idc"])

    t_final = time[-1]
    Vdc_final = x_hist["Vdc"][-1]

    print("[SUMMARY] test_run_simulation_basic_pq_zero_power: "
          f"steps={len(time)-1}, t_final={t_final}, Vdc_final={Vdc_final}")
