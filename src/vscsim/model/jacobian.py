"""
Cálculo de Jacobianos para la formulación DAE del modelo RMS.

Incluye:
- df/dx
- dg/dx
- dg/dy

Reglas (ETU v1.3, Sección 4.5):
- No derivar la saturación.
- No derivar respecto a v_conv_d, v_conv_q.
- v_conv_d y v_conv_q se consideran constantes dentro del NR.

Implementación conforme a ENG-1.0.
"""

from typing import Mapping

# quitar:
# from .variables import STATE_KEYS, ALGEBRAIC_KEYS


def df_dx(
    x: Mapping[str, float],
    y: Mapping[str, float],
    params: Mapping[str, float],
    inputs: Mapping[str, float],
) -> list[list[float]]:
    """
    Calcula la matriz df/dx a partir de las ecuaciones dinámicas f(x, y).

    Ecuaciones dinámicas (de f_rhs):

        L * di_d/dt = v_conv_d - R * id + ω * L * iq - v_pcc_d
        L * di_q/dt = v_conv_q - R * iq - ω * L * id - v_pcc_q
        Cdc * dVdc/dt = Idc

    con:
        x = {id, iq, Vdc}
        y = {Idc, P_ac, Q_ac}

    Derivadas resultantes:

        ∂(di_d/dt)/∂id   = -R/L
        ∂(di_d/dt)/∂iq   =  ω
        ∂(di_d/dt)/∂Vdc  =  0

        ∂(di_q/dt)/∂id   = -ω
        ∂(di_q/dt)/∂iq   = -R/L
        ∂(di_q/dt)/∂Vdc  =  0

        ∂(dVdc/dt)/∂id   =  0
        ∂(dVdc/dt)/∂iq   =  0
        ∂(dVdc/dt)/∂Vdc  =  0
    """
    # Parámetros eléctricos
    L = params["L"]
    R = params["R"]
    omega = params["omega"]

    # Coeficientes comunes
    R_over_L = R / L
    # omega se usa tal cual

    # Orden de estados: STATE_KEYS = ("id", "iq", "Vdc")
    # Orden de ecuaciones dinámicas: ("id", "iq", "Vdc")

    return [
        # df_id/dx  = [∂f_id/∂id, ∂f_id/∂iq, ∂f_id/∂Vdc]
        [-R_over_L, omega, 0.0],
        # df_iq/dx  = [∂f_iq/∂id, ∂f_iq/∂iq, ∂f_iq/∂Vdc]
        [-omega, -R_over_L, 0.0],
        # df_Vdc/dx = [∂f_Vdc/∂id, ∂f_Vdc/∂iq, ∂f_Vdc/∂Vdc]
        [0.0, 0.0, 0.0],
    ]


def dg_dx(
    x: Mapping[str, float],
    y: Mapping[str, float],
    params: Mapping[str, float],
    inputs: Mapping[str, float],
) -> list[list[float]]:
    """
    Calcula la matriz dg/dx a partir de las ecuaciones algebraicas g(x, y).

    Ecuaciones algebraicas (de g_residual):

        P_ac = 1.5 * (v_pcc_d * id + v_pcc_q * iq)
        Q_ac = 1.5 * (v_pcc_q * id - v_pcc_d * iq)
        Idc  = P_ac / Vdc

    Residuales:

        g_Idc = Idc - P_ac / Vdc
        g_P   = P_ac - 1.5 * (v_pcc_d * id + v_pcc_q * iq)
        g_Q   = Q_ac - 1.5 * (v_pcc_q * id - v_pcc_d * iq)

    con:
        x = {id, iq, Vdc}
        y = {Idc, P_ac, Q_ac}

    Derivadas respecto a x:

        g_Idc:
            ∂g_Idc/∂id   = 0
            ∂g_Idc/∂iq   = 0
            ∂g_Idc/∂Vdc  =  P_ac / Vdc^2

        g_P:
            ∂g_P/∂id     = -1.5 * v_pcc_d
            ∂g_P/∂iq     = -1.5 * v_pcc_q
            ∂g_P/∂Vdc    = 0

        g_Q:
            ∂g_Q/∂id     = -1.5 * v_pcc_q
            ∂g_Q/∂iq     =  1.5 * v_pcc_d
            ∂g_Q/∂Vdc    = 0

    La matriz se devuelve en el orden de ALGEBRAIC_KEYS por filas
    y STATE_KEYS por columnas.
    """
    # Estados
    Vdc = x["Vdc"]

    # Algebraicas
    P_ac = y["P_ac"]

    # Entradas
    v_pcc_d = inputs["v_pcc_d"]
    v_pcc_q = inputs["v_pcc_q"]

    factor = 1.5

    # Derivadas para g_Idc
    dg_Idc_did = 0.0
    dg_Idc_diq = 0.0
    dg_Idc_dVdc = P_ac / (Vdc * Vdc)

    # Derivadas para g_P
    dg_P_did = -factor * v_pcc_d
    dg_P_diq = -factor * v_pcc_q
    dg_P_dVdc = 0.0

    # Derivadas para g_Q
    dg_Q_did = -factor * v_pcc_q
    dg_Q_diq = factor * v_pcc_d
    dg_Q_dVdc = 0.0

    # Orden de filas: ("Idc", "P_ac", "Q_ac")
    # Orden de columnas: ("id", "iq", "Vdc")

    return [
        [dg_Idc_did, dg_Idc_diq, dg_Idc_dVdc],
        [dg_P_did, dg_P_diq, dg_P_dVdc],
        [dg_Q_did, dg_Q_diq, dg_Q_dVdc],
    ]


def dg_dy(
    x: Mapping[str, float],
    y: Mapping[str, float],
    params: Mapping[str, float],
    inputs: Mapping[str, float],
) -> list[list[float]]:
    """
    Calcula la matriz dg/dy a partir de las ecuaciones algebraicas g(x, y).

    Recordando:

        g_Idc = Idc - P_ac / Vdc
        g_P   = P_ac - P_calc
        g_Q   = Q_ac - Q_calc

    con:
        x = {id, iq, Vdc}
        y = {Idc, P_ac, Q_ac}

    Derivadas respecto a y:

        g_Idc:
            ∂g_Idc/∂Idc  = 1
            ∂g_Idc/∂P_ac = -1 / Vdc
            ∂g_Idc/∂Q_ac = 0

        g_P:
            ∂g_P/∂Idc   = 0
            ∂g_P/∂P_ac  = 1
            ∂g_P/∂Q_ac  = 0

        g_Q:
            ∂g_Q/∂Idc   = 0
            ∂g_Q/∂P_ac  = 0
            ∂g_Q/∂Q_ac  = 1

    La matriz se devuelve en el orden de ALGEBRAIC_KEYS
    tanto por filas como por columnas.
    """
    # Estados
    Vdc = x["Vdc"]

    # Derivadas para g_Idc
    dg_Idc_dIdc = 1.0
    dg_Idc_dP_ac = -1.0 / Vdc
    dg_Idc_dQ_ac = 0.0

    # Derivadas para g_P
    dg_P_dIdc = 0.0
    dg_P_dP_ac = 1.0
    dg_P_dQ_ac = 0.0

    # Derivadas para g_Q
    dg_Q_dIdc = 0.0
    dg_Q_dP_ac = 0.0
    dg_Q_dQ_ac = 1.0

    # Orden de filas y columnas: ("Idc", "P_ac", "Q_ac")

    return [
        [dg_Idc_dIdc, dg_Idc_dP_ac, dg_Idc_dQ_ac],
        [dg_P_dIdc, dg_P_dP_ac, dg_P_dQ_ac],
        [dg_Q_dIdc, dg_Q_dP_ac, dg_Q_dQ_ac],
    ]
