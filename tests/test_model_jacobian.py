# tests/test_model_jacobian.py
"""
Pruebas del Jacobiano del modelo RMS.

Se comprueba la coherencia de df/dx y dg/dy con las ecuaciones
analíticas, sin introducir ingeniería nueva.
"""

import math

from vscsim.model.dae import f_rhs, g_residual
from vscsim.model.jacobian import df_dx, dg_dx, dg_dy


def test_df_dx_matches_analytical():
    x = {"id": 0.5, "iq": -0.3, "Vdc": 2.0}
    y = {"Idc": 1.0, "P_ac": 0.0, "Q_ac": 0.0}
    params = {"L": 0.1, "R": 0.01, "Cdc": 0.01, "omega": 100.0}
    inputs = {"v_conv_d": 0.0, "v_conv_q": 0.0, "v_pcc_d": 0.0, "v_pcc_q": 0.0}

    J = df_dx(x, y, params, inputs)

    L = params["L"]
    R = params["R"]
    omega = params["omega"]

    expected = [
        [-R / L, omega, 0.0],
        [-omega, -R / L, 0.0],
        [0.0, 0.0, 0.0],
    ]

    for i in range(3):
        for j in range(3):
            assert J[i][j] == expected[i][j]

    print("[SUMMARY] test_df_dx_matches_analytical: df_dx ok for R, L, omega")


def test_dg_dy_matches_analytical():
    x = {"id": 1.0, "iq": -0.5, "Vdc": 2.0}
    Vdc = x["Vdc"]
    y = {"Idc": 1.0, "P_ac": 2.0, "Q_ac": 3.0}
    params = {}
    inputs = {}

    J = dg_dy(x, y, params, inputs)

    # Derivadas esperadas:
    # g_Idc: [1, -1/Vdc, 0]
    # g_P:   [0, 1, 0]
    # g_Q:   [0, 0, 1]
    expected = [
        [1.0, -1.0 / Vdc, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    for i in range(3):
        for j in range(3):
            assert abs(J[i][j] - expected[i][j]) < 1e-9

    print("[SUMMARY] test_dg_dy_matches_analytical: dg_dy ok for Vdc=", Vdc)
