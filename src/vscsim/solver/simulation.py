"""
Secuencia de simulación RMS VSC-HVDC (secuencia 5.2 de la ETU v1.3).

Este módulo implementa un único paso de simulación, run_step, que:

1. Evalúa el control externo (modo PQ o VdcQ).
2. Evalúa el control interno proporcional en dq.
3. Aplica la saturación de tensión del convertidor.
4. Resuelve las ecuaciones algebraicas g(x, y) = 0 mediante NR.
5. Evalúa f(x, y) para obtener x_dot.
6. Integra los estados x usando Euler explícito.

No modifica el modelo eléctrico ni las ecuaciones de la DAE; solamente
orquesta la ejecución en el orden aprobado en ENG-1.0.
"""

from __future__ import annotations

from typing import Any, Mapping, Tuple

from vscsim.model.dae import f_rhs, g_residual
from vscsim.model.jacobian import dg_dy
from vscsim.solver.integrator import step_forward
from vscsim.solver.nr import JacobianFunc, ResidualFunc, newton_raphson
from vscsim.vsc.control_external import compute_current_references
from vscsim.vsc.control_inner import compute_converter_voltage_references
from vscsim.vsc.saturation import apply_voltage_saturation


def _build_inputs(
    scenario: Mapping[str, Any],
    v_conv_d: float,
    v_conv_q: float,
) -> dict[str, float]:
    """Construye el diccionario de inputs para el modelo DAE.

    Incluye:
    - v_conv_d, v_conv_q: tensión del convertidor (después de saturación).
    - v_pcc_d, v_pcc_q: tensión en el PCC, proveniente del escenario.
    """
    v_pcc_d = float(scenario.get("v_pcc_d", 1.0))
    v_pcc_q = float(scenario.get("v_pcc_q", 0.0))
    return {
        "v_conv_d": v_conv_d,
        "v_conv_q": v_conv_q,
        "v_pcc_d": v_pcc_d,
        "v_pcc_q": v_pcc_q,
    }


def _apply_scenario_limits(
    x: Mapping[str, float],
    y: Mapping[str, float],
    scenario: Mapping[str, Any],
) -> Tuple[dict[str, float], dict[str, float]]:
    """Aplica límites de escenario a x e y.

    Para ENG-1.0 esta función es identidad; se deja como punto de extensión
    para futuros recortes de estados / potencias definidos por ingeniería.
    """
    return dict(x), dict(y)


def run_step(
    t: float,
    dt: float,
    x: Mapping[str, float],
    y: Mapping[str, float],
    scenario: Mapping[str, Any],
    params: Mapping[str, float],
) -> Tuple[dict[str, float], dict[str, float]]:
    """Ejecuta un paso de simulación respetando exactamente la secuencia 5.2.

    Parámetros
    ----------
    t :
        Tiempo actual (no se usa en el modelo, pero se pasa para posibles
        extensiones futuras).

    dt :
        Paso de integración.

    x :
        Estados dinámicos actuales x_k = {id, iq, Vdc}.

    y :
        Variables algebraicas actuales y_k = {Idc, P_ac, Q_ac}.

    scenario :
        Escenario de simulación (incluye modo de control, referencias,
        tensiones en el PCC, etc.).

    params :
        Parámetros eléctricos y de control.

    Retorno
    -------
    x_next, y_next :
        Estados y algebraicas después de un paso de simulación de duración dt.
    """
    # ------------------------------------------------------------------
    # 1) Control externo
    # ------------------------------------------------------------------
    refs = compute_current_references(
        t=t,
        x=x,
        y=y,
        scenario=scenario,
        params=params,
    )
    # compute_current_references devuelve un dict; extraemos las referencias
    id_ref = float(refs.get("id_ref", 0.0))
    iq_ref = float(refs.get("iq_ref", 0.0))

    # ------------------------------------------------------------------
    # 2) Control interno proporcional (estructura compatible con PI)
    # ------------------------------------------------------------------
    voltages_ref, _controller_state = compute_converter_voltage_references(
        id_ref=id_ref,
        iq_ref=iq_ref,
        x=x,
        params=params,
        controller_state=None,
    )
    v_conv_d_ref = float(voltages_ref["v_conv_d_ref"])
    v_conv_q_ref = float(voltages_ref["v_conv_q_ref"])

    # ------------------------------------------------------------------
    # 3) Saturación de tensión del convertidor
    # ------------------------------------------------------------------
    v_max = float(params.get("V_max", 1.0))
    v_conv_d_sat, v_conv_q_sat = apply_voltage_saturation(
        v_conv_d_ref,
        v_conv_q_ref,
        v_max,
    )

    # ------------------------------------------------------------------
    # 4) Resolver g(x, y) = 0 mediante NR (sobre y únicamente)
    # ------------------------------------------------------------------
    inputs = _build_inputs(
        scenario=scenario,
        v_conv_d=v_conv_d_sat,
        v_conv_q=v_conv_q_sat,
    )

    def residual_func(
        x_nr: Mapping[str, float],
        y_nr: Mapping[str, float],
        params_nr: Mapping[str, float] | None,
        inputs_nr: Mapping[str, float] | None,
    ) -> dict[str, float]:
        """Wrapper que adapta g_residual a la firma de ResidualFunc.

        params_nr e inputs_nr pueden ser None según la firma conceptual
        de newton_raphson; aquí se sustituyen por los diccionarios reales
        si vienen a None.
        """
        return g_residual(
            x_nr,
            y_nr,
            params_nr or params,
            inputs_nr or inputs,
        )

    def jacobian_func(
        x_nr: Mapping[str, float],
        y_nr: Mapping[str, float],
        params_nr: Mapping[str, float] | None,
        inputs_nr: Mapping[str, float] | None,
    ) -> list[list[float]]:
        """Wrapper que adapta dg_dy a la firma de JacobianFunc."""
        return dg_dy(
            x_nr,
            y_nr,
            params_nr or params,
            inputs_nr or inputs,
        )

    # Tipos concretos para satisfacer a mypy
    residual_typed: ResidualFunc = residual_func
    jacobian_typed: JacobianFunc = jacobian_func

    y_next, _ = newton_raphson(
        x=dict(x),
        y0=dict(y),
        residual=residual_typed,
        jacobian=jacobian_typed,
        params=params,
        inputs=inputs,
    )

    # ------------------------------------------------------------------
    # 5) Evaluar f(x, y) para obtener x_dot
    # ------------------------------------------------------------------
    x_dot = f_rhs(
        x=dict(x),
        y=y_next,
        params=params,
        inputs=inputs,
    )

    # ------------------------------------------------------------------
    # 6) Integrar estados x
    # ------------------------------------------------------------------
    x_next = step_forward(
        x=dict(x),
        x_dot=x_dot,
        dt=dt,
    )

    # ------------------------------------------------------------------
    # 7) Aplicar límites de escenario (identidad en ENG-1.0)
    # ------------------------------------------------------------------
    x_limited, y_limited = _apply_scenario_limits(x_next, y_next, scenario)

    return x_limited, y_limited
