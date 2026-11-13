"""
Servicio de negocio del Módulo de Archivo (FastAPI).
Actúa como puente entre:
1. Frontend (Flutter) -> Recepción de código fuente con UploadFile y devolución de logs + binarios (.bin).
2. Compilador "Sketch" (ESP-IDF) -> Creación de estructura estricta ESP-IDF en directorio temporal y entrega de ruta absoluta.
3. Módulo de Flasheo -> Entrega de rutas/binarios (.bin) con sus offsets de memoria de ESP32.
"""

import base64
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List
from fastapi import UploadFile

# Permitir importar los gestores locales desde la raíz del proyecto
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from main import DEFAULT_SKETCH_TEMPLATE, ConfigManager, ExamplesCatalog
from .schemas import (
    ArchivoActionResponse,
    BuildAndFilesDeliveryResponse,
    CompilerInputResultRequest,
    ESPIDFProjectPreparedResponse,
    GeneratedBinarySchema,
    OpenFileRequest,
    PreferencesModel,
    SaveFileRequest,
)


class ArchivoService:
    """
    Gestiona tanto la preparación de proyectos temporales en formato estricto ESP-IDF
    como el empaquetado de resultados (.bin + logs) de regreso a Flutter.
    """

    def __init__(self, base_dir: str | None = None):
        self.config_manager = ConfigManager(base_dir=base_dir or ROOT_DIR)
        # Registro en memoria de directorios temporales activos: {project_id: absolute_path}
        self._active_espidf_projects: Dict[str, str] = {}

    # -------------------------------------------------------------------------
    # 1 y 2. Recepción de archivos desde Flutter y estructuración para ESP-IDF
    # -------------------------------------------------------------------------
    async def prepare_espidf_project(
        self,
        uploaded_files: List[UploadFile],
        project_name: str = "esp32_sketch",
    ) -> ESPIDFProjectPreparedResponse:
        """
        Recibe los archivos enviados por Flutter mediante UploadFile y construye
        un directorio temporal con la estructura estricta que exige ESP-IDF:

        <temp_dir>/<project_name>/
        ├── CMakeLists.txt
        └── main/
            ├── CMakeLists.txt
            └── <archivos fuente .c / .cpp / .h>
        """
        safe_project_name = re.sub(r"[^a-zA-Z0-9_]", "_", project_name.strip()) or "esp32_sketch"
        project_id = f"{safe_project_name}_{uuid.uuid4().hex[:8]}"

        try:
            # Crear directorio temporal base y carpeta del proyecto ESP-IDF
            temp_root = tempfile.mkdtemp(prefix="espidf_workspace_")
            project_dir = os.path.join(temp_root, safe_project_name)
            main_dir = os.path.join(project_dir, "main")
            os.makedirs(main_dir, exist_ok=True)

            created_files: List[str] = []
            source_filenames_in_main: List[str] = []
            custom_root_cmake_uploaded = False
            custom_main_cmake_uploaded = False

            for upload in uploaded_files:
                raw_name = os.path.basename(upload.filename or "main.c")
                file_bytes = await upload.read()

                # Si el usuario sube su propio CMakeLists.txt, distinguimos si es raíz o de main/
                if raw_name == "CMakeLists.txt":
                    content_text = file_bytes.decode("utf-8", errors="replace")
                    if "idf_component_register" in content_text:
                        target_path = os.path.join(main_dir, "CMakeLists.txt")
                        custom_main_cmake_uploaded = True
                    else:
                        target_path = os.path.join(project_dir, "CMakeLists.txt")
                        custom_root_cmake_uploaded = True
                else:
                    # Si sube un archivo .ino y ESP-IDF requiere .cpp/.c, lo guardamos también o adaptamos
                    target_path = os.path.join(main_dir, raw_name)
                    if raw_name.endswith((".c", ".cpp", ".cc")):
                        source_filenames_in_main.append(raw_name)
                    elif raw_name.endswith(".ino"):
                        # Convertimos/guardamos como .cpp dentro de main/ para que CMake de ESP-IDF lo compile
                        cpp_name = os.path.splitext(raw_name)[0] + ".cpp"
                        target_path = os.path.join(main_dir, cpp_name)
                        source_filenames_in_main.append(cpp_name)

                with open(target_path, "wb") as f_out:
                    f_out.write(file_bytes)
                created_files.append(os.path.abspath(target_path))

            # Si no se subió ningún archivo fuente (.c / .cpp), creamos un main.c mínimo válido para ESP-IDF
            if not source_filenames_in_main:
                default_main_c = os.path.join(main_dir, "main.c")
                with open(default_main_c, "w", encoding="utf-8", newline="\n") as f_main:
                    f_main.write(
                        '#include <stdio.h>\n\n'
                        'void app_main(void)\n'
                        '{\n'
                        '    printf("ESP32 listo desde ESP-IDF!\\n");\n'
                        '}\n'
                    )
                source_filenames_in_main.append("main.c")
                created_files.append(os.path.abspath(default_main_c))

            # 1) Generar CMakeLists.txt raíz obligatorio para ESP-IDF
            if not custom_root_cmake_uploaded:
                root_cmake_path = os.path.join(project_dir, "CMakeLists.txt")
                root_cmake_content = (
                    "# Generado automáticamente por el Módulo de Archivo para ESP-IDF\n"
                    "cmake_minimum_required(VERSION 3.16)\n\n"
                    "include($ENV{IDF_PATH}/tools/cmake/project.cmake)\n"
                    f"project({safe_project_name})\n"
                )
                with open(root_cmake_path, "w", encoding="utf-8", newline="\n") as f_rc:
                    f_rc.write(root_cmake_content)
                created_files.append(os.path.abspath(root_cmake_path))

            # 2) Generar main/CMakeLists.txt obligatorio para registrar los SRCS en ESP-IDF
            if not custom_main_cmake_uploaded:
                main_cmake_path = os.path.join(main_dir, "CMakeLists.txt")
                srcs_formatted = " ".join(f'"{src}"' for src in source_filenames_in_main)
                main_cmake_content = (
                    f"idf_component_register(SRCS {srcs_formatted}\n"
                    '                       INCLUDE_DIRS ".")\n'
                )
                with open(main_cmake_path, "w", encoding="utf-8", newline="\n") as f_mc:
                    f_mc.write(main_cmake_content)
                created_files.append(os.path.abspath(main_cmake_path))

            abs_project_dir = os.path.abspath(project_dir)
            self._active_espidf_projects[project_id] = abs_project_dir

            return ESPIDFProjectPreparedResponse(
                success=True,
                project_id=project_id,
                project_name=safe_project_name,
                project_absolute_path=abs_project_dir,
                created_files=created_files,
                message="Proyecto estructurado correctamente bajo el estándar ESP-IDF.",
                errors=[],
            )

        except Exception as e:
            return ESPIDFProjectPreparedResponse(
                success=False,
                project_id=project_id,
                project_name=safe_project_name,
                project_absolute_path="",
                created_files=[],
                message="Error al estructurar el directorio temporal para ESP-IDF.",
                errors=[str(e)],
            )

    # -------------------------------------------------------------------------
    # 3. Entrega de la ruta absoluta al compilador (Módulo "Sketch")
    # -------------------------------------------------------------------------
    def get_project_directory_for_compiler(self, project_id_or_path: str) -> str:
        """
        Función puente para el módulo 'Sketch' (compilador ESP-IDF):
        Recibe el `project_id` (o ruta) y devuelve la ruta absoluta validada del
        directorio raíz del proyecto temporal donde existe el CMakeLists.txt raíz.
        """
        if project_id_or_path in self._active_espidf_projects:
            target = self._active_espidf_projects[project_id_or_path]
        else:
            target = os.path.abspath(project_id_or_path)

        if not os.path.isdir(target):
            raise FileNotFoundError(
                f"No se encontró el directorio temporal del proyecto ESP-IDF: {target}"
            )
        return os.path.abspath(target)

    # -------------------------------------------------------------------------
    # 4. Empaquetado de archivos .bin y registros (Logs) de regreso a Flutter
    # -------------------------------------------------------------------------
    def collect_build_results_for_flutter(
        self,
        req: CompilerInputResultRequest,
    ) -> BuildAndFilesDeliveryResponse:
        """
        Toma los archivos `.bin` generados por el compilador ESP-IDF dentro del
        directorio del proyecto (especialmente en `build/`) junto con los logs
        de éxito/errores, y construye la respuesta estructurada para la UI de Log en Flutter.
        """
        try:
            project_dir = self.get_project_directory_for_compiler(req.project_id)
        except FileNotFoundError as err:
            return BuildAndFilesDeliveryResponse(
                success=False,
                status="PROJECT_NOT_FOUND",
                project_id=req.project_id,
                project_absolute_path="",
                result_summary="No se localizó el directorio temporal del proyecto.",
                compilation_logs=req.compiler_stdout,
                errors=[str(err)] + req.compiler_stderr,
                binaries=[],
            )

        build_dir = os.path.join(project_dir, "build")
        search_root = build_dir if os.path.isdir(build_dir) else project_dir

        binaries_list: List[GeneratedBinarySchema] = []
        if os.path.isdir(search_root):
            for root, _dirs, files in os.walk(search_root):
                for file in sorted(files):
                    if file.endswith(".bin"):
                        full_bin_path = os.path.abspath(os.path.join(root, file))
                        rel_path = Path(full_bin_path).relative_to(Path(project_dir)).as_posix()
                        size_bytes = os.path.getsize(full_bin_path)

                        # Determinar offset estándar en ESP32 para ayudar al módulo de flasheo
                        flash_offset = self._infer_esp32_flash_offset(file)

                        b64_data = None
                        if req.include_base64:
                            try:
                                with open(full_bin_path, "rb") as bf:
                                    b64_data = base64.b64encode(bf.read()).decode("ascii")
                            except Exception:
                                b64_data = None

                        download_url = f"/api/archivo/espidf/{req.project_id}/descargar-bin?rel_path={rel_path}"

                        binaries_list.append(
                            GeneratedBinarySchema(
                                filename=file,
                                relative_path=rel_path,
                                absolute_path=full_bin_path,
                                size_bytes=size_bytes,
                                flash_offset=flash_offset,
                                download_url=download_url,
                                content_base64=b64_data,
                            )
                        )

        overall_success = req.compilation_success and len(req.compiler_stderr) == 0
        status_label = "COMPILATION_SUCCESS" if overall_success else "COMPILATION_FAILED"
        summary_msg = (
            f"Compilación exitosa. Binarios (.bin) recolectados: {len(binaries_list)}."
            if overall_success
            else f"La compilación reportó {len(req.compiler_stderr)} error(es)."
        )

        return BuildAndFilesDeliveryResponse(
            success=overall_success,
            status=status_label,
            project_id=req.project_id,
            project_absolute_path=project_dir,
            result_summary=summary_msg,
            compilation_logs=req.compiler_stdout,
            errors=req.compiler_stderr,
            binaries=binaries_list,
        )

    @staticmethod
    def _infer_esp32_flash_offset(filename: str) -> str:
        lower = filename.lower()
        if "bootloader" in lower:
            return "0x1000"
        if "partition" in lower:
            return "0x8000"
        if "ota_data" in lower:
            return "0xd000"
        return "0x10000"

    def resolve_binary_file_path(self, project_id: str, rel_path: str) -> str:
        """Valida de forma segura la ruta de un archivo .bin para su descarga directa."""
        project_dir = Path(self.get_project_directory_for_compiler(project_id)).resolve()
        candidate = (project_dir / rel_path).resolve()
        if project_dir not in candidate.parents and candidate != project_dir:
            raise PermissionError("Acceso denegado fuera del directorio del proyecto.")
        if not candidate.is_file() or candidate.suffix.lower() != ".bin":
            raise FileNotFoundError(f"El archivo binario solicitado no existe: {rel_path}")
        return str(candidate)

    def cleanup_temp_project(self, project_id: str) -> bool:
        """Elimina el directorio temporal cuando ya no se requiere."""
        if project_id not in self._active_espidf_projects:
            return False
        project_dir = self._active_espidf_projects.pop(project_id)
        parent_temp = os.path.dirname(project_dir)
        if os.path.isdir(parent_temp) and os.path.basename(parent_temp).startswith("espidf_workspace_"):
            shutil.rmtree(parent_temp, ignore_errors=True)
        elif os.path.isdir(project_dir):
            shutil.rmtree(project_dir, ignore_errors=True)
        return True

    # -------------------------------------------------------------------------
    # Operaciones adicionales del Menú Archivo (Nuevo, Abrir, Guardar, Submenús, Preferencias)
    # -------------------------------------------------------------------------
    def new_sketch(self) -> ArchivoActionResponse:
        return ArchivoActionResponse(
            success=True,
            action="new_sketch",
            result="Nuevo sketch inicializado.",
            errors=[],
            files=[],
            content="",
        )

    def open_sketch(self, req: OpenFileRequest) -> ArchivoActionResponse:
        filepath = req.filepath
        if not filepath.endswith((".ino", ".cpp", ".c", ".h")):
            return ArchivoActionResponse(
                success=False,
                action="open_file",
                result="Extensión de archivo no soportada.",
                errors=[f"El archivo '{filepath}' no tiene una extensión válida (.ino, .cpp, .c, .h)."],
                files=[filepath],
            )
        try:
            used_encoding = "utf-8"
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                used_encoding = "latin-1"
                with open(filepath, "r", encoding="latin-1") as f:
                    content = f.read()

            self.config_manager.add_recent_file(filepath)
            return ArchivoActionResponse(
                success=True,
                action="open_file",
                result=f"Archivo '{os.path.basename(filepath)}' cargado correctamente.",
                errors=[],
                files=[filepath],
                content=content,
                encoding=used_encoding,
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="open_file",
                result="No se pudo abrir el archivo solicitado.",
                errors=[str(e)],
                files=[filepath],
            )

    def save_sketch(self, req: SaveFileRequest) -> ArchivoActionResponse:
        target = req.filepath
        if not os.path.splitext(target)[1]:
            target += ".ino"
        generated_files = [target]
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
            if self.config_manager.settings.get("auto_backup_on_save") and os.path.exists(target):
                bak_path = target + ".bak"
                shutil.copy2(target, bak_path)
                generated_files.append(bak_path)

            with open(target, "w", encoding="utf-8", newline="") as f:
                f.write(req.content)

            self.config_manager.add_recent_file(target)
            return ArchivoActionResponse(
                success=True,
                action="save_file",
                result=f"Archivo guardado exitosamente en '{target}'.",
                errors=[],
                files=generated_files,
                content=req.content,
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="save_file",
                result="Error al guardar el archivo en disco.",
                errors=[str(e)],
                files=[],
            )

    def get_submenus_data(self) -> ArchivoActionResponse:
        recent = self.config_manager.settings.get("recent_files", [])
        sketchbook = [
            {"name": name, "path": path}
            for name, path in self.config_manager.list_sketchbook_projects()
        ]
        return ArchivoActionResponse(
            success=True,
            action="get_submenus",
            result="Submenús secundarios obtenidos correctamente.",
            errors=[],
            files=recent,
            metadata={
                "recent_files": recent,
                "sketchbook_projects": sketchbook,
                "examples_categories": ExamplesCatalog.CATEGORIES,
            },
        )

    def get_preferences(self) -> ArchivoActionResponse:
        return ArchivoActionResponse(
            success=True,
            action="get_preferences",
            result="Preferencias actuales cargadas.",
            errors=[],
            files=[self.config_manager.config_path],
            metadata=self.config_manager.settings,
        )

    def update_preferences(self, prefs: PreferencesModel) -> ArchivoActionResponse:
        self.config_manager.settings.update(prefs.model_dump())
        self.config_manager.save_config()
        self.config_manager.ensure_sketchbook_exists()
        return ArchivoActionResponse(
            success=True,
            action="update_preferences",
            result="Preferencias actualizadas y guardadas en disco.",
            errors=[],
            files=[self.config_manager.config_path],
            metadata=self.config_manager.settings,
        )

    def create_backup(self, filepath: str) -> ArchivoActionResponse:
        if not os.path.exists(filepath):
            return ArchivoActionResponse(
                success=False,
                action="advanced_backup",
                result="El archivo original no existe en disco.",
                errors=[f"No se encontró: {filepath}"],
                files=[],
            )
        bak_path = filepath + ".bak"
        try:
            shutil.copy2(filepath, bak_path)
            return ArchivoActionResponse(
                success=True,
                action="advanced_backup",
                result=f"Respaldo creado en '{bak_path}'.",
                errors=[],
                files=[filepath, bak_path],
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="advanced_backup",
                result="Fallo al generar respaldo (.bak).",
                errors=[str(e)],
                files=[],
            )
