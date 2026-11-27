# Archivo: core/backend/ide_core/config/registro_modulos.py
"""Carga y registro de modulos plug-in del IDE."""

import importlib

from fastapi import FastAPI

from ide_core.config.constants import MODULOS_REGISTRADOS
from ide_core.utils.logger import log_sistema


def _obtener_adaptador_sketch():
    """Intenta obtener el adaptador de compilacion ESP-IDF del modulo Sketch."""
    try:
        from sketch_backend.controllers.compilacion import adaptador_compilacion_azul

        return adaptador_compilacion_azul
    except ImportError:
        return None


def registrar_modulos(app: FastAPI) -> None:
    """Importa y registra cada modulo declarado en MODULOS_REGISTRADOS."""
    adaptador_sketch = _obtener_adaptador_sketch()

    for ruta in MODULOS_REGISTRADOS:
        try:
            modulo = importlib.import_module(ruta)
        except ImportError as exc:
            log_sistema.error("Modulo no disponible: %s (%s)", ruta, exc)
            continue

        registrar = getattr(modulo, "registrar", None)
        if not callable(registrar):
            log_sistema.warning("Modulo sin funcion registrar(): %s", ruta)
            continue

        if ruta == "azul_backend.modulo" and adaptador_sketch is not None:
            registrar(app, compile_adapter=adaptador_sketch)
        else:
            registrar(app)
        log_sistema.info("Modulo registrado: %s", ruta)
