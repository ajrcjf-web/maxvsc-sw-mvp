"""
Control externo del VSC.

Modos:
- Control P_ac / Q_ac   ("PQ")
- Control Vdc / Q_ac    ("VdcQ")

Produce:
- id_ref
- iq_ref

Implementación conforme a la ETU v1.3 (ENG-1.0):

- Usa exclusivamente las relaciones de potencia ya definidas en el modelo:
    P_ac = 1.5 * (v_pcc_d * id + v_pcc_q * iq)
    Q_ac = 1.5 * (v_pcc_q * id - v_pcc_d * iq)

- No introduce nuevas dinámicas ni estados.
"""

from typing import Mapping, Any


def _compute_currents_from_pq(
    P_ref: float,
    Q_ref: float,
    v_pcc_d: float,
    v_pcc_q: float,
) -> tuple[float, float]:
    """
    Calcula (id_ref, iq_ref) a partir de (P_ref, Q_ref) y (v_pcc_d, v_pcc_q)
    resolviendo el sistema lineal derivado de:

        P_ac = 1.5 * (v_pcc_d * id + v_pcc_q * iq)
        Q_ac = 1.5 * (v_pcc_q * id - v_pcc_d * iq)

    Esto es una simple inversión algebraica de las mismas ecuaciones
    usadas en el modelo, no un modelo nuevo.
    """
    factor = 1.5

    # Sistema:
    #   P_ref / factor = v_d * id + v_q * iq
    #   Q_ref / factor = v_q * id - v_d * iq
    sP = P_ref / factor
    sQ = Q_ref / factor

    v_d = v_pcc_d
    v_q = v_pcc_q

    # Matriz A:
    # [ v_d   v_q ]
    # [ v_q  -v_d ]
    det = v_d * (-v_d) - v_q * v_q  # = -(v_d^2 + v_q^2)

    if det == 0.0:
        # Escenario físicamente degenerado (tensión PCC nula):
        # en ENG-1.0, devolvemos corrientes nulas para evitar división por cero.
        return 0.0, 0.0

    inv_det = 1.0 / det

    # Inversa de A:
    # A^{-1} = 1/det * [ -v_d   -v_q ]
    #                   [ -v_q   v_d ]
    id_ref = inv_det * (-v_d * sP - v_q * sQ)
    iq_ref = inv_det * (-v_q * sP + v_d * sQ)

    return id_ref, iq_ref


def compute_current_references(
    t: float,
    x: Mapping[str, float],
    y: Mapping[str, float],
    scenario: Mapping[str, Any],
    params: Mapping[str, float],
) -> dict:
    """
    Calcula id_ref e iq_ref a partir del modo de control externo.

    Modos soportados (scenario["control_mode"]):

    - "PQ":
        Usa P_ref, Q_ref y v_pcc_d/q del escenario para obtener id_ref, iq_ref
        mediante las mismas ecuaciones de potencia que el modelo.

        Requiere en scenario:
            "P_ref", "Q_ref", "v_pcc_d", "v_pcc_q"

    - "VdcQ":
        Para ENG-1.0, se asume que el escenario ya proporciona directamente
        id_ref e iq_ref coherentes con los objetivos de Vdc/Q:

            "id_ref", "iq_ref"

        De este modo no se introduce ninguna dinámica adicional de control
        de Vdc; el tratamiento de Vdc se mantiene en el escenario.

    Esta implementación no introduce modelos nuevos; sólo reusa la
    formulación de potencia ya establecida o delega en el escenario.
    """
    mode = scenario.get("control_mode", "PQ")

    if mode == "PQ":
        P_ref = scenario["P_ref"]
        Q_ref = scenario["Q_ref"]
        v_pcc_d = scenario["v_pcc_d"]
        v_pcc_q = scenario["v_pcc_q"]

        id_ref, iq_ref = _compute_currents_from_pq(
            P_ref=P_ref,
            Q_ref=Q_ref,
            v_pcc_d=v_pcc_d,
            v_pcc_q=v_pcc_q,
        )
        return {"id_ref": id_ref, "iq_ref": iq_ref}

    if mode == "VdcQ":
        # Para ENG-1.0, el control de Vdc/Q se delega al escenario, que
        # debe proporcionar directamente las referencias de corriente.
        id_ref = scenario["id_ref"]
        iq_ref = scenario["iq_ref"]
        return {"id_ref": id_ref, "iq_ref": iq_ref}

    # Modo desconocido: por seguridad, devolver corrientes nulas.
    return {"id_ref": 0.0, "iq_ref": 0.0}
