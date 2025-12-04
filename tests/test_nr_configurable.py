import math

from vscsim.solver.nr import newton_raphson


def _residual_scalar(x, y, params, inputs):
    """Problema escalar no lineal: y^2 - 2 = 0."""
    val = list(y.values())[0]
    return {"y": val * val - 2.0}


def _jacobian_scalar(x, y, params, inputs):
    val = list(y.values())[0]
    # dg/dy = 2y
    return [[2.0 * val]]


def test_newton_raphson_default_config_converges():
    x = {}
    y0 = {"y": 1.0}
    params = {}
    inputs = {}

    y_sol, n_iter = newton_raphson(
        x=x,
        y0=y0,
        residual=_residual_scalar,
        jacobian=_jacobian_scalar,
        params=params,
        inputs=inputs,
    )

    assert n_iter > 0
    y_val = y_sol["y"]
    assert math.isclose(y_val, math.sqrt(2.0), rel_tol=1e-6, abs_tol=1e-6)


def test_newton_raphson_respects_nr_max_iter_and_nr_tol():
    x = {}
    y0 = {"y": 10.0}
    inputs = {}

    params_few = {
        "nr_max_iter": 2,
        "nr_tol": 1e-12,
    }
    _, n_iter_few = newton_raphson(
        x=x,
        y0=y0,
        residual=_residual_scalar,
        jacobian=_jacobian_scalar,
        params=params_few,
        inputs=inputs,
    )

    params_many = {
        "nr_max_iter": 10,
        "nr_tol": 1e-12,
    }
    _, n_iter_many = newton_raphson(
        x=x,
        y0=y0,
        residual=_residual_scalar,
        jacobian=_jacobian_scalar,
        params=params_many,
        inputs=inputs,
    )

    assert n_iter_many >= n_iter_few


def test_newton_raphson_logger_is_called():
    x = {}
    y0 = {"y": 1.0}
    params = {"nr_max_iter": 3}
    inputs = {}

    calls = []

    def logger(info):
        calls.append(info)

    newton_raphson(
        x=x,
        y0=y0,
        residual=_residual_scalar,
        jacobian=_jacobian_scalar,
        params=params,
        inputs=inputs,
        logger=logger,
    )

    assert len(calls) >= 1
    for entry in calls:
        assert "iter" in entry
        assert "res_norm" in entry
        assert "y" in entry
