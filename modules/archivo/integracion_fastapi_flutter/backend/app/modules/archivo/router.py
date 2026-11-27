"""
Endpoints en FastAPI para el Módulo de Archivo.
Incluye:
1. Recepción de código fuente desde Flutter con UploadFile y preparación en estructura ESP-IDF.
2. Función y endpoint puente para entregar la ruta absoluta del proyecto temporal al compilador "Sketch".
3. Empaquetado de archivos .bin generados y logs de compilación/errores de regreso hacia Flutter.
4. Descarga directa de binarios (.bin) y funciones completas del menú Archivo y proyectos locales.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from .schemas import (
    ArchivoActionResponse,
    BuildAndFilesDeliveryResponse,
    CompilerInputResultRequest,
    CreateProjectFileRequest,
    ESPIDFProjectPreparedResponse,
    OpenFileRequest,
    PreferencesModel,
    SaveFileRequest,
    SketchInfoRequest,
)
from .service import ArchivoService

router = APIRouter(prefix="/api/archivo", tags=["Módulo de Archivo (ESP-IDF & IDE)"])
archivo_service = ArchivoService()


# =============================================================================
# FUNCIÓN PUENTE DIRECTA PARA EL EQUIPO DEL COMPILADOR ("SKETCH")
# =============================================================================
def obtener_ruta_absoluta_para_sketch(project_id: str) -> str:
    """
    Función que el módulo 'Sketch' (compilador ESP-IDF) puede importar y llamar
    directamente en Python para obtener la ruta absoluta del directorio temporal
    donde ya están creados el CMakeLists.txt raíz y la subcarpeta main/.
    """
    return archivo_service.get_project_directory_for_compiler(project_id)


# =============================================================================
# ENDPOINTS PUENTE: FLUTTER <-> MÓDULO ARCHIVO (ESP-IDF) <-> SKETCH / FLASHEO
# =============================================================================
@router.post("/espidf/preparar", response_model=ESPIDFProjectPreparedResponse)
async def preparar_proyecto_espidf(
    project_name: str = Form(default="esp32_sketch", description="Nombre del proyecto ESP-IDF"),
    files: List[UploadFile] = File(
        ..., description="Archivos de código fuente (.c, .cpp, .h, .ino) enviados desde Flutter"
    ),
):
    return await archivo_service.prepare_espidf_project(
        uploaded_files=files,
        project_name=project_name,
    )


@router.get("/espidf/{project_id}/ruta-compilador")
def endpoint_ruta_para_compilador(project_id: str):
    try:
        abs_path = obtener_ruta_absoluta_para_sketch(project_id)
        return {
            "success": True,
            "project_id": project_id,
            "project_absolute_path": abs_path,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/espidf/entregar-resultados", response_model=BuildAndFilesDeliveryResponse)
def entregar_binarios_y_logs_a_flutter(request: CompilerInputResultRequest):
    return archivo_service.collect_build_results_for_flutter(request)


@router.get("/espidf/{project_id}/descargar-bin")
def descargar_archivo_binario(
    project_id: str,
    rel_path: str = Query(..., description="Ruta relativa del archivo .bin dentro del proyecto ESP-IDF"),
):
    try:
        bin_abs_path = archivo_service.resolve_binary_file_path(project_id, rel_path)
        return FileResponse(
            path=bin_abs_path,
            media_type="application/octet-stream",
            filename=os.path.basename(bin_abs_path),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/espidf/{project_id}")
def limpiar_proyecto_temporal(project_id: str):
    removed = archivo_service.cleanup_temp_project(project_id)
    return {"success": removed, "project_id": project_id}


# =============================================================================
# ENDPOINTS DEL MENÚ ARCHIVO LOCAL Y GESTIÓN DE PROYECTOS
# =============================================================================
@router.post("/nuevo", response_model=ArchivoActionResponse)
def endpoint_nuevo_sketch():
    return archivo_service.new_sketch()


@router.post("/abrir", response_model=ArchivoActionResponse)
def endpoint_abrir_archivo(request: OpenFileRequest):
    return archivo_service.open_sketch(request)


@router.post("/guardar", response_model=ArchivoActionResponse)
def endpoint_guardar_archivo(request: SaveFileRequest):
    return archivo_service.save_sketch(request)


@router.post("/cerrar", response_model=ArchivoActionResponse)
def endpoint_cerrar_sketch():
    return archivo_service.close_sketch()


@router.get("/actual", response_model=ArchivoActionResponse)
def endpoint_obtener_proyecto_actual():
    return archivo_service.get_current_project()


@router.get("/proyecto/archivos", response_model=ArchivoActionResponse)
def endpoint_obtener_archivos_proyecto(
    project_path: Optional[str] = Query(
        default=None,
        description="Ruta opcional del proyecto o archivo principal a consultar",
    ),
):
    return archivo_service.get_project_files(project_path=project_path)


@router.post("/proyecto/archivo", response_model=ArchivoActionResponse)
def endpoint_crear_archivo_proyecto(request: CreateProjectFileRequest):
    return archivo_service.create_project_file(request)


@router.get("/submenus", response_model=ArchivoActionResponse)
def endpoint_obtener_submenus():
    return archivo_service.get_submenus_data()


@router.delete("/recientes", response_model=ArchivoActionResponse)
def endpoint_limpiar_recientes():
    return archivo_service.clear_recent_files()


@router.get("/preferencias", response_model=ArchivoActionResponse)
def endpoint_obtener_preferencias():
    return archivo_service.get_preferences()


@router.put("/preferencias", response_model=ArchivoActionResponse)
def endpoint_actualizar_preferencias(prefs: PreferencesModel):
    return archivo_service.update_preferences(prefs)


@router.post("/preferencias/restablecer", response_model=ArchivoActionResponse)
def endpoint_restablecer_preferencias():
    return archivo_service.reset_preferences()


@router.post("/avanzado/respaldo", response_model=ArchivoActionResponse)
def endpoint_crear_respaldo(request: OpenFileRequest):
    return archivo_service.create_backup(request.filepath)


@router.post("/avanzado/info", response_model=ArchivoActionResponse)
def endpoint_obtener_info_sketch(request: Optional[SketchInfoRequest] = None):
    return archivo_service.get_sketch_info(request)

