"""
Secuencia de simulación conforme a la Sección 5.2 de la ETU v1.3.

Orden obligatorio:
1) Control externo → id_ref, iq_ref
2) Control PI interno → v_conv_d*, v_conv_q*
3) Saturación → v_conv_d, v_conv_q
4) NR: g(x_k, y) = 0 → y_{k+1}
5) Cálculo de x_dot = f(x_k, y_{k+1})
6) Integración de x(t + dt)
7) Aplicar límites del escenario

Implementación conforme a ENG-1.0.

Este módulo solo orquesta la secuencia numérica; no modifica el modelo
eléctrico ni las ecuaciones de la DAE.
"""

from typing import Mapping, Any, Tuple

from vscsim.vsc.control_external import compute_current_references
from vscsim.vsc.control_inner import compute_converter_voltage_references
from vscsim.vsc.saturation import apply_voltage_saturation

from vscsim.model.dae import f_rhs, g_residual
from vscsim.model.jacobian import dg_dy

from vscsim.solver.nr import newton_raphson
from vscsim.solver.integrator import step_forward


def _apply_scenario_limits(
    x: Mapping[str, float],
    y: Mapping[str, float],
    scenario: Mapping[str, Any],
    params: Mapping[str, float],
) -> Tuple[dict, dict]:
    """
    Aplica los límites definidos por el escenario al final del paso.

    En la ETU v1.3 se indica el paso:
        7) Aplicar límites del escenario

    La lógica concreta de límites (por ejemplo, recorte de corrientes,
    tensiones o potencias) pertenece al nivel de escenario y validación.
    Para ENG-1.0, se deja como identidad (sin modificar x ni y).

    Esta función existe para reflejar explícitamente el paso 7, sin
    introducir nueva ingeniería.
    """
    # Identidad para ENG-1.0 (sin límites adicionales)
    return dict(x), dict(y)


def run_step(
    t: float,
    dt: float,
    x: Mapping[str, float],
    y: Mapping[str, float],
    scenario: Mapping[str, Any],
    params: Mapping[str, float],
) -> tuple[dict, dict]:
    """
    Ejecuta un paso de simulación respetando exactamente la secuencia 5.2.

    Parámetros
    ----------
    t :
        Tiempo actual.

    dt :
        Paso de integración.

    x :
        Estados dinámicos actuales (id, iq, Vdc).

    y :
        Variables algebraicas actuales (Idc, P_ac, Q_ac).

    scenario :
        Configuración del escenario de simulación (modo de control,
        referencias, tensiones en el PCC, etc.).

    params :
        Parámetros eléctricos y de control del sistema.

    Retorno
    -------
    x_next, y_next : tuple[dict, dict]
        Estados y variables algebraicas al final del paso de tiempo.
    """
    # ------------------------------------------------------------------
    # 1) Control externo → id_ref, iq_ref
    # ------------------------------------------------------------------
    refs = compute_current_references(t, x, y, scenario, params)
    id_ref = refs["id_ref"]
    iq_ref = refs["iq_ref"]

    # ------------------------------------------------------------------
    # 2) Control PI interno → v_conv_d*, v_conv_q*
    # ------------------------------------------------------------------
    voltages_ref, _controller_state_out = compute_converter_voltage_references(
        id_ref=id_ref,
        iq_ref=iq_ref,
        x=x,
        params=params,
        controller_state=None,
    )
    v_conv_d_ref = voltages_ref["v_conv_d_ref"]
    v_conv_q_ref = voltages_ref["v_conv_q_ref"]

    # ------------------------------------------------------------------
    # 3) Saturación → v_conv_d, v_conv_q
    # ------------------------------------------------------------------
    v_max = params["V_max"]
    v_conv_d, v_conv_q = apply_voltage_saturation(
        v_conv_d_ref,
        v_conv_q_ref,
        v_max,
    )

    # ------------------------------------------------------------------
    # 4) NR: g(x_k, y) = 0 → y_{k+1}
    # ------------------------------------------------------------------
    inputs = {
        "v_conv_d": v_conv_d,
        "v_conv_q": v_conv_q,
        "v_pcc_d": scenario["v_pcc_d"],
        "v_pcc_q": scenario["v_pcc_q"],
    }

    y_nr, _n_iter = newton_raphson(
        x=x,
        y0=y,
        residual=g_residual,
        jacobian=dg_dy,
        params=params,
        inputs=inputs,
    )

    # ------------------------------------------------------------------
    # 5) Cálculo de x_dot = f(x_k, y_{k+1})
    # ------------------------------------------------------------------
    x_dot = f_rhs(
        x=x,
        y=y_nr,
        params=params,
        inputs=inputs,
    )

    # ------------------------------------------------------------------
    # 6) Integración de x(t + dt)
    # ------------------------------------------------------------------
    x_next = step_forward(
        x=x,
        x_dot=x_dot,
        dt=dt,
    )

    # ------------------------------------------------------------------
    # 7) Aplicar límites del escenario
    # ------------------------------------------------------------------
    x_limited, y_limited = _apply_scenario_limits(
        x=x_next,
        y=y_nr,
        scenario=scenario,
        params=params,
    )

    return x_limited, y_limited
