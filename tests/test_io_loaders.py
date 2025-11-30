# tests/test_io_loaders.py
"""
Pruebas de los módulos IO: parameters, scenario, initial_conditions.
"""

import pytest

from vscsim.io.parameters import load_parameters
from vscsim.io.scenario import load_scenario
from vscsim.io.initial_conditions import load_initial_conditions


def test_load_parameters_missing_raises():
    config = {
        "L": 0.1,
        # falta R
        "Cdc": 0.01,
        "omega": 1.0,
        "V_max": 1.0,
        "Kp_id": 0.0,
        "Kp_iq": 0.0,
    }

    with pytest.raises(ValueError):
        load_parameters(config)

    print("[SUMMARY] test_load_parameters_missing_raises: passed (ValueError)")


def test_load_parameters_ok():
    config = {
        "L": 0.1,
        "R": 0.01,
        "Cdc": 0.01,
        "omega": 1.0,
        "V_max": 1.0,
        "Kp_id": 0.0,
        "Kp_iq": 0.0,
    }

    params = load_parameters(config)

    for key in config.keys():
        assert key in params

    print("[SUMMARY] test_load_parameters_ok: params keys=", list(params.keys()))


def test_load_scenario_pq_and_vdcq():
    # PQ
    pq_cfg = {
        "control_mode": "PQ",
        "P_ref": 1.0,
        "Q_ref": 0.5,
        "v_pcc_d": 1.0,
        "v_pcc_q": 0.0,
    }
    scenario_pq = load_scenario(pq_cfg)
    assert scenario_pq["control_mode"] == "PQ"
    assert "P_ref" in scenario_pq and "Q_ref" in scenario_pq

    # VdcQ
    vdcq_cfg = {
        "control_mode": "VdcQ",
        "id_ref": 1.0,
        "iq_ref": -0.5,
        "v_pcc_d": 1.0,
        "v_pcc_q": 0.0,
    }
    scenario_vdcq = load_scenario(vdcq_cfg)
    assert scenario_vdcq["control_mode"] == "VdcQ"
    assert "id_ref" in scenario_vdcq and "iq_ref" in scenario_vdcq

    print("[SUMMARY] test_load_scenario_pq_and_vdcq: "
          f"PQ_keys={list(scenario_pq.keys())}, "
          f"VdcQ_keys={list(scenario_vdcq.keys())}")


def test_load_initial_conditions_defaults():
    cfg = {}  # sin nada

    ic = load_initial_conditions(cfg)

    x0 = ic["x0"]
    y0 = ic["y0"]

    # Todos los estados y algebraicas deben existir y ser 0.0
    for key in ("id", "iq", "Vdc"):
        assert key in x0
        assert x0[key] == 0.0

    for key in ("Idc", "P_ac", "Q_ac"):
        assert key in y0
        assert y0[key] == 0.0

    print("[SUMMARY] test_load_initial_conditions_defaults: "
          f"x0={x0}, y0={y0}")
