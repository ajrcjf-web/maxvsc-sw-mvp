"""
Control dq interno del VSC.

Estructura conceptual (ETU v1.3):
- id_ref → PI_d → v_conv_d*
- iq_ref → PI_q → v_conv_q*

En ENG-1.0, se implementa un lazo proporcional sobre id/iq, usando
ganancias definidas en params, sin introducir estados dinámicos
adicionales (no se agrega la parte integradora al modelo).

Esto respeta:
- El modelo eléctrico (no se altera la DAE).
- La separación entre control externo e interno.
"""

from typing import Mapping


def compute_converter_voltage_references(
    id_ref: float,
    iq_ref: float,
    x: Mapping[str, float],
    params: Mapping[str, float],
    controller_state: Mapping[str, float] | None = None,
) -> tuple[dict, dict]:
    """
    Calcula v_conv_d* y v_conv_q* a partir de id_ref e iq_ref.

    Se usa un control proporcional simple:

        v_conv_d* = Kp_id * (id_ref - id)
        v_conv_q* = Kp_iq * (iq_ref - iq)

    donde:
        id, iq se toman de x.
        Kp_id, Kp_iq se definen en params.

    Parámetros
    ----------
    id_ref, iq_ref :
        Referencias de corriente en dq.

    x :
        Estados dinámicos actuales, incluyendo "id" y "iq".

    params :
        Parámetros de control que incluyen:
            "Kp_id": ganancia proporcional del lazo d
            "Kp_iq": ganancia proporcional del lazo q

    controller_state :
        Estado interno del controlador. Para ENG-1.0 no se modifica, ya
        que no se implementa la parte integradora. Se devuelve tal cual.

    Retorno
    -------
    voltages_ref : dict
        {"v_conv_d_ref": v_conv_d*, "v_conv_q_ref": v_conv_q*}

    controller_state_out : dict
        Estado interno del controlador (sin cambios en ENG-1.0).
    """
    id_ = x["id"]
    iq_ = x["iq"]

    Kp_id = params.get("Kp_id", 0.0)
    Kp_iq = params.get("Kp_iq", 0.0)

    e_id = id_ref - id_
    e_iq = iq_ref - iq_

    v_conv_d_ref = Kp_id * e_id
    v_conv_q_ref = Kp_iq * e_iq

    voltages_ref = {
        "v_conv_d_ref": v_conv_d_ref,
        "v_conv_q_ref": v_conv_q_ref,
    }

    controller_state_out = dict(controller_state or {})

    return voltages_ref, controller_state_out
