"""
Secuencia de simulación RMS VSC-HVDC (secuencia 5.2 de la ETU v1.3).

Este módulo implementa:

- run_step: un único paso de simulación, que:
  1. Evalúa el control externo (modo PQ o VdcQ).
  2. Evalúa el control interno proporcional en dq.
  3. Aplica la saturación de tensión del convertidor.
  4. Resuelve las ecuaciones algebraicas g(x, y) = 0 mediante NR.
  5. Evalúa f(x, y) para obtener x_dot.
  6. Integra los estados x usando:
     - Euler explícito (comportamiento por defecto, ENG-1.0), o
     - un integrador RK configurable (RK1/RK2/RK4) como parte del framework.

- run_simulation_adaptive: un lazo externo que llama repetidamente a run_step
  usando un dt adaptativo basado en un estimador de error local “paso grueso
  vs dos pasos finos”.

No modifica el modelo eléctrico ni las ecuaciones de la DAE; solamente
orquesta la ejecución en el orden aprobado en ENG-1.0.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Tuple, List, cast

from vscsim.model.dae import f_rhs, g_residual
from vscsim.model.jacobian import dg_dy
from vscsim.solver.integrator import step_forward
from vscsim.solver.integrator_factory import get_integrator
from vscsim.solver.nr import JacobianFunc, ResidualFunc, newton_raphson
from vscsim.solver.timestepper import AdaptiveTimestepper
from vscsim.utils.logger import global_log
from vscsim.vsc.control_external import compute_current_references
from vscsim.vsc.control_inner import compute_converter_voltage_references
from vscsim.vsc.saturation import apply_voltage_saturation


def _build_inputs(
    scenario: Mapping[str, Any],
    v_conv_d: float,
    v_conv_q: float,
) -> dict[str, float]:
    """Construye el diccionario de inputs para el modelo DAE."""
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
    """Aplica límites de escenario a x e y (identidad en ENG-1.0)."""
    return dict(x), dict(y)


def run_step(
    t: float,
    dt: float,
    x: Mapping[str, float],
    y: Mapping[str, float],
    scenario: Mapping[str, Any],
    params: Mapping[str, float],
    integrator_name: str | None = None,
) -> Tuple[dict[str, float], dict[str, float]]:
    """Ejecuta un paso de simulación respetando exactamente la secuencia 5.2."""
    # ------------------------------------------------------------------
    # Logging general: inicio de paso
    # ------------------------------------------------------------------
    global_log(
        "debug",
        "sim_step_start",
        t=t,
        dt=dt,
        integrator=integrator_name or "legacy_euler",
    )

    # ------------------------------------------------------------------
    # Selección de integrador numérico (Track A1.1 - framework)
    # ------------------------------------------------------------------
    use_legacy_euler = integrator_name is None
    rk_integrator = None
    if not use_legacy_euler:
        rk_integrator = get_integrator(integrator_name)  # type: ignore[arg-type]

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
        return dg_dy(
            x_nr,
            y_nr,
            params_nr or params,
            inputs_nr or inputs,
        )

    # Ajustes de tipado para mypy: el comportamiento en tiempo de ejecución
    # no cambia, sólo se hace un cast explícito al tipo de protocolo.
    residual_typed: ResidualFunc = cast(ResidualFunc, residual_func)
    jacobian_typed: JacobianFunc = cast(JacobianFunc, jacobian_func)

    y_next, nr_iter = newton_raphson(
        x=dict(x),
        y0=dict(y),
        residual=residual_typed,
        jacobian=jacobian_typed,
        params=params,
        inputs=inputs,
    )

    # Logging NR (general sim, complementa el logging interno de NR)
    global_log(
        "debug",
        "nr_solve",
        iterations=nr_iter,
    )

    # ------------------------------------------------------------------
    # 5) Evaluar f(x, y) para obtener x_dot / RHS
    # ------------------------------------------------------------------
    if use_legacy_euler:
        x_dot = f_rhs(
            x=dict(x),
            y=y_next,
            params=params,
            inputs=inputs,
        )

        # 6) Integrar estados x con Euler explícito (step_forward)
        x_next = step_forward(
            x=dict(x),
            x_dot=x_dot,
            dt=dt,
        )
    else:

        def rhs(state: Mapping[str, float], context: Mapping[str, Any]) -> dict[str, float]:
            return f_rhs(
                x=dict(state),
                y=y_next,
                params=params,
                inputs=inputs,
            )

        x_next = rk_integrator.step(  # type: ignore[union-attr]
            f=rhs,
            state=dict(x),
            dt=dt,
            context={},
        )

    # ------------------------------------------------------------------
    # 7) Aplicar límites de escenario (identidad en ENG-1.0)
    # ------------------------------------------------------------------
    x_limited, y_limited = _apply_scenario_limits(x_next, y_next, scenario)

    # Logging general: fin de paso
    global_log(
        "debug",
        "sim_step_end",
        t=t,
        dt=dt,
    )

    return x_limited, y_limited


def run_simulation_adaptive(
    t0: float,
    t_end: float,
    x0: Mapping[str, float],
    y0: Mapping[str, float],
    scenario: Mapping[str, Any],
    params: Mapping[str, float],
    integrator_name: str = "rk4",
    dt_initial: float = 1e-3,
    dt_min: float = 1e-5,
    dt_max: float = 1e-1,
    tol: float = 1e-4,
    max_steps: int = 100000,
) -> tuple[List[float], List[dict[str, float]], List[dict[str, float]], List[float]]:
    """
    Ejecuta una simulación completa con dt adaptativo usando run_step como
    “caja negra” de la secuencia 5.2.

    Estrategia de control de error:
        - Paso “grueso”:     dt
        - Dos pasos “finos”: dt/2 + dt/2
        - error_estimate = max |x_coarse - x_fine|

    Si error_estimate <= tol → se acepta el paso (con la solución fina).
    Si error_estimate >  tol → se reduce dt y se reintenta. Si ya estamos
    en dt_min, se fuerza la aceptación del paso para garantizar progreso.
    """
    if t_end <= t0:
        raise ValueError("t_end must be > t0")

    times: List[float] = [t0]
    x_history: List[dict[str, float]] = [dict(x0)]
    y_history: List[dict[str, float]] = [dict(y0)]
    dt_history: List[float] = []

    t = float(t0)
    x = dict(x0)
    y = dict(y0)

    ts = AdaptiveTimestepper(
        dt=dt_initial,
        dt_min=dt_min,
        dt_max=dt_max,
        safety=0.9,
        growth_factor_max=2.0,
        shrink_factor_min=0.5,
        order=2.0,
    )

    steps = 0

    while t < t_end and steps < max_steps:
        dt = ts.current_dt()
        if t + dt > t_end:
            dt = t_end - t

        # Logging: intento de paso adaptativo
        global_log(
            "debug",
            "adaptive_step_try",
            t=t,
            dt=dt,
        )

        # Coarse: un paso dt
        x_coarse, y_coarse = run_step(
            t=t,
            dt=dt,
            x=x,
            y=y,
            scenario=scenario,
            params=params,
            integrator_name=integrator_name,
        )

        # Fine: dos pasos dt/2
        dt_half = dt * 0.5

        x_half, y_half = run_step(
            t=t,
            dt=dt_half,
            x=x,
            y=y,
            scenario=scenario,
            params=params,
            integrator_name=integrator_name,
        )

        x_fine, y_fine = run_step(
            t=t + dt_half,
            dt=dt_half,
            x=x_half,
            y=y_half,
            scenario=scenario,
            params=params,
            integrator_name=integrator_name,
        )

        # Estimador de error local sobre x
        error_estimate = 0.0
        for key in x.keys():
            err_k = abs(x_coarse[key] - x_fine[key])
            if err_k > error_estimate:
                error_estimate = err_k

        new_dt = ts.update(error_estimate=error_estimate, tol=tol)

        # Criterio de aceptación:
        #  - error_estimate <= tol → aceptamos
        #  - o bien, estamos ya en dt_min → aceptación forzada
        accept = (error_estimate <= tol) or math.isclose(
            new_dt,
            dt_min,
            rel_tol=0.0,
            abs_tol=1e-15,
        )

        # Logging del resultado del paso adaptativo
        global_log(
            "debug",
            "adaptive_step_eval",
            t=t,
            dt=dt,
            error=error_estimate,
            new_dt=new_dt,
            accept=accept,
        )

        if accept:
            t = t + dt
            x = x_fine
            y = y_fine
            steps += 1

            times.append(t)
            x_history.append(dict(x))
            y_history.append(dict(y))
            dt_history.append(dt)
        else:
            # Rechazar paso, reintentar con dt actualizado
            continue

    if steps >= max_steps:
        raise RuntimeError(
            "run_simulation_adaptive: max_steps alcanzado sin llegar a t_end",
        )

    return times, x_history, y_history, dt_history
