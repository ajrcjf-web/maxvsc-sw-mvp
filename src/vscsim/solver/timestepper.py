"""
vscsim.solver.timestepper

Lógica de paso de tiempo adaptativo (dt_adaptativo) para el framework numérico.

No modifica el modelo RMS ni la DAE; solo calcula el siguiente dt a partir
de un error estimado y una tolerancia objetivo.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdaptiveTimestepper:
    """
    Gestor de paso de tiempo adaptativo.

    La regla está pensada para integradores de orden ~2 (por ejemplo RK2),
    pero es genérica: recibe un error estimado y ajusta dt dentro de
    [dt_min, dt_max].

    Modelo de ajuste (simplificado):

        error ~ dt^p,   con p ≈ 2

        factor ≈ (tol / error)^(1/p)

    con límites en el factor de crecimiento/disminución y un factor de
    seguridad para evitar oscilaciones fuertes.
    """

    dt: float
    dt_min: float
    dt_max: float
    safety: float = 0.9
    growth_factor_max: float = 2.0
    shrink_factor_min: float = 0.5
    order: float = 2.0  # orden efectivo asumido del integrador (RK2 ~ 2)

    def current_dt(self) -> float:
        """Devuelve el dt actual."""
        return self.dt

    def clamp_dt(self) -> float:
        """Aplica límites dt_min/dt_max al dt actual."""
        self.dt = max(self.dt_min, min(self.dt_max, self.dt))
        return self.dt

    def update(self, error_estimate: float, tol: float) -> float:
        """
        Actualiza dt en función de un error estimado y una tolerancia.

        Parameters
        ----------
        error_estimate :
            Estimación escalar del error local del paso actual.
            Debe ser >= 0.
        tol :
            Tolerancia objetivo (típicamente pequeña y > 0).

        Returns
        -------
        float
            Nuevo dt después del ajuste y del clamp [dt_min, dt_max].

        Notas
        -----
        - Si error_estimate <= 0, se asume error muy pequeño y se intenta
          incrementar dt hasta el límite superior permitido.
        - Si error_estimate >> tol, dt se reduce.
        - Si error_estimate ≈ tol, dt se mantiene aproximadamente.
        """
        if tol <= 0.0:
            raise ValueError("tol must be > 0.0")

        if error_estimate < 0.0:
            raise ValueError("error_estimate must be >= 0.0")

        # Caso "error ~ 0": aumentar dt lo máximo posible dentro de límites.
        if error_estimate == 0.0:
            factor = self.growth_factor_max
        else:
            # factor ~ (tol / error)^(1/p)
            ratio = tol / error_estimate
            ratio = max(1e-12, min(1e12, ratio))
            factor = self.safety * (ratio ** (1.0 / self.order))

        factor = max(self.shrink_factor_min, min(self.growth_factor_max, factor))

        self.dt *= factor
        return self.clamp_dt()
