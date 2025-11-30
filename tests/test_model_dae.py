# tests/test_model_dae.py
"""
Pruebas sobre f_rhs y g_residual del modelo RMS.
"""

import math

from vscsim.model.dae import f_rhs, g_residual


def test_f_rhs_simple_case():
    x = {"id": 1.0, "iq": 0.0, "Vdc": 2.0}
    y = {"Idc": 3.0, "P_ac": 0.0, "Q_ac": 0.0}
    params = {"L": 1.0, "R": 0.0, "Cdc": 1.0, "omega": 0.0}
    inputs = {"v_conv_d": 1.0, "v_conv_q": 0.0, "v_pcc_d": 0.0, "v_pcc_q": 0.0}

    f = f_rhs(x, y, params, inputs)

    assert f["id"] == 1.0
    assert f["iq"] == 0.0
    assert f["Vdc"] == 3.0

    print("[SUMMARY] test_f_rhs_simple_case: "
          f"id_dot={f['id']}, iq_dot={f['iq']}, Vdc_dot={f['Vdc']}")


def test_g_residual_power_consistency():
    # Punto consistente: P_ac y Q_ac calculados exactamente con las fórmulas
    x = {"id": 1.0, "iq": -0.5, "Vdc": 2.0}
    params = {"L": 0.1, "R": 0.01, "Cdc": 0.01, "omega": 2 * math.pi * 50.0}
    inputs = {"v_pcc_d": 1.0, "v_pcc_q": 0.5}

    v_pcc_d = inputs["v_pcc_d"]
    v_pcc_q = inputs["v_pcc_q"]
    id_ = x["id"]
    iq_ = x["iq"]

    P_calc = 1.5 * (v_pcc_d * id_ + v_pcc_q * iq_)
    Q_calc = 1.5 * (v_pcc_q * id_ - v_pcc_d * iq_)
    Idc_calc = P_calc / x["Vdc"]

    y = {"Idc": Idc_calc, "P_ac": P_calc, "Q_ac": Q_calc}

    g = g_residual(x, y, params, inputs)

    assert abs(g["P_ac"]) < 1e-9
    assert abs(g["Q_ac"]) < 1e-9
    assert abs(g["Idc"]) < 1e-9

    print("[SUMMARY] test_g_residual_power_consistency: "
          f"g_Idc={g['Idc']}, g_P={g['P_ac']}, g_Q={g['Q_ac']}")
