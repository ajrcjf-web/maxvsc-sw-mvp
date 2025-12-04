# Dashboard MaxVSC-SW

Backend ligero basado en FastAPI para explorar resultados de simulación.

## Estructura

- `dashboard/app.py`: aplicación FastAPI.
- `dashboard/io.py`: carga de ficheros CSV.
- `dashboard/config.py`: configuración de directorio de datos.
- `dashboard/main.py`: entrypoint (`python -m dashboard.main`).

## Directorio de datos

Por defecto, el dashboard busca ficheros CSV bajo:

```text
./outputs
