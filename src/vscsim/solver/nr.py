"""
vscsim.solver.nr

Implementación del método de Newton–Raphson sobre las ecuaciones
algebraicas g(x, y) = 0, utilizando únicamente la Jacobiana dg/dy.

Este módulo forma parte del framework numérico y no modifica la
ingeniería del modelo RMS ni la definición de g(x, y) en la ETU v1.3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Tuple, Protocol, List


class ResidualFunc(Protocol):
    """
    Firma de la función de residuo g(x, y).

    Parameters
    ----------
    x :
        Estados dinámicos actuales.
    y :
        Variables algebraicas actuales.
    params :
        Parámetros eléctricos / de control.
    inputs :
        Entradas algebraicas (por ejemplo tensiones, consignas, etc.).

    Returns
    -------
    Mapping[str, float]
        Residuo g(x, y) indexado por las mismas claves que y.
    """

    def __call__(
        self,
        x: Mapping[str, float],
        y: Mapping[str, float],
        params: Mapping[str, float] | None,
        inputs: Mapping[str, float] | None,
    ) -> Mapping[str, float]:
        ...


class JacobianFunc(Protocol):
    """
    Firma de la función de Jacobiana dg/dy.

    Devuelve una matriz en forma de lista de listas, consistente con
    el orden de las claves de y.
    """

    def __call__(
        self,
        x: Mapping[str, float],
        y: Mapping[str, float],
        params: Mapping[str, float] | None,
        inputs: Mapping[str, float] | None,
    ) -> List[List[float]]:
        ...


@dataclass
class NRConfig:
    """
    Configuración opcional del solver de Newton–Raphson.

    Estos parámetros forman parte del framework numérico (Track A1.3)
    y no alteran la formulación de g(x, y) ni la ingeniería de ENG-1.0.
    """

    tol: float = 1e-8
    max_iter: int = 20
    norm: str = "max"  # "max" o "l2"
    verbose: bool = False


def _vector_norm(values: Mapping[str, float], kind: str = "max") -> float:
    """Norma de un vector representado como dict."""
    if not values:
        return 0.0

    if kind == "l2":
        s = 0.0
        for v in values.values():
            s += float(v) * float(v)
        return s ** 0.5

    # Norma infinito ("max")
    m = 0.0
    for v in values.values():
        av = abs(float(v))
        if av > m:
            m = av
    return m


def _solve_linear_system(jac: List[List[float]], res: List[float]) -> List[float]:
    """
    Resuelve J * delta = -res mediante eliminación gaussiana simple.

    No depende de librerías externas y está pensado para sistemas
    pequeños (como el g(x, y) del MVP: Idc, P_ac, Q_ac).
    """
    n = len(res)
    # Matriz aumentada [J | -res]
    aug = [list(row) + [-res[i]] for i, row in enumerate(jac)]

    # Eliminación hacia adelante
    for k in range(n):
        pivot = aug[k][k]
        if pivot == 0.0:
            raise ZeroDivisionError("Pivot cero en eliminación gaussiana (Jacobiana singular).")

        inv_pivot = 1.0 / pivot
        for j in range(k, n + 1):
            aug[k][j] *= inv_pivot

        for i in range(k + 1, n):
            factor = aug[i][k]
            if factor == 0.0:
                continue
            for j in range(k, n + 1):
                aug[i][j] -= factor * aug[k][j]

    # Sustitución hacia atrás
    delta = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = 0.0
        for j in range(i + 1, n):
            s += aug[i][j] * delta[j]
        delta[i] = aug[i][n] - s

    return delta


def newton_raphson(
    x: Mapping[str, float],
    y0: Mapping[str, float],
    residual: ResidualFunc,
    jacobian: JacobianFunc,
    params: Mapping[str, float] | None = None,
    inputs: Mapping[str, float] | None = None,
    *,
    tol: float | None = None,
    max_iter: int | None = None,
    norm: str | None = None,
    logger: Callable[[dict[str, Any]], None] | None = None,
) -> Tuple[dict[str, float], int]:
    """
    Resuelve g(x, y) = 0 respecto a y usando Newton–Raphson clásico.

    Devuelve:
        y      : solución encontrada (o último valor si no converge),
        n_iter : número de iteraciones realizadas.

    Se mantiene compatibilidad con la API original (segundo return = int),
    añadiendo solo configuración opcional vía params/kwargs y logging.
    """
    # ----------------------------
    # Lectura de configuración NR
    # ----------------------------
    cfg = NRConfig()
    if params is not None:
        if "nr_tol" in params:
            cfg.tol = float(params["nr_tol"])
        if "nr_max_iter" in params:
            cfg.max_iter = int(params["nr_max_iter"])
        if "nr_norm" in params:
            cfg.norm = str(params["nr_norm"])
        if "nr_verbose" in params:
            cfg.verbose = bool(params["nr_verbose"])

    if tol is not None:
        cfg.tol = float(tol)
    if max_iter is not None:
        cfg.max_iter = int(max_iter)
    if norm is not None:
        cfg.norm = str(norm)

    # ----------------------------
    # Bucle de Newton–Raphson
    # ----------------------------
    y = dict(y0)
    keys = list(y.keys())

    n_iter = 0

    for it in range(cfg.max_iter):
        g_val = residual(x, y, params, inputs)
        res_norm = _vector_norm(g_val, kind=cfg.norm)

        n_iter = it + 1

        if logger is not None:
            logger({
                "iter": it,
                "res_norm": res_norm,
                "y": dict(y),
            })

        if res_norm <= cfg.tol:
            break

        # Jacobiana y actualización
        j_mat = jacobian(x, y, params, inputs)
        r_vec = [float(g_val[k]) for k in keys]

        # J * delta = -g  → delta = -J^{-1} g
        delta_vec = _solve_linear_system(j_mat, r_vec)

        for k, key in enumerate(keys):
            y[key] = float(y[key]) + delta_vec[k]

        if cfg.verbose and logger is None:
            print(f"[NR] iter={it} res_norm={res_norm:.3e}")

    return y, n_iter
