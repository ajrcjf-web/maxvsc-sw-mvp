"""
Definición y carga de escenarios de simulación.

Incluye:
- Configuración de modo de control externo.
- Referencias de potencia o corriente según el modo.
- Tensiones en el PCC (v_pcc_d, v_pcc_q).

Este módulo no introduce modelos nuevos ni ecuaciones: solo organiza
los datos de escenario que consumen:

- vsc.control_external
- solver.simulation

Implementación conforme a ENG-1.0.
"""

from typing import Mapping, Any


_REQUIRED_COMMON_KEYS = (
    "control_mode",  # "PQ" o "VdcQ"
    "v_pcc_d",       # tensión d en el PCC
    "v_pcc_q",       # tensión q en el PCC
)

_REQUIRED_PQ_KEYS = (
    "P_ref",         # referencia de potencia activa
    "Q_ref",         # referencia de potencia reactiva
)

_REQUIRED_VDCQ_KEYS = (
    "id_ref",        # referencia de corriente d (asociada a Vdc/Q en el escenario)
    "iq_ref",        # referencia de corriente q
)


def load_scenario(config: Mapping[str, Any]) -> dict:
    """
    Construye el escenario de simulación a partir de una configuración mínima.

    No se añaden ecuaciones ni dinámicas de control: sólo se verifica
    que los datos necesarios para el control externo y la simulación
    estén presentes y se copian a un dict interno.

    Modos soportados
    ----------------
    control_mode = "PQ":
        El control externo usa P_ref, Q_ref y v_pcc_d/q para calcular id_ref, iq_ref.

        Se requieren en config:
            "P_ref", "Q_ref", "v_pcc_d", "v_pcc_q"

    control_mode = "VdcQ":
        En ENG-1.0, el lazo de Vdc/Q se delega al escenario: éste debe
        proporcionar directamente id_ref, iq_ref.

        Se requieren en config:
            "id_ref", "iq_ref", "v_pcc_d", "v_pcc_q"

    Parámetros
    ----------
    config :
        Diccionario de configuración de escenario.

    Retorno
    -------
    scenario : dict
        Diccionario listo para utilizarse en:
            - vsc.control_external.compute_current_references
            - solver.simulation.run_step

    Errores
    -------
    ValueError :
        Si falta alguna clave obligatoria según el modo.
    """
    scenario: dict[str, Any] = {}

    # Verificación de claves comunes
    missing_common = [k for k in _REQUIRED_COMMON_KEYS if k not in config]
    if missing_common:
        raise ValueError(
            f"Missing required scenario keys: {', '.join(missing_common)}"
        )

    control_mode = str(config["control_mode"])
    scenario["control_mode"] = control_mode

    # Copia de tensiones PCC
    scenario["v_pcc_d"] = float(config["v_pcc_d"])
    scenario["v_pcc_q"] = float(config["v_pcc_q"])

    # Validación según modo
    if control_mode == "PQ":
        missing_pq = [k for k in _REQUIRED_PQ_KEYS if k not in config]
        if missing_pq:
            raise ValueError(
                f"Missing required PQ scenario keys: {', '.join(missing_pq)}"
            )

        scenario["P_ref"] = float(config["P_ref"])
        scenario["Q_ref"] = float(config["Q_ref"])

    elif control_mode == "VdcQ":
        missing_vdcq = [k for k in _REQUIRED_VDCQ_KEYS if k not in config]
        if missing_vdcq:
            raise ValueError(
                f"Missing required VdcQ scenario keys: {', '.join(missing_vdcq)}"
            )

        scenario["id_ref"] = float(config["id_ref"])
        scenario["iq_ref"] = float(config["iq_ref"])

    else:
        # Modo no reconocido: en ENG-1.0, se considera error explícito.
        raise ValueError(f"Unsupported control_mode in scenario: {control_mode!r}")

    # Copia opcional de claves adicionales sin interpretarlas.
    # Esto permite extender la información de escenario sin alterar la
    # ingeniería del modelo ni del solver.
    for name, value in config.items():
        if name not in scenario:
            scenario[name] = value

    return scenario
