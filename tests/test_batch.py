"""
Tests para vscsim.api.batch

No se ejecuta ingeniería real:
- Se monkeypatchea run_simulation para simular resultados
- Se validan secuencial y paralelo
"""

from __future__ import annotations

import pytest

from vscsim.api.batch import (
    BatchCase,
    BatchResult,
    run_batch,
)


def test_batch_sequential(monkeypatch):
    """
    Verifica:
    - run_batch() secuencial ejecuta todos los casos
    - respeta integrador/flags
    - produce BatchResult por caso
    """
    captured = []

    def fake_run_simulation(**kwargs):
        captured.append(kwargs)
        return {
            "time": [0.0, 0.1],
            "x": [{"id": 1.0}],
            "y": [{"Idc": 0.0}],
        }

    monkeypatch.setattr("vscsim.api.batch.run_simulation", fake_run_simulation)

    cases = [
        BatchCase(
            id="A",
            params_config={"p": 1},
            scenario_config={"s": 1},
            integrator="rk1",
            adaptive=False,
            t_end=0.2,
            dt=0.01,
        ),
        BatchCase(
            id="B",
            params_config={"p": 2},
            scenario_config={"s": 2},
            integrator="rk4",
            adaptive=True,
            t_end=0.5,
            dt=0.001,
        ),
    ]

    results = run_batch(cases, parallel=False)

    assert len(results) == 2

    # Caso A
    rA = results[0]
    assert rA.id == "A"
    assert rA.ok is True
    assert rA.data["time"] == [0.0, 0.1]

    # Caso B
    rB = results[1]
    assert rB.id == "B"
    assert rB.ok is True

    # Verifica que run_simulation fue llamado con los datos correctos
    assert captured[0]["integrator"] == "rk1"
    assert captured[0]["adaptive"] is False
    assert captured[1]["integrator"] == "rk4"
    assert captured[1]["adaptive"] is True


def test_batch_failure(monkeypatch):
    """
    Verifica que si un caso falla, produce BatchResult(ok=False).
    """
    def fake_run_simulation(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("vscsim.api.batch.run_simulation", fake_run_simulation)

    cases = [
        BatchCase(
            id="F",
            params_config={},
            scenario_config={},
            integrator="euler",
            adaptive=False,
            t_end=0.1,
            dt=0.01,
        )
    ]

    results = run_batch(cases, parallel=False)

    assert len(results) == 1
    r = results[0]
    assert r.id == "F"
    assert r.ok is False
    assert r.error == "boom"


def test_batch_parallel(monkeypatch):
    """
    Verifica la ruta paralela (multiprocessing).
    Para evitar overhead, se simula con una función trivial.
    """

    def fake_run_simulation(**kwargs):
        return {"time": [0.0], "x": [{}], "y": [{}]}

    monkeypatch.setattr("vscsim.api.batch.run_simulation", fake_run_simulation)

    cases = [
        BatchCase(
            id=str(i),
            params_config={},
            scenario_config={},
            integrator="euler",
            adaptive=False,
            t_end=0.1,
            dt=0.01,
        )
        for i in range(4)
    ]

    # Parallel=True, pero pequeño → debe devolver 4 resultados
    results = run_batch(cases, parallel=True, max_workers=2)

    assert len(results) == 4
    assert all(isinstance(r, BatchResult) for r in results)
