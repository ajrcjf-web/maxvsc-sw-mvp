# tests/test_cli_main.py
"""
Tests de la CLI extendida vscsim.cli.main

No ejecutan la ingeniería real: se usa monkeypatch para reemplazar
run_simulation y las funciones de export.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vscsim.cli import main as cli_main


def _write_json(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_cli_passes_integrator_and_nr_params(monkeypatch, tmp_path):
    """
    Verifica que la CLI:
    - Pasa integrator y adaptive a run_simulation().
    - Inyecta parámetros NR en params_config.
    - Configura el logger (no comprobamos la salida, solo que no rompe).
    """
    # Archivos mínimos de entrada
    params_data = {}  # dict que hará de params_config
    scenario_data = {}  # dict que hará de scenario_config

    params_path = _write_json(tmp_path, "params.json", params_data)
    scenario_path = _write_json(tmp_path, "scenario.json", scenario_data)

    captured = {}

    def fake_run_simulation(
        *,
        params_config,
        scenario_config,
        t_end,
        dt,
        integrator,
        adaptive,
    ):
        captured["params_config"] = params_config
        captured["scenario_config"] = scenario_config
        captured["t_end"] = t_end
        captured["dt"] = dt
        captured["integrator"] = integrator
        captured["adaptive"] = adaptive
        # Resultado mínimo compatible con export
        return {
            "time": [0.0, 0.1],
            "x": [{"id": 1.0, "iq": 0.0, "Vdc": 1.0}],
            "y": [{"Idc": 0.0, "P_ac": 0.0, "Q_ac": 0.0}],
        }

    # Monkeypatch de run_simulation para no ejecutar ingeniería real
    monkeypatch.setattr(
        "vscsim.cli.main.run_simulation",
        fake_run_simulation,
    )

    # Monkeypatch del logger global para que no haga nada visible
    def fake_configure_logger_from_config(config):
        return None

    monkeypatch.setattr(
        "vscsim.cli.main.configure_global_logger_from_config",
        fake_configure_logger_from_config,
    )

    argv = [
        "--params",
        str(params_path),
        "--scenario",
        str(scenario_path),
        "--t-end",
        "0.2",
        "--dt",
        "0.01",
        "--integrator",
        "rk2",
        "--adaptive",
        "--nr-tol",
        "1e-5",
        "--nr-max-iter",
        "15",
        "--nr-norm",
        "l2",
        "--nr-verbose",
        "--log-level",
        "debug",
    ]

    exit_code = cli_main.main(argv)
    assert exit_code == 0

    # Comprobaciones sobre lo que recibió fake_run_simulation
    assert captured["integrator"] == "rk2"
    assert captured["adaptive"] is True
    assert captured["t_end"] == pytest.approx(0.2)
    assert captured["dt"] == pytest.approx(0.01)

    params_config = captured["params_config"]
    # NR inyectado por CLI
    assert params_config["nr_tol"] == pytest.approx(1e-5)
    assert params_config["nr_max_iter"] == 15
    assert params_config["nr_norm"] == "l2"
    assert params_config["nr_verbose"] is True


def test_cli_export_csv_calls_exporter(monkeypatch, tmp_path):
    """
    Verifica que la CLI llama a export_simulation_csv cuando se usa
    --export csv y --output.
    """
    params_path = _write_json(tmp_path, "params.json", {})
    scenario_path = _write_json(tmp_path, "scenario.json", {})

    def fake_run_simulation(**kwargs):
        return {
            "time": [0.0, 0.1],
            "x": [{"id": 1.0}, {"id": 0.9}],
            "y": [{"Idc": 0.0}, {"Idc": 0.1}],
        }

    called = {}

    def fake_export_csv(times, x_hist, y_hist, path, config):
        called["times"] = times
        called["x_hist"] = x_hist
        called["y_hist"] = y_hist
        called["path"] = path

    monkeypatch.setattr("vscsim.cli.main.run_simulation", fake_run_simulation)
    monkeypatch.setattr(
        "vscsim.cli.main.export_simulation_csv",
        fake_export_csv,
    )

    out_path = tmp_path / "out.csv"

    argv = [
        "--params",
        str(params_path),
        "--scenario",
        str(scenario_path),
        "--export",
        "csv",
        "--output",
        str(out_path),
    ]

    exit_code = cli_main.main(argv)
    assert exit_code == 0

    assert called["path"] == str(out_path)
    assert called["times"] == [0.0, 0.1]
    assert len(called["x_hist"]) == 2
    assert len(called["y_hist"]) == 2


def test_cli_export_requires_output(monkeypatch, tmp_path):
    """
    Verifica que la CLI exige --output cuando se usa --export != none.
    """
    params_path = _write_json(tmp_path, "params.json", {})
    scenario_path = _write_json(tmp_path, "scenario.json", {})

    def fake_run_simulation(**kwargs):
        return {
            "time": [0.0, 0.1],
            "x": [{"id": 1.0}],
            "y": [{"Idc": 0.0}],
        }

    monkeypatch.setattr("vscsim.cli.main.run_simulation", fake_run_simulation)

    argv = [
        "--params",
        str(params_path),
        "--scenario",
        str(scenario_path),
        "--export",
        "csv",
        # Sin --output → debe fallar con SystemExit(2)
    ]

    with pytest.raises(SystemExit) as excinfo:
        cli_main.main(argv)

    assert excinfo.value.code == 2
