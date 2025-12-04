from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse

from . import io
from .schemas import RunInfo, SignalList, TimeSeriesResponse

app = FastAPI(
    title="MaxVSC Dashboard API",
    description="Backend ligero para visualizar resultados de MaxVSC-SW.",
    version="0.1.0",
)


@app.get("/health", response_model=dict)
def health():
    return {"status": "ok"}


@app.get("/", response_class=PlainTextResponse)
def root():
    return (
        "MaxVSC Dashboard API\n"
        "\n"
        "Endpoints principales:\n"
        "  GET /health\n"
        "  GET /runs\n"
        "  GET /runs/{run_id}/signals\n"
        "  GET /runs/{run_id}/timeseries?signals=col1,col2\n"
    )


@app.get("/runs", response_model=List[RunInfo])
def list_runs():
    """
    Lista todos los runs disponibles.

    Usamos como `id` el nombre del fichero sin extensión (build_run_id),
    y devolvemos la ruta completa del fichero en `path`.
    """
    runs: List[RunInfo] = []
    for run_id, path in io.list_runs():
        runs.append(
            RunInfo(
                id=run_id,
                name=path.name,
                path=str(path),
            )
        )
    return runs


@app.get("/runs/{run_id}/signals", response_model=SignalList)
def get_signals(run_id: str):
    try:
        path = io.find_run_csv(run_id)  # puede ser CSV o Parquet
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run_id not found")

    sigs = io.list_signals(path)
    return SignalList(time_column="time", signals=sigs)


@app.get("/runs/{run_id}/timeseries", response_model=TimeSeriesResponse)
def get_timeseries(
    run_id: str,
    signals: str = Query(
        "",
        description="Lista de señales separadas por comas; "
        "si se deja vacío, se devuelven todas.",
    ),
):
    try:
        path = io.find_run_csv(run_id)  # puede ser CSV o Parquet
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run_id not found")

    times, all_signals = io.load_timeseries(path)

    if not times:
        return TimeSeriesResponse(time=[], signals={})

    if signals:
        requested = [s.strip() for s in signals.split(",") if s.strip()]
        missing = [s for s in requested if s not in all_signals]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Señales no encontradas en fichero: {missing}",
            )
        filtered = {k: all_signals[k] for k in requested}
    else:
        filtered = all_signals

    return TimeSeriesResponse(time=times, signals=filtered)
