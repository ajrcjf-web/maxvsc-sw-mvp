# tests/test_vsc_control.py
"""
Pruebas de los módulos de control y saturación del VSC.
"""

# import math

from vscsim.vsc.control_external import compute_current_references
from vscsim.vsc.control_inner import compute_converter_voltage_references
from vscsim.vsc.saturation import apply_voltage_saturation


def test_control_external_pq_inverts_power_equations():
    scenario = {
        "control_mode": "PQ",
        "P_ref": 1.0,
        "Q_ref": 0.5,
        "v_pcc_d": 1.0,
        "v_pcc_q": 0.5,
    }
    x = {"id": 0.0, "iq": 0.0, "Vdc": 1.0}
    y = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}
    params = {}

    refs = compute_current_references(0.0, x, y, scenario, params)
    id_ref = refs["id_ref"]
    iq_ref = refs["iq_ref"]

    v_d = scenario["v_pcc_d"]
    v_q = scenario["v_pcc_q"]
    P_calc = 1.5 * (v_d * id_ref + v_q * iq_ref)
    Q_calc = 1.5 * (v_q * id_ref - v_d * iq_ref)

    assert abs(P_calc - scenario["P_ref"]) < 1e-9
    assert abs(Q_calc - scenario["Q_ref"]) < 1e-9

    print("[SUMMARY] test_control_external_pq_inverts_power_equations: "
          f"id_ref={id_ref}, iq_ref={iq_ref}, P_calc={P_calc}, Q_calc={Q_calc}")


def test_control_external_vdcq_pass_through():
    scenario = {
        "control_mode": "VdcQ",
        "id_ref": 1.23,
        "iq_ref": -0.5,
        "v_pcc_d": 1.0,
        "v_pcc_q": 0.0,
    }
    x = {"id": 0.0, "iq": 0.0, "Vdc": 1.0}
    y = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}
    params = {}

    refs = compute_current_references(0.0, x, y, scenario, params)

    assert refs["id_ref"] == scenario["id_ref"]
    assert refs["iq_ref"] == scenario["iq_ref"]

    print("[SUMMARY] test_control_external_vdcq_pass_through: "
          f"id_ref={refs['id_ref']}, iq_ref={refs['iq_ref']}")


def test_control_inner_proportional():
    x = {"id": 1.0, "iq": -1.0, "Vdc": 1.0}
    params = {"Kp_id": 2.0, "Kp_iq": 3.0}
    id_ref = 2.0
    iq_ref = 1.0

    voltages_ref, _state = compute_converter_voltage_references(
        id_ref=id_ref,
        iq_ref=iq_ref,
        x=x,
        params=params,
        controller_state=None,
    )

    v_d = voltages_ref["v_conv_d_ref"]
    v_q = voltages_ref["v_conv_q_ref"]

    assert v_d == 2.0 * (2.0 - 1.0)
    assert v_q == 3.0 * (1.0 - (-1.0))

    print("[SUMMARY] test_control_inner_proportional: "
          f"v_conv_d_ref={v_d}, v_conv_q_ref={v_q}")


def test_saturation_limits_magnitude():
    v_conv_d_ref = 3.0
    v_conv_q_ref = 4.0
    v_max = 5.0

    # Vector (3,4) ya tiene módulo 5, no debería cambiar
    v_d, v_q = apply_voltage_saturation(v_conv_d_ref, v_conv_q_ref, v_max)

    assert v_d == v_conv_d_ref
    assert v_q == v_conv_q_ref

    # Ahora un vector con módulo mayor que V_max
    v_conv_d_ref2 = 10.0
    v_conv_q_ref2 = 0.0

    v_d2, v_q2 = apply_voltage_saturation(v_conv_d_ref2, v_conv_q_ref2, v_max)
    mag_sq = v_d2 * v_d2 + v_q2 * v_q2

    assert abs(mag_sq - v_max * v_max) < 1e-9

    print("[SUMMARY] test_saturation_limits_magnitude: "
          f"v_d2={v_d2}, v_q2={v_q2}, |v|^2={mag_sq}")
