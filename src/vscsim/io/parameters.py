"""
Carga de parámetros eléctricos y de control.

Responsabilidad:
- Proveer un contenedor básico de parámetros para el simulador RMS.
- Garantizar que existen las claves mínimas que usan:
    - model.dae
    - vsc.control_inner
    - vsc.saturation
    - solver.simulation

No introduce nuevas ecuaciones ni modelos: solo organiza parámetros
según la ETU v1.3 (ENG-1.0).
"""

from typing import Mapping


# Conjunto mínimo de parámetros requeridos por los módulos ya implementados.
# Esto NO define ingeniería nueva; solo refleja lo que el código ya asume.
_REQUIRED_PARAMS = (
    "L",        # inductancia del filtro AC
    "R",        # resistencia del filtro AC
    "Cdc",      # capacitancia del enlace DC
    "omega",    # frecuencia angular síncrona
    "V_max",    # módulo máximo de tensión del convertidor
    "Kp_id",    # ganancia proporcional lazo d
    "Kp_iq",    # ganancia proporcional lazo q
)


def load_parameters(config: Mapping[str, float]) -> dict:
    """
    Carga y normaliza los parámetros del sistema a partir de una configuración mínima.

    Esta función:
    - Verifica que están presentes las claves mínimas requeridas.
    - Copia los valores a un dict interno.
    - No altera la ingeniería del modelo ni introduce parámetros nuevos.

    Parámetros
    ----------
    config :
        Diccionario de parámetros de entrada. Debe contener como mínimo:

            L      : inductancia del filtro AC
            R      : resistencia del filtro AC
            Cdc    : capacitancia del enlace DC
            omega  : frecuencia angular síncrona (rad/s)
            V_max  : módulo máximo de tensión del convertidor
            Kp_id  : ganancia proporcional del lazo de corriente d
            Kp_iq  : ganancia proporcional del lazo de corriente q

    Retorno
    -------
    params : dict
        Diccionario de parámetros listo para usar por el modelo y el solver.

    Errores
    -------
    ValueError :
        Si falta algún parámetro requerido.
    """
    params: dict[str, float] = {}

    # Verificación de parámetros obligatorios
    missing = [name for name in _REQUIRED_PARAMS if name not in config]
    if missing:
        raise ValueError(
            f"Missing required parameters in config: {', '.join(missing)}"
        )

    # Copia directa de los parámetros requeridos
    for name in _REQUIRED_PARAMS:
        params[name] = float(config[name])

    # Copia opcional de parámetros adicionales (sin interpretarlos)
    # Esto permite que el escenario/usuario añada parámetros extra sin
    # que este módulo altere la ingeniería.
    for name, value in config.items():
        if name not in params:
            params[name] = float(value)

    return params
