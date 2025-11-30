"""
Saturación de las tensiones de referencia del convertidor en dq.

Condición sobre las referencias antes de saturar:
    (v_conv_d*)^2 + (v_conv_q*)^2 ≤ V_max^2

Reglas (ETU v1.3, ENG-1.0):
- No derivar la saturación.
- No incluirla en el Jacobiano.
- No suavizar.

Esta función aplica exclusivamente la saturación definida, sin modificar
el modelo eléctrico ni la formulación de la DAE.
"""

import math


def apply_voltage_saturation(
    v_conv_d_ref: float,
    v_conv_q_ref: float,
    v_max: float,
) -> tuple[float, float]:
    """
    Aplica la saturación a (v_conv_d_ref, v_conv_q_ref),
correspondientes a (v_conv_d*, v_conv_q*) en la ETU.

Si el módulo de la tensión de referencia supera V_max, se escala el
vector (v_conv_d_ref, v_conv_q_ref) para que quede exactamente sobre
el círculo de radio V_max:

    (v_conv_d)^2 + (v_conv_q)^2 = V_max^2

Parámetros
----------
v_conv_d_ref, v_conv_q_ref :
    Tensiones de referencia no saturadas (v_conv_d*, v_conv_q*).

v_max :
    Módulo máximo permitido para la tensión del convertidor.

Retorno
-------
v_conv_d, v_conv_q : tuple[float, float]
    Tensiones de convertidor saturadas.
    """
    # Módulo cuadrado de la referencia
    v_sq = v_conv_d_ref * v_conv_d_ref + v_conv_q_ref * v_conv_q_ref

    # Si está dentro del límite (o es cero), no se modifica
    if v_sq <= v_max * v_max or v_sq == 0.0:
        return v_conv_d_ref, v_conv_q_ref

    # Escalado al círculo de radio V_max
    scale = v_max / math.sqrt(v_sq)
    v_conv_d = v_conv_d_ref * scale
    v_conv_q = v_conv_q_ref * scale

    return v_conv_d, v_conv_q
