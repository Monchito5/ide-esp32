"""
Servicio de negocio del Modulo Archivo (FastAPI).
Actua como puente entre:
1. Frontend (Flutter) -> Recepcion de codigo fuente con UploadFile y devolucion de logs + binarios (.bin).
2. Compilador Sketch (ESP-IDF) -> Creacion de estructura estricta ESP-IDF en directorio temporal y entrega de ruta absoluta.
3. Modulo de Flasheo -> Entrega de rutas/binarios (.bin) con sus offsets de memoria de ESP32.
4. Gestion local de archivos y proyectos reutilizando ConfigManager y FileManager.
"""

import base64
import datetime
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from archivo_backend.config import (
    DEFAULT_SKETCH_TEMPLATE,
    ConfigManager,
    ExamplesCatalog,
    FileManager,
)
from archivo_backend.schemas import (
    ArchivoActionResponse,
    BuildAndFilesDeliveryResponse,
    ClearRecentsResponse,
    CompilerInputResultRequest,
    CreateProjectFileRequest,
    ESPIDFProjectPreparedResponse,
    GeneratedBinarySchema,
    OpenFileRequest,
    PreferencesModel,
    ResetPreferencesResponse,
    SaveFileRequest,
    SketchInfoRequest,
    SketchInfoResponse,
    TemplateResponse,
)
from fastapi import UploadFile


class ArchivoService:
    """
    Gestiona tanto la preparacion de proyectos temporales en formato estricto ESP-IDF
    como las operaciones locales del Menu Archivo reutilizando FileManager.
    """

    def __init__(self, base_dir: str | None = None):
        self.config_manager = ConfigManager(base_dir=base_dir)
        self.file_manager = FileManager(self.config_manager)
        self.current_file: Optional[str] = None
        self.current_encoding: str = "utf-8"
        # Registro en memoria de directorios temporales activos: {project_id: absolute_path}
        self._active_espidf_projects: Dict[str, str] = {}

    # -------------------------------------------------------------------------
    # 1 y 2. Recepcion de archivos desde Flutter y estructuracion para ESP-IDF
    # -------------------------------------------------------------------------
    async def prepare_espidf_project(
        self,
        uploaded_files: List[UploadFile],
        project_name: str = "esp32_sketch",
    ) -> ESPIDFProjectPreparedResponse:
        safe_project_name = (
            re.sub(r"[^a-zA-Z0-9_]", "_", project_name.strip()) or "esp32_sketch"
        )
        project_id = f"{safe_project_name}_{uuid.uuid4().hex[:8]}"

        try:
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

                if raw_name == "CMakeLists.txt":
                    content_text = file_bytes.decode("utf-8", errors="replace")
                    if "idf_component_register" in content_text:
                        target_path = os.path.join(main_dir, "CMakeLists.txt")
                        custom_main_cmake_uploaded = True
                    else:
                        target_path = os.path.join(project_dir, "CMakeLists.txt")
                        custom_root_cmake_uploaded = True
                else:
                    target_path = os.path.join(main_dir, raw_name)
                    if raw_name.endswith((".c", ".cpp", ".cc")):
                        source_filenames_in_main.append(raw_name)
                    elif raw_name.endswith(".ino"):
                        cpp_name = os.path.splitext(raw_name)[0] + ".cpp"
                        target_path = os.path.join(main_dir, cpp_name)
                        source_filenames_in_main.append(cpp_name)

                with open(target_path, "wb") as f_out:
                    f_out.write(file_bytes)
                created_files.append(os.path.abspath(target_path))

            if not source_filenames_in_main:
                default_main_c = os.path.join(main_dir, "main.c")
                with open(
                    default_main_c, "w", encoding="utf-8", newline="\n"
                ) as f_main:
                    f_main.write(
                        "#include <stdio.h>\n\n"
                        "void app_main(void)\n"
                        "{\n"
                        '    printf("ESP32 listo desde ESP-IDF!\\n");\n'
                        "}\n"
                    )
                source_filenames_in_main.append("main.c")
                created_files.append(os.path.abspath(default_main_c))

            if not custom_root_cmake_uploaded:
                root_cmake_path = os.path.join(project_dir, "CMakeLists.txt")
                root_cmake_content = (
                    "# Generado automaticamente por el Modulo de Archivo para ESP-IDF\n"
                    "cmake_minimum_required(VERSION 3.16)\n\n"
                    "include($ENV{IDF_PATH}/tools/cmake/project.cmake)\n"
                    f"project({safe_project_name})\n"
                )
                with open(root_cmake_path, "w", encoding="utf-8", newline="\n") as f_rc:
                    f_rc.write(root_cmake_content)
                created_files.append(os.path.abspath(root_cmake_path))

            if not custom_main_cmake_uploaded:
                main_cmake_path = os.path.join(main_dir, "CMakeLists.txt")
                srcs_formatted = " ".join(
                    f'"{src}"' for src in source_filenames_in_main
                )
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
                message="Proyecto estructurado correctamente bajo el estandar ESP-IDF.",
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
    # 3. Entrega de la ruta absoluta al compilador (Modulo Sketch)
    # -------------------------------------------------------------------------
    def get_project_directory_for_compiler(self, project_id_or_path: str) -> str:
        if project_id_or_path in self._active_espidf_projects:
            target = self._active_espidf_projects[project_id_or_path]
        else:
            target = os.path.abspath(project_id_or_path)

        if not os.path.isdir(target):
            raise FileNotFoundError(
                f"No se encontro el directorio temporal del proyecto ESP-IDF: {target}"
            )
        return os.path.abspath(target)

    # -------------------------------------------------------------------------
    # 4. Empaquetado de archivos .bin y registros (Logs) de regreso a Flutter
    # -------------------------------------------------------------------------
    def collect_build_results_for_flutter(
        self,
        req: CompilerInputResultRequest,
    ) -> BuildAndFilesDeliveryResponse:
        try:
            project_dir = self.get_project_directory_for_compiler(req.project_id)
        except FileNotFoundError as err:
            return BuildAndFilesDeliveryResponse(
                success=False,
                status="PROJECT_NOT_FOUND",
                project_id=req.project_id,
                project_absolute_path="",
                result_summary="No se localizo el directorio temporal del proyecto.",
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
                        rel_path = (
                            Path(full_bin_path)
                            .relative_to(Path(project_dir))
                            .as_posix()
                        )
                        size_bytes = os.path.getsize(full_bin_path)
                        flash_offset = self._infer_esp32_flash_offset(file)

                        b64_data = None
                        if req.include_base64:
                            try:
                                with open(full_bin_path, "rb") as bf:
                                    b64_data = base64.b64encode(bf.read()).decode(
                                        "ascii"
                                    )
                            except Exception:
                                b64_data = None

                        download_url = f"/api/v1/archivo/espidf/{req.project_id}/descargar-bin?rel_path={rel_path}"

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
        status_label = (
            "COMPILATION_SUCCESS" if overall_success else "COMPILATION_FAILED"
        )
        summary_msg = (
            f"Compilacion exitosa. Binarios (.bin) recolectados: {len(binaries_list)}."
            if overall_success
            else f"La compilacion reporto {len(req.compiler_stderr)} error(es)."
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
        project_dir = Path(
            self.get_project_directory_for_compiler(project_id)
        ).resolve()
        candidate = (project_dir / rel_path).resolve()
        if project_dir not in candidate.parents and candidate != project_dir:
            raise PermissionError("Acceso denegado fuera del directorio del proyecto.")
        if not candidate.is_file() or candidate.suffix.lower() != ".bin":
            raise FileNotFoundError(
                f"El archivo binario solicitado no existe: {rel_path}"
            )
        return str(candidate)

    def cleanup_temp_project(self, project_id: str) -> bool:
        if project_id not in self._active_espidf_projects:
            return False
        project_dir = self._active_espidf_projects.pop(project_id)
        parent_temp = os.path.dirname(project_dir)
        if os.path.isdir(parent_temp) and os.path.basename(parent_temp).startswith(
            "espidf_workspace_"
        ):
            shutil.rmtree(parent_temp, ignore_errors=True)
        elif os.path.isdir(project_dir):
            shutil.rmtree(project_dir, ignore_errors=True)
        return True

    # -------------------------------------------------------------------------
    # 5. Operaciones locales del Menu Archivo reutilizando FileManager
    # -------------------------------------------------------------------------
    def new_sketch(self) -> ArchivoActionResponse:
        self.current_file = None
        self.current_encoding = "utf-8"
        info = self.file_manager.get_project_info(None)
        return ArchivoActionResponse(
            success=True,
            action="new_sketch",
            result="Nuevo sketch inicializado con plantilla base ESP32.",
            errors=[],
            files=[],
            content=DEFAULT_SKETCH_TEMPLATE,
            encoding="utf-8",
            metadata=info,
        )

    def open_sketch(self, req: OpenFileRequest) -> ArchivoActionResponse:
        try:
            resolved_path, content, used_encoding = self.file_manager.read_file(
                req.filepath
            )
            self.current_file = resolved_path
            self.current_encoding = used_encoding
            info = self.file_manager.get_project_info(resolved_path)
            return ArchivoActionResponse(
                success=True,
                action="open_file",
                result=f"Archivo '{os.path.basename(resolved_path)}' cargado correctamente.",
                errors=[],
                files=[resolved_path],
                content=content,
                encoding=used_encoding,
                metadata=info,
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="open_file",
                result="No se pudo abrir el archivo solicitado.",
                errors=[str(e)],
                files=[req.filepath] if req.filepath else [],
                metadata=self.file_manager.get_project_info(self.current_file),
            )

    def save_sketch(self, req: SaveFileRequest) -> ArchivoActionResponse:
        try:
            resolved_path, generated_files = self.file_manager.write_file(
                target_path=req.filepath,
                content=req.content,
                create_project_folder=req.create_project_folder,
            )
            self.current_file = resolved_path
            self.current_encoding = "utf-8"
            info = self.file_manager.get_project_info(resolved_path)
            return ArchivoActionResponse(
                success=True,
                action="save_file",
                result=f"Archivo guardado exitosamente en '{resolved_path}'.",
                errors=[],
                files=generated_files,
                content=req.content,
                encoding="utf-8",
                metadata=info,
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="save_file",
                result="Error al guardar el archivo en disco.",
                errors=[str(e)],
                files=[],
                metadata=self.file_manager.get_project_info(self.current_file),
            )

    def close_sketch(self, filepath: Optional[str] = None) -> ArchivoActionResponse:
        closed_file = filepath or self.current_file
        self.current_file = None
        self.current_encoding = "utf-8"
        info = self.file_manager.get_project_info(None)
        return ArchivoActionResponse(
            success=True,
            action="close_sketch",
            result="Sketch cerrado correctamente.",
            errors=[],
            files=[closed_file] if closed_file else [],
            content="",
            encoding="utf-8",
            metadata=info,
        )

    def get_current_project(self) -> ArchivoActionResponse:
        info = self.file_manager.get_project_info(self.current_file)
        return ArchivoActionResponse(
            success=True,
            action="get_current_project",
            result="Informacion del proyecto activo obtenida.",
            errors=[],
            files=info.get("project_files", []),
            encoding=self.current_encoding,
            metadata=info,
        )

    def get_project_files(
        self, project_path: Optional[str] = None
    ) -> ArchivoActionResponse:
        target = project_path or self.current_file
        if not target:
            info = self.file_manager.get_project_info(None)
            return ArchivoActionResponse(
                success=False,
                action="get_project_files",
                result="No hay un proyecto activo ni se especifico una ruta de proyecto.",
                errors=["No se proporciono project_path y no hay archivo activo."],
                files=[],
                metadata=info,
            )

        abs_target = os.path.abspath(target)
        if not os.path.exists(abs_target):
            return ArchivoActionResponse(
                success=False,
                action="get_project_files",
                result="La ruta del proyecto especificada no existe.",
                errors=[f"No existe la ruta: {abs_target}"],
                files=[],
                metadata=self.file_manager.get_project_info(None),
            )

        info = self.file_manager.get_project_info(abs_target)
        return ArchivoActionResponse(
            success=True,
            action="get_project_files",
            result="Archivos del proyecto obtenidos correctamente.",
            errors=[],
            files=info.get("project_files", []),
            metadata=info,
        )

    def create_project_file(
        self, req: CreateProjectFileRequest
    ) -> ArchivoActionResponse:
        project_dir = req.project_dir
        if not project_dir and self.current_file:
            project_dir = os.path.dirname(self.current_file)

        if not project_dir:
            return ArchivoActionResponse(
                success=False,
                action="create_project_file",
                result="No hay proyecto activo para crear el archivo secundario.",
                errors=["Especifica project_dir o guarda/abre un proyecto primero."],
                files=[],
                metadata=self.file_manager.get_project_info(None),
            )

        try:
            created_path = self.file_manager.create_project_file(
                project_dir=project_dir,
                filename=req.filename,
                content=req.content,
            )
            info = self.file_manager.get_project_info(self.current_file or created_path)
            return ArchivoActionResponse(
                success=True,
                action="create_project_file",
                result=f"Archivo '{req.filename}' creado en el proyecto.",
                errors=[],
                files=[created_path],
                content=req.content,
                encoding="utf-8",
                metadata=info,
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="create_project_file",
                result="No se pudo crear el archivo secundario en el proyecto.",
                errors=[str(e)],
                files=[],
                metadata=self.file_manager.get_project_info(self.current_file),
            )

    def get_submenus_data(self) -> ArchivoActionResponse:
        recent = self.config_manager.settings.get("recent_files", [])
        sketchbook = self.config_manager.list_sketchbook_projects_detailed()
        return ArchivoActionResponse(
            success=True,
            action="get_submenus",
            result="Submenus secundarios obtenidos correctamente.",
            errors=[],
            files=recent,
            metadata={
                "recent_files": recent,
                "sketchbook_projects": sketchbook,
                "examples_categories": ExamplesCatalog.CATEGORIES,
                "sketchbook_path": self.config_manager.settings.get("sketchbook_path"),
                "libraries_path": self.config_manager.get_libraries_path(),
            },
        )

    def get_preferences(self) -> ArchivoActionResponse:
        self.config_manager.get_libraries_path()
        return ArchivoActionResponse(
            success=True,
            action="get_preferences",
            result="Preferencias actuales cargadas.",
            errors=[],
            files=[self.config_manager.config_path],
            metadata=dict(self.config_manager.settings),
        )

    def update_preferences(self, prefs: PreferencesModel) -> ArchivoActionResponse:
        data = prefs.model_dump() if hasattr(prefs, "model_dump") else prefs.dict()
        sketchbook_dir = (
            (data.get("sketchbook_path") or "").strip()
            or self.config_manager.settings.get("sketchbook_path")
            or self.config_manager.default_sketchbook
        )
        data["sketchbook_path"] = sketchbook_dir

        lib_path = data.get("libraries_path")
        if not lib_path or not str(lib_path).strip():
            data["libraries_path"] = os.path.join(sketchbook_dir, "libraries")
        else:
            data["libraries_path"] = str(lib_path).strip()

        self.config_manager.settings.update(data)
        self.config_manager.save_config()
        self.config_manager.ensure_sketchbook_exists()
        return ArchivoActionResponse(
            success=True,
            action="update_preferences",
            result="Preferencias actualizadas y guardadas en disco.",
            errors=[],
            files=[self.config_manager.config_path],
            metadata=dict(self.config_manager.settings),
        )

    def reset_preferences(self) -> ArchivoActionResponse:
        defaults = self.config_manager.reset_defaults()
        return ArchivoActionResponse(
            success=True,
            action="reset_preferences",
            result="Preferencias restablecidas a valores por defecto.",
            errors=[],
            files=[self.config_manager.config_path],
            metadata=dict(defaults),
        )

    def clear_recent_files(self) -> ArchivoActionResponse:
        self.config_manager.clear_recent_files()
        return ArchivoActionResponse(
            success=True,
            action="clear_recent_files",
            result="Historial de archivos recientes limpiado.",
            errors=[],
            files=[],
            metadata={"recent_files": []},
        )

    def create_backup(self, filepath: Optional[str] = None) -> ArchivoActionResponse:
        target = filepath or self.current_file
        if not target:
            return ArchivoActionResponse(
                success=False,
                action="advanced_backup",
                result="No se especifico archivo para crear respaldo (.bak).",
                errors=["Ruta de archivo vacia."],
                files=[],
            )
        try:
            bak_path = self.file_manager.create_backup(target)
            return ArchivoActionResponse(
                success=True,
                action="advanced_backup",
                result=f"Respaldo creado en '{bak_path}'.",
                errors=[],
                files=[os.path.abspath(target), bak_path],
                metadata=self.file_manager.get_project_info(target),
            )
        except Exception as e:
            return ArchivoActionResponse(
                success=False,
                action="advanced_backup",
                result="Fallo al generar respaldo (.bak).",
                errors=[str(e)],
                files=[],
            )

    def get_sketch_info(
        self, req: Optional[SketchInfoRequest] = None
    ) -> ArchivoActionResponse:
        target_path = (
            req.filepath if req and req.filepath else None
        ) or self.current_file
        content = req.content if req else None
        stats = self.file_manager.get_sketch_stats(
            content=content,
            filepath=target_path,
            encoding=self.current_encoding,
        )
        return ArchivoActionResponse(
            success=True,
            action="sketch_info",
            result="Informacion y estadisticas del sketch obtenidas.",
            errors=[],
            files=[os.path.abspath(target_path)] if target_path else [],
            encoding=stats["encoding"],
            metadata=stats,
        )

    # -------------------------------------------------------------------------
    # Metodos de compatibilidad con endpoints previos del monorepo
    # -------------------------------------------------------------------------
    def save_as_sketch(self, filepath: str, content: str) -> ArchivoActionResponse:
        return self.save_sketch(
            SaveFileRequest(
                filepath=filepath,
                content=content,
                create_project_folder=True,
            )
        )

    def reload_sketch(self, filepath: str) -> ArchivoActionResponse:
        return self.open_sketch(OpenFileRequest(filepath=filepath))

    def get_sketch_template(self) -> TemplateResponse:
        return TemplateResponse(template=DEFAULT_SKETCH_TEMPLATE)

    def get_sketch_info_legacy(self, filepath: str) -> SketchInfoResponse:
        if not filepath or not os.path.exists(filepath):
            return SketchInfoResponse(
                filepath=filepath,
                lineas=0,
                caracteres=0,
                tamaño_bytes=0,
                ultima_modificacion="",
            )
        try:
            stats = self.file_manager.get_sketch_stats(filepath=filepath)
            mtime = os.path.getmtime(filepath)
            ultima_mod = datetime.datetime.fromtimestamp(mtime).isoformat()
            return SketchInfoResponse(
                filepath=filepath,
                lineas=stats["lines"],
                caracteres=stats["chars"],
                tamaño_bytes=stats["size_bytes"],
                ultima_modificacion=ultima_mod,
                encoding=stats["encoding"],
            )
        except Exception:
            return SketchInfoResponse(
                filepath=filepath,
                lineas=0,
                caracteres=0,
                tamaño_bytes=0,
                ultima_modificacion="",
            )

    def reset_preferences_legacy(self) -> ResetPreferencesResponse:
        self.config_manager.reset_defaults()
        return ResetPreferencesResponse(
            success=True,
            configuracion=dict(self.config_manager.settings),
            mensaje="Preferencias restablecidas a valores por defecto.",
        )

    def clear_recents(self) -> ClearRecentsResponse:
        self.config_manager.clear_recent_files()
        return ClearRecentsResponse(
            success=True,
            mensaje="Historial de archivos recientes limpiado.",
        )
