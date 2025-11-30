# tests/test_solver_nr.py
"""
Pruebas del solver Newton–Raphson para y.
"""

from vscsim.solver.nr import newton_raphson
from vscsim.model.dae import g_residual
from vscsim.model.jacobian import dg_dy


def test_nr_converges_simple_system():
    # Sistema diagonal muy simple: y -> (1,2,3)
    def g_simple(x, y, params, inputs):
        return {
            "Idc": y["Idc"] - 1.0,
            "P_ac": y["P_ac"] - 2.0,
            "Q_ac": y["Q_ac"] - 3.0,
        }

    def J_simple(x, y, params, inputs):
        return [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]

    x = {"id": 0.0, "iq": 0.0, "Vdc": 1.0}
    y0 = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}

    y_nr, n_iter = newton_raphson(x, y0, g_simple, J_simple)

    assert y_nr["Idc"] == 1.0
    assert y_nr["P_ac"] == 2.0
    assert y_nr["Q_ac"] == 3.0
    assert n_iter <= 2

    print("[SUMMARY] test_nr_converges_simple_system: "
          f"y={y_nr}, iterations={n_iter}")


def test_nr_with_real_g_residual():
    # Punto consistente: g(x,y)=0 → NR debe converger en 0 iteraciones
    x = {"id": 0.0, "iq": 0.0, "Vdc": 1.0}
    params = {"L": 0.1, "R": 0.01, "Cdc": 0.01, "omega": 1.0}
    inputs = {"v_conv_d": 0.0, "v_conv_q": 0.0, "v_pcc_d": 1.0, "v_pcc_q": 0.0}
    y0 = {"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}

    y_nr, n_iter = newton_raphson(x, y0, g_residual, dg_dy, params, inputs)

    # g(x,y)=0 en ese punto; NR debe parar inmediatamente o en muy pocas iteraciones
    from vscsim.model.dae import g_residual as g_res

    g_final = g_res(x, y_nr, params, inputs)
    norm_g = max(abs(g_final[k]) for k in g_final.keys())

    assert norm_g < 1e-8

    print("[SUMMARY] test_nr_with_real_g_residual: "
          f"y={y_nr}, iterations={n_iter}, norm_g={norm_g}")
