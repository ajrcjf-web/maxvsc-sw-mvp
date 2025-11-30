"""
Integrador de los estados x del modelo RMS.

Integra:
    x_dot = f(x, y)

La ETU v1.3 permite integración explícita o semi-implícita. Aquí se
implementa un integrador explícito de Euler, sin alterar el modelo ni
la secuencia numérica 5.2.

Implementación conforme a ENG-1.0.
"""

from typing import Mapping


def step_forward(
    x: Mapping[str, float],
    x_dot: Mapping[str, float],
    dt: float,
) -> dict:
    """
    Integra los estados x durante un paso de tiempo dt usando Euler explícito.

        x_next = x + dt * x_dot

    donde:
        x     = {id, iq, Vdc}
        x_dot = f(x, y) evaluado en el instante actual.

    Parámetros
    ----------
    x :
        Estados dinámicos actuales.

    x_dot :
        Derivadas de los estados dinámicos en el instante actual.

    dt :
        Paso de integración.

    Retorno
    -------
    x_next : dict
        Nuevo estado integrado tras un paso dt.

    Notas
    -----
    - Este integrador no modifica la formulación del modelo (f, g).
    - La elección de Euler explícito es compatible con la ETU v1.3,
      que permite integración explícita o semi-implícita.
    """
    x_next: dict[str, float] = {}

    for key, value in x.items():
        # Se asume que x_dot contiene derivadas para las mismas claves
        dx_dt = x_dot.get(key, 0.0)
        x_next[key] = value + dt * dx_dt

    return x_next
