import math

from vscsim.solver.timestepper import AdaptiveTimestepper


def test_adaptive_timestepper_grows_when_error_small():
    ts = AdaptiveTimestepper(
        dt=0.1,
        dt_min=0.01,
        dt_max=1.0,
        safety=0.9,
        growth_factor_max=2.0,
        shrink_factor_min=0.5,
        order=2.0,
    )

    dt_initial = ts.current_dt()
    # Error muy pequeño comparado con la tolerancia → debe crecer
    new_dt = ts.update(error_estimate=1e-8, tol=1e-3)

    assert new_dt > dt_initial
    assert new_dt <= ts.dt_max


def test_adaptive_timestepper_shrinks_when_error_large():
    ts = AdaptiveTimestepper(
        dt=0.1,
        dt_min=0.01,
        dt_max=1.0,
        safety=0.9,
        growth_factor_max=2.0,
        shrink_factor_min=0.5,
        order=2.0,
    )

    dt_initial = ts.current_dt()
    # Error mucho mayor que la tolerancia → debe reducir dt
    new_dt = ts.update(error_estimate=1e-1, tol=1e-3)

    assert new_dt < dt_initial
    assert new_dt >= ts.dt_min


def test_adaptive_timestepper_clamps_to_bounds():
    ts = AdaptiveTimestepper(
        dt=0.5,
        dt_min=0.1,
        dt_max=0.6,
        safety=0.9,
        growth_factor_max=2.0,
        shrink_factor_min=0.5,
        order=2.0,
    )

    # Forzamos crecimiento hacia arriba repetidamente
    for _ in range(5):
        ts.update(error_estimate=1e-9, tol=1e-3)

    assert math.isclose(ts.current_dt(), ts.dt_max, rel_tol=0.0, abs_tol=1e-12)

    # Ahora forzamos reducción fuerte de error (al revés: error grande)
    for _ in range(5):
        ts.update(error_estimate=1.0, tol=1e-3)

    assert math.isclose(ts.current_dt(), ts.dt_min, rel_tol=0.0, abs_tol=1e-12)
