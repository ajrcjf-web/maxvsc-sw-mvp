# tests/test_imports.py
"""
Pruebas básicas de importación de módulos.

Verifica que la arquitectura de paquetes es coherente y que las
funciones clave existen.
"""

import importlib


def test_import_model_modules():
    modules = [
        "vscsim.model.variables",
        "vscsim.model.dae",
        "vscsim.model.jacobian",
    ]
    for name in modules:
        importlib.import_module(name)
    print("[SUMMARY] test_import_model_modules: imported", modules)


def test_import_solver_modules():
    modules = [
        "vscsim.solver.nr",
        "vscsim.solver.integrator",
        "vscsim.solver.simulation",
    ]
    for name in modules:
        importlib.import_module(name)
    print("[SUMMARY] test_import_solver_modules: imported", modules)


def test_import_vsc_modules():
    modules = [
        "vscsim.vsc.control_external",
        "vscsim.vsc.control_inner",
        "vscsim.vsc.saturation",
    ]
    for name in modules:
        importlib.import_module(name)
    print("[SUMMARY] test_import_vsc_modules: imported", modules)


def test_import_io_api_cli():
    modules = [
        "vscsim.io.parameters",
        "vscsim.io.scenario",
        "vscsim.io.initial_conditions",
        "vscsim.api.simulation",
        "vscsim.cli.main",
    ]
    for name in modules:
        importlib.import_module(name)
    print("[SUMMARY] test_import_io_api_cli: imported", modules)
