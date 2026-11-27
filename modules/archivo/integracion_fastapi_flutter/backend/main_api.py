"""
Punto de entrada FastAPI para integrar el módulo Archivo con el frontend en Flutter.
Ejecución opcional (si se usa modo servidor):
    uvicorn integracion_fastapi_flutter.backend.main_api:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app.modules.archivo.router import router as archivo_router

app = FastAPI(
    title="ESP32 IDE Backend - Módulo Archivo",
    version="1.0.0",
    description="API del módulo Archivo para integración con Flutter y demás módulos del ESP32 IDE.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(archivo_router)

