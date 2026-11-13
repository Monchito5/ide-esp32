"""
Endpoints en FastAPI para el Modulo de Archivo.
Incluye:
1. Recepcion de codigo fuente desde Flutter con UploadFile y preparacion en estructura ESP-IDF.
2. Funcion y endpoint puente para entregar la ruta absoluta del proyecto temporal al compilador "Sketch".
3. Empaquetado de archivos .bin generados y logs de compilacion/errores de regreso hacia Flutter.
4. Descarga directa de binarios (.bin) y funciones del menu Archivo.
"""

import os
from typing import List

from archivo_backend.schemas import (ArchivoActionResponse,
                                     BuildAndFilesDeliveryResponse,
                                     ClearRecentsResponse, CloseSketchRequest,
                                     CompilerInputResultRequest,
                                     ESPIDFProjectPreparedResponse,
                                     OpenFileRequest, OpenFolderRequest,
                                     PreferencesModel, ReloadRequest,
                                     ResetPreferencesResponse, SaveAsRequest,
                                     SaveFileRequest, SketchInfoRequest,
                                     SketchInfoResponse, TemplateResponse)
from archivo_backend.service import ArchivoService
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/archivo", tags=["Modulo de Archivo (ESP-IDF & IDE)"])
archivo_service = ArchivoService()


# =============================================================================
# FUNCION PUENTE DIRECTA PARA EL EQUIPO DEL COMPILADOR ("SKETCH")
# =============================================================================
def obtener_ruta_absoluta_para_sketch(project_id: str) -> str:
    """
    Funcion que el modulo 'Sketch' (compilador ESP-IDF) puede importar y llamar
    directamente en Python para obtener la ruta absoluta del directorio temporal
    donde ya estan creados el CMakeLists.txt raiz y la subcarpeta main/.
    """
    return archivo_service.get_project_directory_for_compiler(project_id)


# =============================================================================
# ENDPOINTS PUENTE: FLUTTER <-> MODULO ARCHIVO (ESP-IDF) <-> SKETCH / FLASHEO
# =============================================================================
@router.post("/espidf/preparar", response_model=ESPIDFProjectPreparedResponse)
async def preparar_proyecto_espidf(
    project_name: str = Form(
        default="esp32_sketch", description="Nombre del proyecto ESP-IDF"
    ),
    files: List[UploadFile] = File(
        ...,
        description="Archivos de codigo fuente (.c, .cpp, .h, .ino) enviados desde Flutter",
    ),
):
    """
    1. Recibe los archivos de codigo fuente escritos por el usuario en Flutter mediante UploadFile.
    2. Crea un directorio temporal con la estructura estricta de ESP-IDF:
       - <temp_dir>/<project_name>/CMakeLists.txt
       - <temp_dir>/<project_name>/main/CMakeLists.txt
       - <temp_dir>/<project_name>/main/<archivos fuente>
    3. Devuelve el project_id y project_absolute_path listos para el compilador Sketch.
    """
    return await archivo_service.prepare_espidf_project(
        uploaded_files=files,
        project_name=project_name,
    )


@router.get("/espidf/{project_id}/ruta-compilador")
def endpoint_ruta_para_compilador(project_id: str):
    """
    Devuelve la ruta absoluta del directorio temporal del proyecto ESP-IDF
    para que el modulo Sketch pueda ejecutar la compilacion ahi.
    """
    try:
        abs_path = obtener_ruta_absoluta_para_sketch(project_id)
        return {
            "success": True,
            "project_id": project_id,
            "project_absolute_path": abs_path,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/espidf/entregar-resultados", response_model=BuildAndFilesDeliveryResponse
)
def entregar_binarios_y_logs_a_flutter(request: CompilerInputResultRequest):
    """
    Una vez que el compilador Sketch termina, este endpoint recolecta todos los
    archivos .bin generados en el directorio temporal (build/) junto con los
    registros de exito/errores, y los devuelve a Flutter para mostrarlos en la UI
    del Log y pasarlos al modulo de flasheo.
    """
    return archivo_service.collect_build_results_for_flutter(request)


@router.get("/espidf/{project_id}/descargar-bin")
def descargar_archivo_binario(
    project_id: str,
    rel_path: str = Query(
        ..., description="Ruta relativa del archivo .bin dentro del proyecto ESP-IDF"
    ),
):
    """
    Permite a Flutter o al modulo de flasheo descargar directamente cualquier
    archivo .bin generado (bootloader.bin, partition-table.bin, app.bin).
    """
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
    """Elimina el directorio temporal de ESP-IDF una vez concluido el flasheo."""
    removed = archivo_service.cleanup_temp_project(project_id)
    return {"success": removed, "project_id": project_id}


# =============================================================================
# ENDPOINTS ADICIONALES DEL MENU ARCHIVO LOCAL (Nuevo, Abrir, Guardar, Submenus, Preferencias)
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


@router.get("/submenus", response_model=ArchivoActionResponse)
def endpoint_obtener_submenus():
    return archivo_service.get_submenus_data()


@router.get("/preferencias", response_model=ArchivoActionResponse)
def endpoint_obtener_preferencias():
    return archivo_service.get_preferences()


@router.put("/preferencias", response_model=ArchivoActionResponse)
def endpoint_actualizar_preferencias(prefs: PreferencesModel):
    return archivo_service.update_preferences(prefs)


@router.post("/avanzado/respaldo", response_model=ArchivoActionResponse)
def endpoint_crear_respaldo(request: OpenFileRequest):
    return archivo_service.create_backup(request.filepath)


# =============================================================================
# ENDPOINTS ADICIONALES DEL MENU ARCHIVO (Cerrar, Guardar como, Recargar, etc.)
# =============================================================================
@router.post("/cerrar", response_model=ArchivoActionResponse)
def endpoint_cerrar_sketch(request: CloseSketchRequest):
    return archivo_service.close_sketch(request.filepath)


@router.post("/guardar-como", response_model=ArchivoActionResponse)
def endpoint_guardar_como(request: SaveAsRequest):
    return archivo_service.save_as_sketch(request.filepath, request.content)


@router.post("/recargar", response_model=ArchivoActionResponse)
def endpoint_recargar_sketch(request: ReloadRequest):
    return archivo_service.reload_sketch(request.filepath)


@router.get("/plantilla-base", response_model=TemplateResponse)
def endpoint_plantilla_base():
    return archivo_service.get_sketch_template()


@router.get("/info-sketch", response_model=SketchInfoResponse)
def endpoint_info_sketch(
    filepath: str = Query(..., description="Ruta del archivo a inspeccionar")
):
    return archivo_service.get_sketch_info(filepath)


@router.post("/restablecer-preferencias", response_model=ResetPreferencesResponse)
def endpoint_restablecer_preferencias():
    return archivo_service.reset_preferences()


@router.post("/limpiar-recientes", response_model=ClearRecentsResponse)
def endpoint_limpiar_recientes():
    return archivo_service.clear_recents()
