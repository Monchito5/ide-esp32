# Archivo: modules/archivo/backend/archivo_backend/modulo.py
"""
Punto de entrada publico del modulo Archivo.

El core lo importa como:
    from archivo_backend.modulo import registrar
"""

from fastapi import FastAPI
from archivo_backend.router import router

NOMBRE_MODULO = "archivo"
VERSION_MODULO = "1.0.0"


def registrar(app: FastAPI) -> None:
    """Registra las rutas del modulo en la app del IDE."""
    app.include_router(router)
