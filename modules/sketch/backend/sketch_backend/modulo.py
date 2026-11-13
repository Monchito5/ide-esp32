"""Punto de entrada del modulo Sketch."""

from fastapi import FastAPI

from sketch_backend.routes import router

NOMBRE_MODULO = "sketch"
VERSION_MODULO = "1.0.0"


def registrar(app: FastAPI) -> None:
    """Registra las rutas del modulo Sketch en la aplicacion principal."""
    app.include_router(router)
