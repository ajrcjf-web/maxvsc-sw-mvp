"""
Condiciones iniciales del modelo RMS.

Provee valores iniciales para:
- Estados dinámicos x = {id, iq, Vdc}
- Variables algebraicas y = {Idc, P_ac, Q_ac}

Este módulo no introduce modelos ni ecuaciones nuevas: solo organiza
las condiciones iniciales que se utilizarán en:

- model.dae (f_rhs, g_residual)
- solver.simulation (run_step)

Implementación conforme a la ETU v1.3 (ENG-1.0).
"""

from typing import Mapping, Any

from vscsim.model.variables import STATE_KEYS, ALGEBRAIC_KEYS


def load_initial_conditions(config: Mapping[str, Any]) -> dict:
    """
    Devuelve un diccionario con condiciones iniciales para estados y
    variables algebraicas.

    Formato esperado de config
    ---------------------------
    config puede contener dos niveles lógicos:

    - Claves directas para estados:
        "id", "iq", "Vdc"

    - Claves directas para algebraicas:
        "Idc", "P_ac", "Q_ac"

    También se permite (opcionalmente) agrupar en sub-dicts:
        "x0": { "id": ..., "iq": ..., "Vdc": ... }
        "y0": { "Idc": ..., "P_ac": ..., "Q_ac": ... }

    Política ENG-1.0
    ----------------
    - Para los estados x:
        Si no se proporciona un valor, se inicializa a 0.0.

    - Para las algebraicas y:
        Si no se proporciona un valor, se inicializa a 0.0.
        De este modo, y0 siempre contiene las tres componentes
        {Idc, P_ac, Q_ac} y el solver NR dispone de un vector inicial
        completo para g(x, y) = 0.

    La consistencia fina con g(x, y) = 0 (por ejemplo, ajustar y0
    para cumplir exactamente las ecuaciones) corresponde a la fase
    de inicialización / tests, no a este módulo de I/O.

    Parámetros
    ----------
    config :
        Diccionario de configuración de condiciones iniciales.

    Retorno
    -------
    ic : dict
        Diccionario con dos claves:
            "x0": dict con {id, iq, Vdc}
            "y0": dict con {Idc, P_ac, Q_ac} (siempre las tres, con
                  valores por defecto 0.0 si no se dan).
    """
    x0: dict[str, float] = {}
    y0: dict[str, float] = {}

    # 1) Estados dinámicos x = {id, iq, Vdc}
    # Intentar primero desde sub-dict "x0" si existe
    x0_cfg = config.get("x0", {})

    for name in STATE_KEYS:
        if name in x0_cfg:
            x0[name] = float(x0_cfg[name])
        elif name in config:
            x0[name] = float(config[name])
        else:
            # Valor por defecto en ENG-1.0
            x0[name] = 0.0

    # 2) Variables algebraicas y = {Idc, P_ac, Q_ac}
    # Intentar primero desde sub-dict "y0" si existe
    y0_cfg = config.get("y0", {})

    for name in ALGEBRAIC_KEYS:
        if name in y0_cfg:
            y0[name] = float(y0_cfg[name])
        elif name in config:
            y0[name] = float(config[name])
        else:
            # Valor por defecto en ENG-1.0 para asegurar que y0
            # siempre tenga Idc, P_ac y Q_ac definidos, de modo que
            # g_residual y NR puedan trabajar sin claves ausentes.
            y0[name] = 0.0

    return {
        "x0": x0,
        "y0": y0,
    }
