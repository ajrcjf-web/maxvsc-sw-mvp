"""
Implementación del solver Newton–Raphson para las variables algebraicas y.

Resuelve:
    g(x_k, y) = 0 → y_{k+1}

Reglas (ETU v1.3, ENG-1.0):
- x se mantiene fijo durante NR.
- No se deriva la saturación.
- v_conv_d y v_conv_q se consideran constantes dentro del NR.
- Se utiliza exclusivamente g(x, y) y el Jacobiano respecto a y, dg/dy.

Este módulo implementa únicamente el algoritmo NR; no modifica el modelo
eléctrico ni la formulación DAE.
"""

from typing import Mapping, Callable, Tuple

from vscsim.model.variables import ALGEBRAIC_KEYS


# Firma conceptual de las funciones de residual y Jacobiano
ResidualFunc = Callable[
    [
        Mapping[str, float],  # x
        Mapping[str, float],  # y
        Mapping[str, float] | None,  # params
        Mapping[str, float] | None,  # inputs
    ],
    dict,
]

JacobianFunc = Callable[
    [
        Mapping[str, float],  # x
        Mapping[str, float],  # y
        Mapping[str, float] | None,  # params
        Mapping[str, float] | None,  # inputs
    ],
    list[list[float]],
]


# Parámetros numéricos mínimos (no forman parte de la ingeniería, solo NR básico)
_DEFAULT_MAX_ITER = 20
_DEFAULT_TOL = 1e-8


def _max_norm(vec: list[float]) -> float:
    """Norma infinito (máximo valor absoluto) de un vector."""
    return max((abs(v) for v in vec), default=0.0)


def _solve_linear_system(
    A: list[list[float]],
    b: list[float],
) -> list[float]:
    """
    Resuelve el sistema lineal A * x = b mediante eliminación gaussiana
    con pivotado parcial sencillo.

    Esta función es genérica y no modifica el modelo ni la formulación
    matemática; solo implementa el paso algebraico requerido por NR.
    """
    n = len(b)

    # Copias locales para no modificar los argumentos de entrada
    M = [row[:] for row in A]
    rhs = b[:]

    # Eliminación hacia adelante
    for k in range(n):
        # Búsqueda de pivote
        pivot_row = max(range(k, n), key=lambda i: abs(M[i][k]))
        pivot_val = M[pivot_row][k]

        if abs(pivot_val) == 0.0:
            raise ValueError("Jacobian is singular in Newton–Raphson step.")

        # Intercambio de filas si es necesario
        if pivot_row != k:
            M[k], M[pivot_row] = M[pivot_row], M[k]
            rhs[k], rhs[pivot_row] = rhs[pivot_row], rhs[k]

        # Eliminación
        for i in range(k + 1, n):
            factor = M[i][k] / M[k][k]
            rhs[i] -= factor * rhs[k]
            for j in range(k, n):
                M[i][j] -= factor * M[k][j]

    # Sustitución hacia atrás
    x = [0.0] * n
    for i in reversed(range(n)):
        s = rhs[i]
        for j in range(i + 1, n):
            s -= M[i][j] * x[j]
        x[i] = s / M[i][i]

    return x


def newton_raphson(
    x: Mapping[str, float],
    y0: Mapping[str, float],
    residual: ResidualFunc,
    jacobian: JacobianFunc,
    params: Mapping[str, float] | None = None,
    inputs: Mapping[str, float] | None = None,
) -> Tuple[dict, int]:
    """
    Ejecuta el lazo NR para resolver g(x, y) = 0 con x fijo.

    Parámetros
    ----------
    x :
        Estados dinámicos x_k en el instante actual (id, iq, Vdc).
        Se consideran constantes durante toda la iteración NR.

    y0 :
        Valor inicial de las variables algebraicas y (Idc, P_ac, Q_ac).

    residual :
        Función que implementa g(x, y), devolviendo un dict con las
        mismas claves que y (por ejemplo: "Idc", "P_ac", "Q_ac").

    jacobian :
        Función que implementa dg/dy, devolviendo una matriz cuadrada
        (lista de listas) en el orden de ALGEBRAIC_KEYS.

    params :
        Parámetros del sistema. Se pasan directamente a residual y
        jacobian. Pueden ser None si no se requieren.

    inputs :
        Entradas algebraicas (por ejemplo tensiones), constantes durante
        NR. Se pasan directamente a residual y jacobian. Pueden ser None.

    Retorno
    -------
    y_nr : dict
        Solución de las variables algebraicas tras NR.

    n_iter : int
        Número de iteraciones realizadas.

    Notas
    -----
    - El orden de las variables algebraicas se fija por ALGEBRAIC_KEYS,
      que debe ser coherente con g(x, y) y dg/dy.
    - La implementación respeta la estructura g(x, y) = 0 y utiliza
      exclusivamente información de f/g y sus Jacobianos.
    - No se altera el modelo eléctrico ni la formulación de la ETU v1.3.
    """
    # Copias locales para no modificar referencias de entrada
    y = dict(y0)
    params_local = params or {}
    inputs_local = inputs or {}

    max_iter = _DEFAULT_MAX_ITER
    tol = _DEFAULT_TOL

    # Orden de variables algebraicas fijado por el baseline
    keys = list(ALGEBRAIC_KEYS)

    n_iter = 0

    for k in range(max_iter):
        # Evaluar residual g(x, y)
        g = residual(x, y, params_local, inputs_local)

        # Comprobación básica de consistencia de claves
        if set(g.keys()) != set(keys):
            raise ValueError(
                "Residual keys do not match ALGEBRAIC_KEYS in Newton–Raphson."
            )

        r_vec = [g[key] for key in keys]

        # Criterio de convergencia
        norm_r = _max_norm(r_vec)
        if norm_r < tol:
            n_iter = k
            return y, n_iter

        # Evaluar Jacobiano dg/dy
        J = jacobian(x, y, params_local, inputs_local)

        if len(J) != len(keys) or any(len(row) != len(keys) for row in J):
            raise ValueError("Jacobian size does not match ALGEBRAIC_KEYS in NR.")

        # Resolver J * Δy = -g
        rhs = [-val for val in r_vec]
        delta = _solve_linear_system(J, rhs)

        # Actualizar y
        for i, key in enumerate(keys):
            y[key] = y[key] + delta[i]

        n_iter = k + 1

    # Si se alcanza max_iter sin converger, se devuelve el último y y el nº de iteraciones
    return y, n_iter
