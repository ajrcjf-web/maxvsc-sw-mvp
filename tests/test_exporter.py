import csv
import os

import pytest

from vscsim.utils.exporter import (
    export_csv,
    export_parquet,
    ExportConfig,
    _pd,  # pandas interno (puede ser None)
)


def test_export_csv_basic(tmp_path):
    """
    Verifica que export_csv escribe un archivo CSV con cabecera y filas correctas.
    """
    rows = [
        {"t": 0.0, "id": 1.0, "iq": 0.0},
        {"t": 0.1, "id": 0.9, "iq": -0.1},
    ]

    out_path = tmp_path / "results.csv"

    export_csv(rows, str(out_path), config=ExportConfig(overwrite=False))

    assert out_path.exists()

    with out_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        read_rows = list(reader)

    # Mismas columnas
    assert reader.fieldnames == ["t", "id", "iq"]

    # Mismos valores (como strings en CSV)
    assert read_rows[0]["t"] == "0.0"
    assert read_rows[0]["id"] == "1.0"
    assert read_rows[0]["iq"] == "0.0"

    assert read_rows[1]["t"] == "0.1"
    assert read_rows[1]["id"] == "0.9"
    assert read_rows[1]["iq"] == "-0.1"


def test_export_csv_overwrite_protection(tmp_path):
    """
    Verifica que export_csv respeta overwrite=False y lanza FileExistsError
    si el archivo ya existe.
    """
    out_path = tmp_path / "results.csv"
    out_path.write_text("preexisting", encoding="utf-8")

    rows = [{"a": 1}]

    with pytest.raises(FileExistsError):
        export_csv(rows, str(out_path), config=ExportConfig(overwrite=False))

    # Con overwrite=True no debe fallar
    export_csv(rows, str(out_path), config=ExportConfig(overwrite=True))
    assert out_path.exists()


@pytest.mark.parametrize("use_engine", [None, "pyarrow"])
def test_export_parquet(tmp_path, use_engine):
    """
    Verifica export_parquet:

    - Si pandas no está disponible, debe lanzar RuntimeError.
    - Si pandas está disponible, se escribe un archivo Parquet legible.
    """
    rows = [
        {"t": 0.0, "id": 1.0},
        {"t": 0.1, "id": 0.9},
    ]

    out_path = tmp_path / "results.parquet"

    if _pd is None:
        # Entorno sin pandas: debe fallar claramente
        with pytest.raises(RuntimeError):
            export_parquet(rows, str(out_path), config=ExportConfig(overwrite=True), engine=use_engine)
        return

    # Entorno con pandas: debe escribir un fichero Parquet válido
    export_parquet(rows, str(out_path), config=ExportConfig(overwrite=True), engine=use_engine)

    assert out_path.exists()
    df = _pd.read_parquet(str(out_path))  # type: ignore[union-attr]
    assert list(df.columns) == ["t", "id"]
    assert len(df) == 2
    assert df["t"].iloc[0] == pytest.approx(0.0)
    assert df["id"].iloc[1] == pytest.approx(0.9)
