from __future__ import annotations

import csv
from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard import config


client = TestClient(app)


def _write_sample_csv(tmpdir: Path) -> str:
    """
    Crea un CSV simple con columnas: time, id, iq.
    Devuelve el run_id esperado (coherente con build_run_id).
    """
    outputs = tmpdir / "outputs" / "advanced"
    outputs.mkdir(parents=True, exist_ok=True)

    path = outputs / "sample_case.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "id", "iq"])
        for i in range(5):
            writer.writerow([0.1 * i, i * 1.0, i * 2.0])

    # build_run_id(path) -> "sample_case"
    return "sample_case"


def test_dashboard_endpoints(tmp_path, monkeypatch):
    # Configuramos el DATA_DIR para que apunte al tmp
    data_dir = tmp_path / "outputs"
    monkeypatch.setenv("MAXVSC_DASHBOARD_DATA_DIR", str(data_dir))

    # Forzamos recálculo del DATA_DIR en config
    import importlib

    importlib.reload(config)

    run_id = _write_sample_csv(tmp_path)

    # /health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # /runs
    r = client.get("/runs")
    assert r.status_code == 200
    runs = r.json()
    assert any(item["id"] == run_id for item in runs)

    # /runs/{run_id}/signals
    r = client.get(f"/runs/{run_id}/signals")
    assert r.status_code == 200
    sigs = r.json()
    assert sigs["time_column"] == "time"
    assert set(sigs["signals"]) == {"id", "iq"}

    # /runs/{run_id}/timeseries
    r = client.get(f"/runs/{run_id}/timeseries?signals=id,iq")
    assert r.status_code == 200
    ts = r.json()
    assert len(ts["time"]) == 5
    assert len(ts["signals"]["id"]) == 5
    assert len(ts["signals"]["iq"]) == 5
