"""
API mínima para ejecutar simulaciones RMS VSC-HVDC.

Expone funciones de alto nivel para:
- Preparar parámetros y escenarios.
- Cargar condiciones iniciales.
- Ejecutar la simulación en el tiempo usando la secuencia 5.2.
- Devolver resultados básicos: id, iq, Vdc, Idc, P_ac, Q_ac.

Esta API no modifica el modelo ni el solver: sólo encadena:

- io.parameters.load_parameters
- io.scenario.load_scenario
- io.initial_conditions.load_initial_conditions
- solver.simulation.run_step

Implementación conforme a la ETU v1.3 (ENG-1.0).
"""

from typing import Mapping, Any

from vscsim.io.parameters import load_parameters
from vscsim.io.scenario import load_scenario
from vscsim.io.initial_conditions import load_initial_conditions
from vscsim.model.variables import ALGEBRAIC_KEYS

from vscsim.solver.simulation import run_step


def run_simulation(
    params_config: Mapping[str, float],
    scenario_config: Mapping[str, Any],
    t_end: float,
    dt: float,
) -> dict:
    """
    Ejecuta una simulación RMS VSC-HVDC hasta t_end con paso dt.

    Esta función:
    - Carga parámetros (eléctricos y de control).
    - Carga el escenario (modo de control, referencias, tensiones PCC).
    - Carga condiciones iniciales (x0, y0).
    - Ejecuta un lazo en el tiempo llamando a solver.simulation.run_step,
      que implementa la secuencia 5.2 de la ETU v1.3.
    - Devuelve las trayectorias de las variables básicas.

    Notas numéricas
    ---------------
    - Si t_end / dt no es entero, se usa:

          n_steps = int(t_end / dt)

      de modo que el último instante simulado es t = n_steps * dt,
      que será menor o igual que t_end. Esto no altera la ingeniería
      del modelo; es una decisión de implementación para ENG-1.0.

    Parámetros
    ----------
    params_config :
        Diccionario de parámetros de entrada, pasado a
        io.parameters.load_parameters.

    scenario_config :
        Diccionario de escenario, pasado a io.scenario.load_scenario.

    t_end :
        Tiempo final de simulación.

    dt :
        Paso de integración.

    Retorno
    -------
    results : dict
        Diccionario con:
            "time": lista de tiempos
            "x": dict con listas:
                "id":  [...],
                "iq":  [...],
                "Vdc": [...]
            "y": dict con listas:
                "Idc":  [...],
                "P_ac": [...],
                "Q_ac": [...]

        No se añade ninguna magnitud adicional fuera del baseline.
    """
    if dt <= 0.0:
        raise ValueError("Time step dt must be positive.")

    if t_end < 0.0:
        raise ValueError("t_end must be non-negative.")

    # ------------------------------------------------------------------
    # 1) Cargar parámetros, escenario y condiciones iniciales
    # ------------------------------------------------------------------
    params = load_parameters(params_config)
    scenario = load_scenario(scenario_config)
    ic = load_initial_conditions(scenario_config.get("initial_conditions", {}))

    x: dict[str, float] = dict(ic["x0"])
    y: dict[str, float] = dict(ic["y0"])

    # Asegurar que y contiene todas las algebraicas requeridas,
    # incluso si el escenario no proporcionó valores explícitos.
    for name in ALGEBRAIC_KEYS:
        if name not in y:
            y[name] = 0.0

    # ------------------------------------------------------------------
    # 2) Preparar estructuras de salida
    # ------------------------------------------------------------------
    times: list[float] = []
    x_hist: dict[str, list[float]] = {
        "id": [],
        "iq": [],
        "Vdc": [],
    }
    y_hist: dict[str, list[float]] = {
        "Idc": [],
        "P_ac": [],
        "Q_ac": [],
    }

    # Estado inicial
    t = 0.0
    times.append(t)
    x_hist["id"].append(x["id"])
    x_hist["iq"].append(x["iq"])
    x_hist["Vdc"].append(x["Vdc"])
    y_hist["Idc"].append(y["Idc"])
    y_hist["P_ac"].append(y["P_ac"])
    y_hist["Q_ac"].append(y["Q_ac"])

    # Número de pasos
    if t_end == 0.0:
        # Solo devolvemos el estado inicial
        return {
            "time": times,
            "x": x_hist,
            "y": y_hist,
        }

    n_steps = int(t_end / dt)

    # ------------------------------------------------------------------
    # 3) Lazo en el tiempo usando la secuencia 5.2 (run_step)
    # ------------------------------------------------------------------
    for _ in range(n_steps):
        x, y = run_step(
            t=t,
            dt=dt,
            x=x,
            y=y,
            scenario=scenario,
            params=params,
        )
        t += dt

        times.append(t)
        x_hist["id"].append(x["id"])
        x_hist["iq"].append(x["iq"])
        x_hist["Vdc"].append(x["Vdc"])
        y_hist["Idc"].append(y["Idc"])
        y_hist["P_ac"].append(y["P_ac"])
        y_hist["Q_ac"].append(y["Q_ac"])

    return {
        "time": times,
        "x": x_hist,
        "y": y_hist,
    }
