# Archivo: modules/editor/backend/editor_backend/modulo.py
"""
Punto de entrada publico del modulo Editor (Equipo Rojo).

El core lo importa como:
    from editor_backend.modulo import registrar
"""

from fastapi import FastAPI

from editor_backend.routes import router

NOMBRE_MODULO = "editor"
VERSION_MODULO = "1.0.0"


def registrar(app: FastAPI) -> None:
    """Registra las rutas del modulo en la app del IDE."""
    app.include_router(router)
