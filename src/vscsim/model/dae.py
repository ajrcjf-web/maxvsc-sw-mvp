"""
Formulación DAE del modelo RMS VSC-HVDC en dq.

Conjuntos de variables:

- Estados dinámicos:
    x = {id, iq, Vdc}

- Variables algebraicas:
    y = {Idc, P_ac, Q_ac}

Funciones:

- f(x, y): define x_dot
- g(x, y): define el sistema algebraico g(x, y) = 0

Implementación conforme a la ETU v1.3 (ENG-1.0).
"""

from typing import Protocol, Mapping


class StateVector(Protocol):
    """Representa el estado dinámico x = {id, iq, Vdc}."""
    # Implementación concreta pendiente.


class AlgebraicVector(Protocol):
    """Representa las incógnitas algebraicas y = {Idc, P_ac, Q_ac}."""
    # Implementación concreta pendiente.


def f_rhs(
    x: Mapping[str, float],
    y: Mapping[str, float],
    params: Mapping[str, float],
    inputs: Mapping[str, float],
) -> dict:
    """
    Calcula x_dot = f(x, y).

    Ecuaciones dinámicas (ETU v1.3):

        L * di_d/dt = v_conv_d - R * id + ω * L * iq - v_pcc_d
        L * di_q/dt = v_conv_q - R * iq - ω * L * id - v_pcc_q
        Cdc * dVdc/dt = Idc

    donde:
        x = {id, iq, Vdc}
        y = {Idc, P_ac, Q_ac}

    params:
        Parámetros eléctricos del sistema (L, R, Cdc, omega, etc.).

    inputs:
        Tensiones en el convertidor y en el PCC:
        v_conv_d, v_conv_q, v_pcc_d, v_pcc_q.
    """
    # Estados dinámicos
    id_ = x["id"]
    iq_ = x["iq"]
    Vdc = x["Vdc"]

    # Algebraicas
    Idc = y["Idc"]

    # Parámetros eléctricos
    L = params["L"]          # inductancia del filtro AC
    R = params["R"]          # resistencia del filtro AC
    Cdc = params["Cdc"]      # capacitancia del enlace DC
    omega = params["omega"]  # frecuencia angular síncrona

    # Entradas (tensiones ya saturadas)
    v_conv_d = inputs["v_conv_d"]
    v_conv_q = inputs["v_conv_q"]
    v_pcc_d = inputs["v_pcc_d"]
    v_pcc_q = inputs["v_pcc_q"]

    # Ecuaciones diferenciales
    did_dt = (v_conv_d - R * id_ + omega * L * iq_ - v_pcc_d) / L
    diq_dt = (v_conv_q - R * iq_ - omega * L * id_ - v_pcc_q) / L
    dVdc_dt = Idc / Cdc

    return {
        "id": did_dt,
        "iq": diq_dt,
        "Vdc": dVdc_dt,
    }


def g_residual(
    x: Mapping[str, float],
    y: Mapping[str, float],
    params: Mapping[str, float],
    inputs: Mapping[str, float],
) -> dict:
    """
    Calcula g(x, y) = 0 para el sistema algebraico.

    Ecuaciones algebraicas (ETU v1.3):

        P_ac = 1.5 * (v_pcc_d * id + v_pcc_q * iq)
        Q_ac = 1.5 * (v_pcc_q * id - v_pcc_d * iq)
        Idc  = P_ac / Vdc

    Se formulan como residuales:

        g_P   = P_ac - 1.5 * (v_pcc_d * id + v_pcc_q * iq)
        g_Q   = Q_ac - 1.5 * (v_pcc_q * id - v_pcc_d * iq)
        g_Idc = Idc - P_ac / Vdc

    donde:
        x = {id, iq, Vdc}
        y = {Idc, P_ac, Q_ac}

    params:
        Parámetros del sistema. En la formulación actual de la ETU v1.3
        no aparecen explícitamente en las ecuaciones algebraicas, pero
        se mantiene este argumento por simetría de interfaz con f(x, y).

    inputs:
        Tensiones en el PCC:
        v_pcc_d, v_pcc_q.
    """
    # params no se usa explícitamente en g(x, y) para la formulación actual
    _ = params  # mantiene la firma DAE y evita avisos de variable sin uso

    # Estados dinámicos
    id_ = x["id"]
    iq_ = x["iq"]
    Vdc = x["Vdc"]

    # Algebraicas
    Idc = y["Idc"]
    P_ac = y["P_ac"]
    Q_ac = y["Q_ac"]

    # Entradas (tensiones en el PCC)
    v_pcc_d = inputs["v_pcc_d"]
    v_pcc_q = inputs["v_pcc_q"]

    # Potencias calculadas según la ETU
    P_calc = 1.5 * (v_pcc_d * id_ + v_pcc_q * iq_)
    Q_calc = 1.5 * (v_pcc_q * id_ - v_pcc_d * iq_)

    # Corriente DC calculada
    Idc_calc = P_ac / Vdc

    # Residuales algebraicos g(x, y) = 0
    g_Idc = Idc - Idc_calc
    g_P = P_ac - P_calc
    g_Q = Q_ac - Q_calc

    return {
        "Idc": g_Idc,
        "P_ac": g_P,
        "Q_ac": g_Q,
    }
