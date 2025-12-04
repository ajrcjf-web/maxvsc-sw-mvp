"""
vscsim.api.batch

Ejecutor batch para múltiples casos de simulación RMS VSC-HVDC.

Objetivos:
- Ejecutar muchos casos en secuencia o paralelo ligero.
- Permitir integrador por caso.
- Devuelve resultados por caso sin alterar run_simulation ni la ingeniería.
"""

from __future__ import annotations

import multiprocessing as mp
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from vscsim.api.simulation import run_simulation


@dataclass
class BatchCase:
    """
    Un caso batch unitario:

    - params_config : dict con parámetros de simulación
    - scenario_config : dict con escenario
    - integrator : "euler", "rk1", "rk2", "rk4"
    - adaptive : bool
    - t_end : float
    - dt : float  (o dt inicial si adaptive=True)
    """

    id: str
    params_config: Mapping[str, Any]
    scenario_config: Mapping[str, Any]
    integrator: str
    adaptive: bool
    t_end: float
    dt: float


@dataclass
class BatchResult:
    """
    Resultado de un caso batch:

    - id : identificador del caso
    - ok : bool (True si la simulación completó sin excepción)
    - data : dict con resultados de run_simulation, o None si falló
    - error : str si falló
    """

    id: str
    ok: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]


def _run_single_case(case: BatchCase) -> BatchResult:
    """
    Ejecuta un caso batch.
    NO altera ingeniería.
    """
    try:
        result = run_simulation(
            params_config=case.params_config,
            scenario_config=case.scenario_config,
            t_end=case.t_end,
            dt=case.dt,
            integrator=case.integrator,
            adaptive=case.adaptive,
        )
        return BatchResult(id=case.id, ok=True, data=result, error=None)

    except Exception as e:
        return BatchResult(id=case.id, ok=False, data=None, error=str(e))


# ---------------------------------------------------------------------
# API pública batch
# ---------------------------------------------------------------------

def run_batch(
    cases: List[BatchCase],
    parallel: bool = False,
    max_workers: int = 4,
) -> List[BatchResult]:
    """
    Ejecuta un conjunto de casos batch.

    Parámetros
    ----------
    cases : list[BatchCase]
        Casos a ejecutar.
    parallel : bool
        Si True, usa multiprocessing simple.
    max_workers : int
        Número de procesos si parallel=True.

    Returns
    -------
    list[BatchResult]
        Un resultado por caso, en el mismo orden del input.
    """
    if not parallel:
        # Modo secuencial sencillo
        results: List[BatchResult] = []
        for case in cases:
            results.append(_run_single_case(case))
        return results

    # Modo paralelo ligero usando multiprocessing
    with mp.Pool(processes=max_workers) as pool:
        results = pool.map(_run_single_case, cases)
    return results
