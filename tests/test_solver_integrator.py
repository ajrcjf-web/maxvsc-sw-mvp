# tests/test_solver_integrator.py
"""
Pruebas del integrador Euler explícito.
"""

import pytest
from vscsim.solver.integrator import step_forward


def test_integrator_euler_constant_derivative():
    x = {"id": 0.0, "iq": 0.0, "Vdc": 0.0}
    x_dot = {"id": 1.0, "iq": 2.0, "Vdc": 3.0}
    dt = 0.1

    x_next = step_forward(x, x_dot, dt)

    assert x_next["id"] == pytest.approx(0.1)
    assert x_next["iq"] == pytest.approx(0.2)
    assert x_next["Vdc"] == pytest.approx(0.3)

    print("[SUMMARY] test_integrator_euler_constant_derivative: "
          f"x_next={x_next}, dt={dt}")
