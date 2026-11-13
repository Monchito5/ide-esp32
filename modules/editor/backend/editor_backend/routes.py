# Archivo: modules/editor/backend/editor_backend/routes.py
"""Rutas API del modulo Editor (Equipo Rojo)."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from editor_backend.controllers.config_controller import (
    actualizar_configuracion,
    obtener_configuracion,
)
from editor_backend.controllers.format_controller import formatear_codigo_cpp
from editor_backend.controllers.search_controller import (
    buscar_en_archivos,
    reemplazar_en_archivos,
)
from ide_core.config.constants import PREFIJO_API

router = APIRouter(prefix=f"{PREFIJO_API}/editor", tags=["editor"])


class SolicitudFormato(BaseModel):
    codigo: str
    tab_size: int = Field(default=2, ge=1, le=8)


class SolicitudBusquedaArchivos(BaseModel):
    termino: str
    directorio: Optional[str] = None
    sensible_mayusculas: bool = False
    palabra_completa: bool = False


class SolicitudReemplazoArchivos(BaseModel):
    termino: str
    reemplazo: str
    directorio: Optional[str] = None
    sensible_mayusculas: bool = False


class SolicitudConfiguracion(BaseModel):
    tamanio_fuente: Optional[int] = None
    tamanio_tabulacion: Optional[int] = None
    usar_espacios: Optional[bool] = None
    resaltado_sintaxis: Optional[bool] = None
    auto_formato_guardar: Optional[bool] = None
    tema_editor: Optional[str] = None


@router.post("/formato", summary="Formatear código C/C++/Arduino")
def api_formatear(peticion: SolicitudFormato) -> dict:
    return formatear_codigo_cpp(peticion.codigo, peticion.tab_size)


@router.post("/buscar-archivos", summary="Buscar en archivos del proyecto")
def api_buscar_archivos(peticion: SolicitudBusquedaArchivos) -> dict:
    return buscar_en_archivos(
        peticion.termino,
        peticion.directorio,
        peticion.sensible_mayusculas,
        peticion.palabra_completa,
    )


@router.post("/reemplazar-archivos", summary="Reemplazar en archivos del proyecto")
def api_reemplazar_archivos(peticion: SolicitudReemplazoArchivos) -> dict:
    return reemplazar_en_archivos(
        peticion.termino,
        peticion.reemplazo,
        peticion.directorio,
        peticion.sensible_mayusculas,
    )


@router.get("/configuracion", summary="Obtener configuración del editor")
def api_obtener_config() -> dict:
    return obtener_configuracion()


@router.put("/configuracion", summary="Actualizar configuración del editor")
def api_actualizar_config(peticion: SolicitudConfiguracion) -> dict:
    datos = {k: v for k, v in peticion.dict().items() if v is not None}
    return actualizar_configuracion(datos)
