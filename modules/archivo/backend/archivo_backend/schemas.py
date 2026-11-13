"""
Esquemas Pydantic (Contrato API JSON) del Modulo de Archivo (Puente Flutter <-> ESP-IDF Sketch <-> Flasheo).
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GeneratedBinarySchema(BaseModel):
    """Representa un archivo binario (.bin) generado por ESP-IDF tras la compilacion."""
    filename: str = Field(..., description="Nombre del archivo binario (ej. bootloader.bin, partition-table.bin, app.bin)")
    relative_path: str = Field(..., description="Ruta relativa dentro del directorio build/ de ESP-IDF")
    absolute_path: str = Field(..., description="Ruta absoluta local (util para el modulo de flasheo local)")
    size_bytes: int = Field(..., description="Tamaño del binario en bytes")
    flash_offset: Optional[str] = Field(
        default=None,
        description="Offset sugerido para flasheo en ESP32 (ej. 0x1000 bootloader, 0x8000 partition, 0x10000 app)",
    )
    download_url: str = Field(..., description="URL del endpoint para descargar este binario desde Flutter")
    content_base64: Optional[str] = Field(
        default=None,
        description="Contenido del archivo .bin codificado en Base64 (opcional para flasheo directo en cliente web)",
    )


class ESPIDFProjectPreparedResponse(BaseModel):
    """Respuesta tras recibir los archivos con UploadFile y estructurar el proyecto ESP-IDF."""
    success: bool
    project_id: str = Field(..., description="Identificador unico del directorio temporal creado")
    project_name: str = Field(..., description="Nombre asignado al proyecto ESP-IDF")
    project_absolute_path: str = Field(
        ...,
        description="Ruta absoluta del directorio raiz del proyecto ESP-IDF para entregar al modulo 'Sketch'",
    )
    created_files: List[str] = Field(
        default_factory=list,
        description="Lista de archivos estructurados dentro del directorio temporal (CMakeLists.txt, main/*)",
    )
    message: str
    errors: List[str] = Field(default_factory=list)


class CompilerInputResultRequest(BaseModel):
    """
    Datos que recibe nuestro endpoint (o que entrega el modulo 'Sketch') una vez
    que termina la compilacion en ESP-IDF sobre el directorio temporal.
    """
    project_id: str = Field(..., description="ID del proyecto temporal o ruta absoluta del proyecto")
    compilation_success: bool = Field(default=True, description="True si idf.py build termino con codigo 0")
    compiler_stdout: str = Field(default="", description="Salida estandar (logs de compilacion de ESP-IDF)")
    compiler_stderr: List[str] = Field(default_factory=list, description="Lista de errores detectados por el compilador")
    include_base64: bool = Field(
        default=True,
        description="Si es True, incluye el contenido Base64 de cada .binademas del enlace de descarga",
    )


class BuildAndFilesDeliveryResponse(BaseModel):
    """
    Esquema JSON final que el Modulo de Archivo devuelve a Flutter para mostrar
    en la UI de 'Log' y entregar los binarios (.bin) generados.
    """
    success: bool = Field(..., description="Estado general del proceso (True si proceso genero exito)")
    status: str = Field(..., description="Resumen del estado: 'COMPILATION_SUCCESS' | 'COMPILATION_FAILED' | 'PROJECT_NOT_FOUND'")
    project_id: str
    project_absolute_path: str = Field(..., description="Ruta absoluta donde se ejecuto el proyecto ESP-IDF")
    result_summary: str = Field(..., description="Mensaje resumen para encabezar la consola de Log en Flutter")
    compilation_logs: str = Field(default="", description="Salida completa del compilador para pintar en la UI de Log")
    errors: List[str] = Field(default_factory=list, description="Errores detectados (si los hay)")
    binaries: List[GeneratedBinarySchema] = Field(
        default_factory=list,
        description="Lista de archivos .bin recolectados del directorio build/ (con Base64 y URL de descarga)",
    )


# ---------------------------------------------------------------------------
# Esquemas adicionales para las funciones locales del Menu Archivo (Abrir, Guardar, Preferencias, Submenus)
# ---------------------------------------------------------------------------
class OpenFileRequest(BaseModel):
    filepath: str = Field(..., description="Ruta local del archivo (.ino, .cpp, .c, .h) a abrir")


class SaveFileRequest(BaseModel):
    filepath: str = Field(..., description="Ruta local donde se guardara el sketch")
    content: str = Field(..., description="Codigo fuente actual del editor")


class PreferencesModel(BaseModel):
    language: str = Field(default="es", description="Idioma de la interfaz ('es' o 'en')")
    theme: str = Field(default="claro", description="Tema visual ('claro' u 'oscuro')")
    font_family: str = Field(default="Consolas", description="Familia tipografica del editor")
    font_size: int = Field(default=11, ge=8, le=28, description="Tamano de fuente del editor")
    sketchbook_path: str = Field(..., description="Ruta de la carpeta Sketchbook")
    auto_backup_on_save: bool = Field(default=False, description="Crear archivo .bak al guardar")


class ArchivoActionResponse(BaseModel):
    success: bool
    action: str
    result: str
    errors: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    content: Optional[str] = None
    encoding: str = "utf-8"
    metadata: Dict[str, object] = Field(default_factory=dict)
