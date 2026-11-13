# Archivo: modules/simulacion/backend/simulacion_backend/modulo.py
"""
Punto de entrada publico del modulo Simulacion.

El core lo importa como:
    from simulacion_backend.modulo import registrar
"""

from fastapi import FastAPI
from simulacion_backend.routes import router

NOMBRE_MODULO = "simulacion"
VERSION_MODULO = "1.0.0"


def registrar(app: FastAPI) -> None:
    """Registra las rutas del modulo en la app del IDE."""
    app.include_router(router)
