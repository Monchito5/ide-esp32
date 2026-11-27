"""
ESP32 IDE - Módulo de Archivo (Prototipo completo inspirado en Arduino IDE 2.3.10)
==================================================================================

Este módulo implementa todas las funciones locales del menú Archivo descritas en
la documentación de investigación y técnica del proyecto ESP32 IDE, listo para
conectarse con el módulo Sketch / Compilación:

1. Arquitectura dividida en gestores:
   - ConfigManager: Rutas multiplataforma, carpeta Sketchbook, carpeta
     Sketchbook/libraries, historial de archivos recientes, exclusión de
     directorios reservados y persistencia de Preferencias en JSON.
   - FileManager: Gestor headless (sin dependencia de GUI) reutilizable tanto
     por IDEApp (tkinter) como por el backend FastAPI. Soporta formato estándar
     de proyectos Arduino/ESP32 (Sketchbook/<Nombre>/<Nombre>.ino), creación de
     archivos secundarios (.h, .cpp, .c, .ino), lectura UTF-8 con fallback
     Latin-1, respaldos (.bak) y metadatos del proyecto para el compilador.
   - ExamplesCatalog: Catálogo de ejemplos básicos para ESP32 organizados por
     categorías.
   - IDEApp (Menu Manager + Editor tkinter): Interfaz principal de escritorio,
     menú Archivo completo, submenús dinámicos, ventana de Preferencias,
     menú Avanzado, control de cambios sin guardar y atajos de teclado.

Para ejecutar:
    python main.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_NAME = "ESP32 IDE"
SUPPORTED_EXTENSIONS = (".ino", ".cpp", ".c", ".h")

DEFAULT_SKETCH_TEMPLATE = """// Sketch para ESP32
// Configura aquí tus pines y constantes

void setup() {
  // Inicialización: se ejecuta una sola vez al encender o reiniciar la placa
  Serial.begin(115200);
}

void loop() {
  // Código principal: se ejecuta repetidamente
  
}
"""

FILE_TYPES = [
    ("Archivos Arduino/C++", "*.ino *.cpp *.c *.h"),
    ("Sketch de Arduino (*.ino)", "*.ino"),
    ("Código C/C++ (*.cpp;*.c;*.h)", "*.cpp *.c *.h"),
]

# Traducciones básicas para la opción de idioma en Preferencias
TRANSLATIONS = {
    "es": {
        "menu_file": "Archivo",
        "new_sketch": "Nuevo Sketch",
        "open": "Abrir…",
        "recent": "Abierto recientemente",
        "sketchbook": "Sketchbook",
        "examples": "Ejemplos",
        "close": "Cerrar",
        "save": "Guardar",
        "save_as": "Guardar como…",
        "preferences": "Preferencias…",
        "advanced": "Avanzado",
        "exit": "Salir",
        "no_recent": "(Sin archivos recientes)",
        "clear_recent": "Borrar historial de recientes",
        "empty_sketchbook": "(Carpeta Sketchbook vacía)",
        "open_sketchbook_dir": "Abrir carpeta Sketchbook…",
        "refresh_sketchbook": "Actualizar lista de Sketchbook",
        "adv_show_folder": "Mostrar carpeta del Sketch",
        "adv_insert_template": "Insertar plantilla base ESP32",
        "adv_backup": "Crear respaldo del Sketch (.bak)",
        "adv_info": "Información y estadísticas del Sketch…",
        "adv_reload": "Recargar archivo desde el disco",
        "adv_reset_prefs": "Restablecer preferencias por defecto",
        "new_title": "Nuevo Sketch",
        "status_ready": "Listo",
        "status_modified": "Modificado (sin guardar)",
        "status_saved": "Guardado",
    },
    "en": {
        "menu_file": "File",
        "new_sketch": "New Sketch",
        "open": "Open…",
        "recent": "Open Recent",
        "sketchbook": "Sketchbook",
        "examples": "Examples",
        "close": "Close",
        "save": "Save",
        "save_as": "Save As…",
        "preferences": "Preferences…",
        "advanced": "Advanced",
        "exit": "Quit",
        "no_recent": "(No recent files)",
        "clear_recent": "Clear recent history",
        "empty_sketchbook": "(Empty Sketchbook folder)",
        "open_sketchbook_dir": "Open Sketchbook folder…",
        "refresh_sketchbook": "Refresh Sketchbook list",
        "adv_show_folder": "Show Sketch Folder",
        "adv_insert_template": "Insert ESP32 Base Template",
        "adv_backup": "Create Sketch Backup (.bak)",
        "adv_info": "Sketch Information & Statistics…",
        "adv_reload": "Reload File from Disk",
        "adv_reset_prefs": "Reset Default Preferences",
        "new_title": "New Sketch",
        "status_ready": "Ready",
        "status_modified": "Modified (unsaved)",
        "status_saved": "Saved",
    },
}


class ExamplesCatalog:
    """Catálogo de ejemplos integrados organizados por categoría para ESP32."""

    CATEGORIES: dict[str, dict[str, str]] = {
        "01. Básicos": {
            "01_Plantilla_Minima": DEFAULT_SKETCH_TEMPLATE,
            "02_Blink_LED_ESP32": """// Ejemplo: Parpadeo del LED integrado en ESP32 (GPIO 2)
const int PIN_LED = 2;

void setup() {
  pinMode(PIN_LED, OUTPUT);
}

void loop() {
  digitalWrite(PIN_LED, HIGH);
  delay(1000);
  digitalWrite(PIN_LED, LOW);
  delay(1000);
}
""",
            "03_Monitor_Serial": """// Ejemplo: Comunicación por puerto serie en ESP32
int contador = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== ESP32 Inicializado ===");
}

void loop() {
  Serial.print("Ciclo de ejecución #");
  Serial.println(contador++);
  delay(2000);
}
""",
        },
        "02. Digital y PWM": {
            "01_Lectura_Boton": """// Ejemplo: Lectura de botón con resistencia pull-up interna en ESP32
const int PIN_BOTON = 4;
const int PIN_LED = 2;

void setup() {
  pinMode(PIN_BOTON, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
}

void loop() {
  int estado = digitalRead(PIN_BOTON);
  digitalWrite(PIN_LED, estado == LOW ? HIGH : LOW);
}
""",
            "02_Brillo_LED_PWM": """// Ejemplo: Control de brillo gradual en ESP32
const int PIN_LED = 2;

void setup() {
  pinMode(PIN_LED, OUTPUT);
}

void loop() {
  for (int brillo = 0; brillo <= 255; brillo += 5) {
    analogWrite(PIN_LED, brillo);
    delay(20);
  }
  for (int brillo = 255; brillo >= 0; brillo -= 5) {
    analogWrite(PIN_LED, brillo);
    delay(20);
  }
}
""",
        },
        "03. Sensores y ADC": {
            "01_Lectura_ADC_12Bits": """// Ejemplo: Lectura analógica (ADC de 12 bits: 0 a 4095 en ESP32)
const int PIN_SENSOR = 34;

void setup() {
  Serial.begin(115200);
}

void loop() {
  int valorADC = analogRead(PIN_SENSOR);
  float voltaje = (valorADC / 4095.0) * 3.3;
  Serial.printf("ADC: %d | Voltaje: %.2f V\\n", valorADC, voltaje);
  delay(1000);
}
""",
        },
        "04. WiFi ESP32": {
            "01_Escaner_Redes_WiFi": """// Ejemplo: Escaneo de redes WiFi cercanas con ESP32
#include "WiFi.h"

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
}

void loop() {
  Serial.println("Escaneando redes WiFi...");
  int n = WiFi.scanNetworks();
  Serial.printf("Se encontraron %d redes:\\n", n);
  for (int i = 0; i < n; ++i) {
    Serial.printf("%d: %s (%d dBm)\\n", i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i));
  }
  Serial.println("------------------------");
  delay(5000);
}
""",
        },
    }


class ConfigManager:
    """
    Gestiona la configuración del sistema de archivos del módulo Archivo:
    - Rutas multiplataforma
    - Carpeta de proyectos (Sketchbook) y bibliotecas (Sketchbook/libraries)
    - Historial de proyectos recientes
    - Preferencias generales del IDE
    """

    MAX_RECENT_FILES = 10
    RESERVED_DIRS = {"libraries", "build", ".git", "__pycache__", ".vscode", ".idea"}

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, "config_archivo.json")
        self.default_sketchbook = os.path.join(self.base_dir, "Sketchbook")
        self.settings = self._get_default_settings()
        self.load_config()
        self.ensure_sketchbook_exists()

    def _get_default_settings(self) -> dict:
        return {
            "language": "es",
            "theme": "claro",
            "font_family": "Consolas",
            "font_size": 11,
            "sketchbook_path": self.default_sketchbook,
            "libraries_path": os.path.join(self.default_sketchbook, "libraries"),
            "recent_files": [],
            "auto_backup_on_save": False,
        }

    def load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    defaults = self._get_default_settings()
                    for k in defaults:
                        if k in data:
                            defaults[k] = data[k]
                    sketchbook_dir = defaults.get("sketchbook_path") or self.default_sketchbook
                    defaults["sketchbook_path"] = sketchbook_dir
                    lib_path = data.get("libraries_path")
                    if not lib_path or not str(lib_path).strip():
                        defaults["libraries_path"] = os.path.join(sketchbook_dir, "libraries")
                    else:
                        defaults["libraries_path"] = str(lib_path).strip()
                    self.settings = defaults
            except Exception:
                self.settings = self._get_default_settings()
        else:
            self.save_config()
        return self.settings

    def save_config(self) -> bool:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def reset_defaults(self) -> dict:
        self.settings = self._get_default_settings()
        self.save_config()
        self.ensure_sketchbook_exists()
        return self.settings

    def get_libraries_path(self) -> str:
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        lib_path = self.settings.get("libraries_path")
        if not lib_path or not str(lib_path).strip():
            lib_path = os.path.join(sketchbook_dir, "libraries")
            self.settings["libraries_path"] = lib_path
        return str(lib_path)

    def ensure_sketchbook_exists(self) -> None:
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        self.settings["sketchbook_path"] = sketchbook_dir
        libraries_dir = self.get_libraries_path()
        try:
            os.makedirs(sketchbook_dir, exist_ok=True)
            os.makedirs(libraries_dir, exist_ok=True)
        except Exception:
            pass

    def add_recent_file(self, filepath: str) -> None:
        norm_path = os.path.abspath(filepath)
        recent: list[str] = self.settings.get("recent_files", [])
        if norm_path in recent:
            recent.remove(norm_path)
        recent.insert(0, norm_path)
        self.settings["recent_files"] = recent[: self.MAX_RECENT_FILES]
        self.save_config()

    def remove_recent_file(self, filepath: str) -> None:
        norm_path = os.path.abspath(filepath)
        recent: list[str] = self.settings.get("recent_files", [])
        if norm_path in recent:
            recent.remove(norm_path)
            self.settings["recent_files"] = recent
            self.save_config()

    def clear_recent_files(self) -> None:
        self.settings["recent_files"] = []
        self.save_config()

    def _is_ignored_dir(self, dirname: str) -> bool:
        return (
            dirname.startswith(".")
            or dirname in self.RESERVED_DIRS
            or dirname.lower() in self.RESERVED_DIRS
        )

    def list_sketchbook_projects_detailed(self) -> list[dict]:
        """
        Devuelve una lista detallada de proyectos en la carpeta Sketchbook.
        Cada elemento incluye: name, display_name, path, project_dir, files e is_folder_project.
        Ignora carpetas ocultas y RESERVED_DIRS.
        """
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        projects: list[dict] = []
        if not os.path.isdir(sketchbook_dir):
            return projects

        try:
            for entry in sorted(os.listdir(sketchbook_dir)):
                if entry.startswith("."):
                    continue
                full_path = os.path.join(sketchbook_dir, entry)
                if os.path.isfile(full_path):
                    if os.path.splitext(entry)[1].lower() in SUPPORTED_EXTENSIONS:
                        projects.append(
                            {
                                "name": os.path.splitext(entry)[0],
                                "display_name": entry,
                                "path": full_path,
                                "project_dir": sketchbook_dir,
                                "files": [full_path],
                                "is_folder_project": False,
                            }
                        )
                elif os.path.isdir(full_path):
                    if self._is_ignored_dir(entry):
                        continue
                    sub_files = [
                        sub
                        for sub in sorted(os.listdir(full_path))
                        if not sub.startswith(".")
                        and os.path.isfile(os.path.join(full_path, sub))
                        and os.path.splitext(sub)[1].lower() in SUPPORTED_EXTENSIONS
                    ]
                    if not sub_files:
                        continue

                    preferred_ino = f"{entry}.ino"
                    main_sub: str | None = None
                    for sub in sub_files:
                        if sub.lower() == preferred_ino.lower():
                            main_sub = sub
                            break
                    if main_sub is None:
                        ino_candidates = [s for s in sub_files if s.lower().endswith(".ino")]
                        main_sub = ino_candidates[0] if ino_candidates else sub_files[0]

                    main_path = os.path.join(full_path, main_sub)
                    all_files = [os.path.join(full_path, s) for s in sub_files]
                    projects.append(
                        {
                            "name": entry,
                            "display_name": f"{entry}/{main_sub}",
                            "path": main_path,
                            "project_dir": full_path,
                            "files": all_files,
                            "is_folder_project": True,
                        }
                    )
        except Exception:
            pass
        return projects

    def list_sketchbook_projects(self) -> list[tuple[str, str]]:
        """
        Devuelve una lista de tuplas (nombre_visible, ruta_archivo) con los
        proyectos dentro de la carpeta Sketchbook del usuario, ignorando
        carpetas ocultas y RESERVED_DIRS y priorizando <carpeta>.ino.
        """
        return [
            (proj["display_name"], proj["path"])
            for proj in self.list_sketchbook_projects_detailed()
        ]


class FileManager:
    """
    Gestor headless de archivos y proyectos para ESP32 IDE.
    Reutilizable tanto por la interfaz de escritorio (IDEApp) como por FastAPI.
    """

    def __init__(self, config_manager: ConfigManager | None = None):
        self.config_manager = config_manager or ConfigManager()

    def validate_extension(self, filepath: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida (.ino, .cpp, .c, .h)."""
        if not filepath:
            return False
        ext = os.path.splitext(str(filepath).strip())[1].lower()
        return ext in SUPPORTED_EXTENSIONS

    def resolve_open_path(self, path: str) -> str:
        """
        Resuelve la ruta a abrir: soporta un archivo válido o una carpeta de proyecto
        (buscando <carpeta>.ino o el primer .ino).
        Lanza ValueError si la extensión es inválida y FileNotFoundError si no existe.
        """
        if not path or not str(path).strip():
            raise FileNotFoundError("La ruta del archivo a abrir está vacía.")

        abs_path = os.path.abspath(str(path).strip())

        if os.path.isdir(abs_path):
            folder_name = os.path.basename(abs_path)
            preferred_ino = os.path.join(abs_path, f"{folder_name}.ino")
            if os.path.isfile(preferred_ino):
                return preferred_ino

            ino_files = [
                f
                for f in sorted(os.listdir(abs_path))
                if not f.startswith(".")
                and os.path.isfile(os.path.join(abs_path, f))
                and f.lower().endswith(".ino")
            ]
            if ino_files:
                return os.path.join(abs_path, ino_files[0])

            raise FileNotFoundError(
                f"No se encontró un archivo .ino dentro de la carpeta del proyecto: {abs_path}"
            )

        ext = os.path.splitext(abs_path)[1]
        if ext and not self.validate_extension(abs_path):
            raise ValueError(
                f"Extensión de archivo no soportada: '{ext}'. Extensiones válidas: {SUPPORTED_EXTENSIONS}"
            )

        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"El archivo no existe en la ruta especificada: {abs_path}")

        if not self.validate_extension(abs_path):
            raise ValueError(
                f"El archivo '{abs_path}' no tiene una extensión soportada ({SUPPORTED_EXTENSIONS})."
            )

        return abs_path

    def resolve_save_path(self, target_path: str, create_project_folder: bool = True) -> str:
        """
        Resuelve la ruta de guardado:
        - Agrega .ino si falta extensión.
        - Valida que la extensión esté soportada.
        - Si create_project_folder=True, la extensión es .ino, el archivo NO existe
          todavía en disco y el nombre de la carpeta padre no coincide con el nombre
          del archivo, reubica a <parent>/<Nombre>/<Nombre>.ino.
        - Nunca mueve archivos .ino que ya existan en disco.
        """
        if not target_path or not str(target_path).strip():
            raise ValueError("La ruta de destino para guardar está vacía.")

        abs_target = os.path.abspath(str(target_path).strip())
        _, ext = os.path.splitext(abs_target)
        if not ext:
            abs_target = f"{abs_target}.ino"
            ext = ".ino"

        if not self.validate_extension(abs_target):
            raise ValueError(
                f"Extensión de archivo no soportada: '{ext}'. Extensiones válidas: {SUPPORTED_EXTENSIONS}"
            )

        if create_project_folder and ext.lower() == ".ino" and not os.path.exists(abs_target):
            parent_dir = os.path.dirname(abs_target)
            parent_name = os.path.basename(parent_dir)
            sketch_name = os.path.splitext(os.path.basename(abs_target))[0]
            if parent_name != sketch_name:
                abs_target = os.path.join(parent_dir, sketch_name, f"{sketch_name}.ino")

        return abs_target

    def read_file(self, path: str) -> tuple[str, str, str]:
        """
        Lee un archivo en UTF-8 con fallback automático a Latin-1, lo registra en
        recientes y devuelve (resolved_path, content, used_encoding).
        """
        resolved_path = self.resolve_open_path(path)
        used_encoding = "utf-8"
        try:
            with open(resolved_path, "r", encoding="utf-8") as f_obj:
                content = f_obj.read()
        except UnicodeDecodeError:
            used_encoding = "latin-1"
            with open(resolved_path, "r", encoding="latin-1") as f_obj:
                content = f_obj.read()

        self.config_manager.add_recent_file(resolved_path)
        return resolved_path, content, used_encoding

    def write_file(
        self,
        target_path: str,
        content: str,
        create_project_folder: bool = True,
        auto_backup: bool | None = None,
    ) -> tuple[str, list[str]]:
        """
        Crea directorios padre, genera respaldo .bak si auto_backup_on_save está
        activo y el archivo ya existía, escribe en UTF-8, agrega a recientes y
        devuelve (resolved_path, generated_files).
        """
        resolved_path = self.resolve_save_path(
            target_path,
            create_project_folder=create_project_folder,
        )
        os.makedirs(os.path.dirname(resolved_path), exist_ok=True)

        should_backup = (
            bool(self.config_manager.settings.get("auto_backup_on_save", False))
            if auto_backup is None
            else bool(auto_backup)
        )

        generated_files: list[str] = [resolved_path]
        if should_backup and os.path.exists(resolved_path):
            bak_path = f"{resolved_path}.bak"
            shutil.copy2(resolved_path, bak_path)
            generated_files.append(bak_path)

        with open(resolved_path, "w", encoding="utf-8", newline="") as f_obj:
            f_obj.write(content)

        self.config_manager.add_recent_file(resolved_path)
        return resolved_path, generated_files

    def create_backup(self, filepath: str, content_override: str | None = None) -> str:
        """Genera un archivo de respaldo <filepath>.bak y devuelve su ruta absoluta."""
        if not filepath or not str(filepath).strip():
            raise ValueError("Se requiere una ruta de archivo válida para crear respaldo.")

        abs_path = os.path.abspath(str(filepath).strip())
        backup_path = f"{abs_path}.bak"

        if content_override is not None:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(backup_path, "w", encoding="utf-8", newline="") as f_obj:
                f_obj.write(content_override)
        else:
            if not os.path.isfile(abs_path):
                raise FileNotFoundError(f"El archivo original no existe en disco: {abs_path}")
            shutil.copy2(abs_path, backup_path)

        return backup_path

    def get_project_info(self, filepath: str | None) -> dict:
        """
        Devuelve la información completa del proyecto activo para sincronización con
        el módulo Sketch / Compilación.
        """
        sketchbook_path = (
            self.config_manager.settings.get("sketchbook_path")
            or self.config_manager.default_sketchbook
        )
        libraries_path = self.config_manager.get_libraries_path()

        if not filepath or not str(filepath).strip():
            return {
                "has_active_project": False,
                "filepath": None,
                "project_dir": None,
                "project_name": None,
                "main_file": None,
                "project_files": [],
                "is_standard_arduino_layout": False,
                "sketchbook_path": sketchbook_path,
                "libraries_path": libraries_path,
            }

        abs_path = os.path.abspath(str(filepath).strip())
        if os.path.isdir(abs_path):
            project_dir = abs_path
            folder_name = os.path.basename(project_dir)
            preferred_ino = os.path.join(project_dir, f"{folder_name}.ino")
            if os.path.isfile(preferred_ino):
                main_file: str | None = preferred_ino
            else:
                inos = [
                    os.path.join(project_dir, f)
                    for f in sorted(os.listdir(project_dir))
                    if not f.startswith(".")
                    and os.path.isfile(os.path.join(project_dir, f))
                    and f.lower().endswith(".ino")
                ]
                main_file = inos[0] if inos else None
            active_filepath = main_file or abs_path
            project_name = folder_name
        else:
            active_filepath = abs_path
            project_dir = os.path.dirname(abs_path)
            folder_name = os.path.basename(project_dir)
            file_stem = os.path.splitext(os.path.basename(abs_path))[0]
            preferred_ino = os.path.join(project_dir, f"{folder_name}.ino")

            if os.path.isfile(preferred_ino):
                project_name = folder_name
                main_file = preferred_ino
            elif folder_name == file_stem and abs_path.lower().endswith(".ino"):
                project_name = folder_name
                main_file = abs_path
            else:
                project_name = file_stem
                if abs_path.lower().endswith(".ino"):
                    main_file = abs_path
                elif os.path.isdir(project_dir):
                    inos = [
                        os.path.join(project_dir, f)
                        for f in sorted(os.listdir(project_dir))
                        if not f.startswith(".")
                        and os.path.isfile(os.path.join(project_dir, f))
                        and f.lower().endswith(".ino")
                    ]
                    main_file = inos[0] if inos else abs_path
                else:
                    main_file = abs_path

        project_files: list[str] = []
        if os.path.isdir(project_dir):
            for entry in sorted(os.listdir(project_dir)):
                if entry.startswith("."):
                    continue
                full_entry = os.path.join(project_dir, entry)
                if os.path.isfile(full_entry) and self.validate_extension(full_entry):
                    project_files.append(full_entry)

        if (
            os.path.isfile(active_filepath)
            and self.validate_extension(active_filepath)
            and active_filepath not in project_files
        ):
            project_files.append(active_filepath)

        expected_standard_ino = os.path.join(project_dir, f"{os.path.basename(project_dir)}.ino")
        is_standard_layout = bool(
            os.path.basename(project_dir) == project_name
            and (
                os.path.isfile(expected_standard_ino)
                or os.path.normcase(active_filepath) == os.path.normcase(expected_standard_ino)
            )
        )

        return {
            "has_active_project": True,
            "filepath": active_filepath,
            "project_dir": project_dir,
            "project_name": project_name,
            "main_file": main_file,
            "project_files": project_files,
            "is_standard_arduino_layout": is_standard_layout,
            "sketchbook_path": sketchbook_path,
            "libraries_path": libraries_path,
        }

    def create_project_file(self, project_dir: str, filename: str, content: str = "") -> str:
        """
        Crea un archivo secundario (.h, .cpp, .c, .ino) dentro de project_dir.
        Valida que no exista path traversal (../, /, \\), que la extensión sea válida
        y que el archivo no exista previamente (FileExistsError).
        """
        if not project_dir or not str(project_dir).strip():
            raise ValueError("Se requiere un directorio de proyecto válido.")

        clean_name = (filename or "").strip()
        if (
            not clean_name
            or ".." in clean_name
            or "/" in clean_name
            or "\\" in clean_name
            or os.path.basename(clean_name) != clean_name
        ):
            raise ValueError(
                f"Nombre de archivo inválido o intento de path traversal: '{filename}'"
            )

        if not self.validate_extension(clean_name):
            raise ValueError(
                f"Extensión de archivo no soportada para '{clean_name}'. Extensiones válidas: {SUPPORTED_EXTENSIONS}"
            )

        abs_project_dir = os.path.abspath(str(project_dir).strip())
        os.makedirs(abs_project_dir, exist_ok=True)
        target_path = os.path.abspath(os.path.join(abs_project_dir, clean_name))

        if os.path.dirname(target_path) != abs_project_dir:
            raise ValueError(f"Ruta fuera del directorio del proyecto: '{filename}'")

        if os.path.exists(target_path):
            raise FileExistsError(f"El archivo ya existe en el proyecto: {target_path}")

        with open(target_path, "w", encoding="utf-8", newline="") as f_obj:
            f_obj.write(content)

        return target_path

    def get_sketch_stats(
        self,
        content: str | None = None,
        filepath: str | None = None,
        encoding: str = "utf-8",
    ) -> dict:
        """
        Calcula estadísticas del sketch (lines, chars, size_bytes, encoding y project_info).
        Si content es None y filepath existe en disco, lee el archivo automáticamente.
        """
        used_encoding = encoding or "utf-8"
        text_content = content

        if text_content is None and filepath and os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f_obj:
                    text_content = f_obj.read()
                used_encoding = "utf-8"
            except UnicodeDecodeError:
                with open(filepath, "r", encoding="latin-1") as f_obj:
                    text_content = f_obj.read()
                used_encoding = "latin-1"

        text = text_content or ""
        lines = text.count("\n") + 1 if text else 0
        chars = len(text)
        size_bytes = len(text.encode(used_encoding, errors="replace"))

        return {
            "lines": lines,
            "chars": chars,
            "size_bytes": size_bytes,
            "encoding": used_encoding,
            "project_info": self.get_project_info(filepath),
        }


class IDEApp:
    """
    Clase principal que integra la interfaz de prueba del editor, el menú Archivo
    completo, los submenús dinámicos, las preferencias y los atajos de teclado.
    """

    def __init__(self, root: tk.Tk, config_manager: ConfigManager | None = None):
        self.root = root
        self.config_manager = config_manager or ConfigManager()
        self.file_manager = FileManager(self.config_manager)

        # Estado del archivo actual
        self.current_file: str | None = None
        self.current_encoding: str = "utf-8"

        # Configuración de la ventana principal
        self.root.geometry("950x620")
        self.root.minsize(480, 340)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Interceptar el botón de cerrar ventana (X) para validar cambios sin guardar
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Editor de texto principal
        font_family = self.config_manager.settings.get("font_family", "Consolas")
        font_size = int(self.config_manager.settings.get("font_size", 11))
        self.editor = tk.Text(
            self.root,
            wrap="none",
            undo=True,
            font=(font_family, font_size),
            tabs=("1c",),
        )

        # Barras de desplazamiento
        vert_scroll = tk.Scrollbar(self.root, orient="vertical", command=self.editor.yview)
        horiz_scroll = tk.Scrollbar(self.root, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=vert_scroll.set, xscrollcommand=horiz_scroll.set)

        self.editor.grid(row=0, column=0, sticky="nsew")
        vert_scroll.grid(row=0, column=1, sticky="ns")
        horiz_scroll.grid(row=1, column=0, sticky="ew")

        # Barra de estado inferior para mostrar ruta, estado de cambios y codificación
        self.status_var = tk.StringVar(value="Listo")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            relief=tk.SUNKEN,
            padx=8,
            pady=3,
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

        # Detectar modificaciones en el editor para actualizar el asterisco (*) en el título
        self.editor.bind("<<Modified>>", self._on_editor_modified)

        # Construcción del menú Archivo y submenús
        self._build_menus()

        # Registro de atajos de teclado tanto en ventana como en el editor
        self._bind_shortcuts()

        # Aplicar tema visual configurado e inicializar con la plantilla base ESP32
        self.apply_preferences_to_ui()
        self._load_content_into_editor(DEFAULT_SKETCH_TEMPLATE, filepath=None)

    # -------------------------------------------------------------------------
    # Traducción e interfaz
    # -------------------------------------------------------------------------
    def _t(self, key: str) -> str:
        lang = self.config_manager.settings.get("language", "es")
        lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["es"])
        return lang_dict.get(key, key)

    def _build_menus(self) -> None:
        """Construye la barra de menú siguiendo la estructura local de Arduino IDE 2.3.10."""
        self.main_menubar = tk.Menu(self.root)
        self.file_dropdown = tk.Menu(self.main_menubar, tearoff=False)

        # Submenús secundarios
        self.recent_menu = tk.Menu(self.file_dropdown, tearoff=False)
        self.sketchbook_menu = tk.Menu(self.file_dropdown, tearoff=False)
        self.examples_menu = tk.Menu(self.file_dropdown, tearoff=False)
        self.advanced_menu = tk.Menu(self.file_dropdown, tearoff=False)

        # Opciones principales del menú Archivo
        self.file_dropdown.add_command(
            label=self._t("new_sketch"),
            accelerator="Ctrl+N",
            command=self.new_file,
        )
        self.file_dropdown.add_command(
            label=self._t("open"),
            accelerator="Ctrl+O",
            command=self.open_file,
        )
        self.file_dropdown.add_cascade(
            label=self._t("recent"),
            menu=self.recent_menu,
        )
        self.file_dropdown.add_cascade(
            label=self._t("sketchbook"),
            menu=self.sketchbook_menu,
        )
        self.file_dropdown.add_cascade(
            label=self._t("examples"),
            menu=self.examples_menu,
        )
        self.file_dropdown.add_command(
            label=self._t("close"),
            accelerator="Ctrl+W",
            command=self.close_file,
        )
        self.file_dropdown.add_command(
            label=self._t("save"),
            accelerator="Ctrl+S",
            command=self.save_file,
        )
        self.file_dropdown.add_command(
            label=self._t("save_as"),
            accelerator="Ctrl+Mayús+S",
            command=self.save_as,
        )
        self.file_dropdown.add_separator()
        self.file_dropdown.add_command(
            label=self._t("preferences"),
            accelerator="Ctrl+Coma",
            command=self.open_preferences_dialog,
        )
        self.file_dropdown.add_separator()
        self.file_dropdown.add_cascade(
            label=self._t("advanced"),
            menu=self.advanced_menu,
        )
        self.file_dropdown.add_separator()
        self.file_dropdown.add_command(
            label=self._t("exit"),
            accelerator="Ctrl+Q",
            command=self.exit_app,
        )

        self.main_menubar.add_cascade(label=self._t("menu_file"), menu=self.file_dropdown)
        self.root.config(menu=self.main_menubar)

        # Poblar los submenús
        self.refresh_recent_menu()
        self.refresh_sketchbook_menu()
        self._populate_examples_menu()
        self._populate_advanced_menu()

    def _bind_shortcuts(self) -> None:
        """
        Registra los atajos de teclado tanto en la ventana raíz como directamente
        en el widget Text (self.editor), evitando que la clase Text intercepte
        combinaciones como Ctrl+O.
        """
        shortcuts = [
            ("<Control-n>", self.new_file),
            ("<Control-N>", self.new_file),
            ("<Control-o>", self.open_file),
            ("<Control-O>", self.open_file),
            ("<Control-w>", self.close_file),
            ("<Control-W>", self.close_file),
            ("<Control-s>", self.save_file),
            ("<Control-S>", self.save_as),
            ("<Control-Shift-s>", self.save_as),
            ("<Control-Shift-S>", self.save_as),
            ("<Control-comma>", self.open_preferences_dialog),
            ("<Control-q>", self.exit_app),
            ("<Control-Q>", self.exit_app),
        ]
        for sequence, callback in shortcuts:
            self.root.bind(sequence, callback)
            self.editor.bind(sequence, callback)

    def apply_preferences_to_ui(self) -> None:
        """Aplica el tema visual y tamaño de fuente guardados en Preferencias."""
        settings = self.config_manager.settings
        font_family = settings.get("font_family", "Consolas")
        font_size = int(settings.get("font_size", 11))
        theme = settings.get("theme", "claro")

        self.editor.configure(font=(font_family, font_size))

        if theme == "oscuro":
            self.editor.configure(
                bg="#1E1E1E",
                fg="#D4D4D4",
                insertbackground="#FFFFFF",
                selectbackground="#264F78",
                selectforeground="#FFFFFF",
            )
            self.status_bar.configure(bg="#252526", fg="#CCCCCC")
        else:
            self.editor.configure(
                bg="#FFFFFF",
                fg="#1E1E1E",
                insertbackground="#000000",
                selectbackground="#ADD6FF",
                selectforeground="#000000",
            )
            self.status_bar.configure(bg="#F0F0F0", fg="#222222")

        self.update_title()

    def _on_editor_modified(self, event=None) -> None:
        """Se activa cuando cambia el estado edit_modified del editor."""
        self.update_title()

    def update_title(self) -> None:
        """Actualiza el título de la ventana y la barra de estado."""
        if self.current_file is not None:
            fname = os.path.basename(self.current_file)
            location_info = self.current_file
        else:
            fname = self._t("new_title")
            location_info = f"({self._t('new_title')})"

        modified = bool(self.editor.edit_modified())
        dirty_mark = "*" if modified else ""

        self.root.title(f"{dirty_mark}{fname} - {APP_NAME}")

        status_state = self._t("status_modified") if modified else self._t("status_ready")
        self.status_var.set(
            f" {status_state}  |  Archivo: {location_info}  |  Codificación: {self.current_encoding.upper()}"
        )

    # -------------------------------------------------------------------------
    # Control de cambios sin guardar y carga de texto
    # -------------------------------------------------------------------------
    def check_unsaved_changes(self) -> bool:
        """
        Verifica si hay cambios sin guardar en el editor.
        Retorna True si se puede continuar con la acción, o False si el usuario cancela.
        """
        if not self.editor.edit_modified():
            return True

        fname = os.path.basename(self.current_file) if self.current_file else self._t("new_title")
        response = messagebox.askyesnocancel(
            "Cambios sin guardar",
            f"¿Deseas guardar los cambios realizados en '{fname}' antes de continuar?",
        )
        if response is None:
            return False
        if response is True:
            return self._perform_save_and_confirm()
        return True

    def _perform_save_and_confirm(self) -> bool:
        if self.current_file:
            return self.write_to_file(self.current_file, create_project_folder=False)
        return self._save_as_bool()

    def _load_content_into_editor(
        self,
        content: str,
        filepath: str | None,
        encoding: str = "utf-8",
    ) -> None:
        """Reemplaza el texto del editor y reinicia el historial de deshacer y modificado."""
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", content)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.current_file = filepath
        self.current_encoding = encoding
        self.update_title()

    # -------------------------------------------------------------------------
    # Funciones principales: Nuevo, Abrir, Guardar, Guardar como, Cerrar, Salir
    # -------------------------------------------------------------------------
    def new_file(self, event=None) -> str:
        """Inicializa un nuevo sketch con la plantilla base ESP32 sin marcar como modificado."""
        if not self.check_unsaved_changes():
            return "break"

        self._load_content_into_editor(DEFAULT_SKETCH_TEMPLATE, filepath=None)
        return "break"

    def open_file(self, event=None, filepath: str | None = None) -> str:
        """
        Abre un archivo existente validando primero cambios sin guardar.
        Soporta UTF-8 con respaldo automático a Latin-1 para sketches antiguos.
        """
        if not self.check_unsaved_changes():
            return "break"

        if not filepath:
            initial_dir = self.config_manager.settings.get("sketchbook_path", "")
            if not os.path.isdir(initial_dir):
                initial_dir = os.getcwd()
            filepath = filedialog.askopenfilename(
                title="Abrir sketch",
                initialdir=initial_dir,
                filetypes=FILE_TYPES,
            )

        if filepath:
            self._open_from_path(filepath)

        return "break"

    def _open_from_path(self, filepath: str) -> bool:
        """Delegado en FileManager para leer desde disco manejando codificaciones y errores."""
        try:
            resolved_path, content, used_encoding = self.file_manager.read_file(filepath)
            self._load_content_into_editor(
                content,
                filepath=resolved_path,
                encoding=used_encoding,
            )
            self.refresh_recent_menu()
            return True

        except FileNotFoundError:
            messagebox.showerror(
                "Archivo no encontrado",
                f"El archivo no existe en la ruta especificada:\n{filepath}",
            )
            self.config_manager.remove_recent_file(filepath)
            self.refresh_recent_menu()
        except ValueError as e:
            messagebox.showerror(
                "Extensión no válida",
                str(e),
            )
        except PermissionError:
            messagebox.showerror(
                "Error de permisos",
                f"No tienes permisos de lectura para abrir el archivo:\n{filepath}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error al abrir",
                f"No se pudo abrir el archivo:\n{filepath}\n\nDetalle: {e}",
            )
        return False

    def save_file(self, event=None) -> str:
        """Guarda el archivo actual in-place o invoca Guardar como si aún no tiene ruta."""
        if self.current_file:
            self.write_to_file(self.current_file, create_project_folder=False)
        else:
            self.save_as()
        return "break"

    def save_as(self, event=None) -> str:
        """Solicita ubicación para guardar el archivo actual."""
        self._save_as_bool()
        return "break"

    def _save_as_bool(self) -> bool:
        initial_dir = self.config_manager.settings.get("sketchbook_path", "")
        if not os.path.isdir(initial_dir):
            initial_dir = os.getcwd()

        filepath = filedialog.asksaveasfilename(
            title="Guardar como",
            initialdir=initial_dir,
            filetypes=FILE_TYPES,
            defaultextension=".ino",
        )
        if filepath:
            return self.write_to_file(filepath, create_project_folder=True)
        return False

    def write_to_file(self, target_path: str, create_project_folder: bool = False) -> bool:
        """Delegado en FileManager para escribir el contenido del editor en disco."""
        try:
            text_content = self.editor.get("1.0", "end-1c")
            resolved_path, _ = self.file_manager.write_file(
                target_path,
                text_content,
                create_project_folder=create_project_folder,
            )

            self.current_file = resolved_path
            self.current_encoding = "utf-8"
            self.editor.edit_modified(False)
            self.refresh_recent_menu()
            self.refresh_sketchbook_menu()
            self.update_title()
            return True

        except ValueError as e:
            messagebox.showerror("Extensión no válida", str(e))
        except PermissionError:
            messagebox.showerror(
                "Error de permisos",
                f"No tienes permisos de escritura en la ubicación seleccionada:\n{target_path}",
            )
        except OSError as e:
            messagebox.showerror(
                "Error de escritura en disco",
                f"No se pudo guardar el archivo en disco:\n{target_path}\n\nDetalle: {e}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
        return False

    def close_file(self, event=None) -> str:
        """
        Cierra el proyecto actual verificando si hay cambios sin guardar (Ctrl+W).
        Limpia el editor a "" sin archivo activo.
        """
        if not self.check_unsaved_changes():
            return "break"

        self._load_content_into_editor("", filepath=None)
        return "break"

    def exit_app(self, event=None) -> str:
        """
        Cierra la aplicación verificando primero si existen cambios sin guardar (Ctrl+Q).
        """
        if not self.check_unsaved_changes():
            return "break"

        self.config_manager.save_config()
        self.root.destroy()
        return "break"

    # -------------------------------------------------------------------------
    # Submenús secundarios: Abierto recientemente, Sketchbook y Ejemplos
    # -------------------------------------------------------------------------
    def refresh_recent_menu(self) -> None:
        """Actualiza el submenú 'Abierto recientemente' con el historial guardado."""
        self.recent_menu.delete(0, tk.END)
        recent_files: list[str] = self.config_manager.settings.get("recent_files", [])

        if not recent_files:
            self.recent_menu.add_command(label=self._t("no_recent"), state="disabled")
            return

        for idx, path in enumerate(recent_files, start=1):
            label = f"{idx}. {os.path.basename(path)}  ({path})"
            self.recent_menu.add_command(
                label=label,
                command=lambda p=path: self.open_file(filepath=p),
            )

        self.recent_menu.add_separator()
        self.recent_menu.add_command(
            label=self._t("clear_recent"),
            command=self._clear_recent_history,
        )

    def _clear_recent_history(self) -> None:
        self.config_manager.clear_recent_files()
        self.refresh_recent_menu()

    def refresh_sketchbook_menu(self) -> None:
        """Actualiza el submenú 'Sketchbook' listando los proyectos de la carpeta del usuario."""
        self.sketchbook_menu.delete(0, tk.END)
        projects = self.config_manager.list_sketchbook_projects()

        if not projects:
            self.sketchbook_menu.add_command(label=self._t("empty_sketchbook"), state="disabled")
        else:
            for display_name, full_path in projects:
                self.sketchbook_menu.add_command(
                    label=display_name,
                    command=lambda p=full_path: self.open_file(filepath=p),
                )

        self.sketchbook_menu.add_separator()
        self.sketchbook_menu.add_command(
            label=self._t("refresh_sketchbook"),
            command=self.refresh_sketchbook_menu,
        )
        self.sketchbook_menu.add_command(
            label=self._t("open_sketchbook_dir"),
            command=self._open_sketchbook_directory,
        )

    def _open_sketchbook_directory(self) -> None:
        sketchbook_dir = self.config_manager.settings.get("sketchbook_path", "")
        self.config_manager.ensure_sketchbook_exists()
        self._open_folder_in_os(sketchbook_dir)

    def _populate_examples_menu(self) -> None:
        """Construye el submenú 'Ejemplos' organizado por categorías."""
        self.examples_menu.delete(0, tk.END)
        for category, examples in ExamplesCatalog.CATEGORIES.items():
            cat_menu = tk.Menu(self.examples_menu, tearoff=False)
            for example_name, code in examples.items():
                cat_menu.add_command(
                    label=example_name,
                    command=lambda n=example_name, c=code: self.load_example(n, c),
                )
            self.examples_menu.add_cascade(label=category, menu=cat_menu)

    def load_example(self, example_name: str, code: str) -> None:
        """
        Carga un ejemplo en el editor dejando current_file en None para evitar
        sobrescribir la plantilla original y pedir ruta al guardar.
        """
        if not self.check_unsaved_changes():
            return

        self._load_content_into_editor(code, filepath=None)
        self.root.title(f"Ejemplo: {example_name} - {APP_NAME}")

    # -------------------------------------------------------------------------
    # Menú Avanzado y Ventana de Preferencias
    # -------------------------------------------------------------------------
    def _populate_advanced_menu(self) -> None:
        """Construye el submenú 'Avanzado' con herramientas esenciales de archivo."""
        self.advanced_menu.delete(0, tk.END)
        self.advanced_menu.add_command(
            label=self._t("adv_show_folder"),
            command=self.advanced_show_sketch_folder,
        )
        self.advanced_menu.add_command(
            label=self._t("adv_insert_template"),
            command=self.advanced_insert_base_template,
        )
        self.advanced_menu.add_command(
            label=self._t("adv_backup"),
            command=self.advanced_create_backup,
        )
        self.advanced_menu.add_command(
            label=self._t("adv_reload"),
            command=self.advanced_reload_from_disk,
        )
        self.advanced_menu.add_separator()
        self.advanced_menu.add_command(
            label=self._t("adv_info"),
            command=self.advanced_show_sketch_info,
        )
        self.advanced_menu.add_separator()
        self.advanced_menu.add_command(
            label=self._t("adv_reset_prefs"),
            command=self.advanced_reset_preferences,
        )

    def advanced_show_sketch_folder(self) -> None:
        """Abre la carpeta donde reside el sketch actual o la carpeta Sketchbook."""
        if self.current_file and os.path.exists(self.current_file):
            folder = os.path.dirname(os.path.abspath(self.current_file))
        else:
            folder = self.config_manager.settings.get("sketchbook_path", os.getcwd())
            self.config_manager.ensure_sketchbook_exists()
        self._open_folder_in_os(folder)

    def _open_folder_in_os(self, folder_path: str) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder_path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception:
            messagebox.showinfo("Ubicación de carpeta", f"Ruta de la carpeta:\n{folder_path}")

    def advanced_insert_base_template(self) -> None:
        """Inserta la estructura setup()/loop() en la posición actual del cursor."""
        self.editor.insert(tk.INSERT, "\n" + DEFAULT_SKETCH_TEMPLATE)

    def advanced_create_backup(self) -> None:
        """Delegado en FileManager para crear un archivo de respaldo (.bak) del sketch actual."""
        if not self.current_file:
            messagebox.showwarning(
                "Respaldo de Sketch",
                "Primero debes guardar el sketch en disco antes de generar un archivo de respaldo (.bak).",
            )
            return

        try:
            text_content = self.editor.get("1.0", "end-1c")
            backup_path = self.file_manager.create_backup(
                self.current_file,
                content_override=text_content,
            )
            messagebox.showinfo(
                "Respaldo creado",
                f"Se creó la copia de seguridad correctamente en:\n{backup_path}",
            )
        except Exception as e:
            messagebox.showerror("Error al crear respaldo", f"No se pudo crear el respaldo:\n{e}")

    def advanced_reload_from_disk(self) -> None:
        """Recarga el archivo actual desde el disco."""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showinfo(
                "Recargar desde disco",
                "No hay un archivo guardado en disco asociado al sketch actual.",
            )
            return

        if self.editor.edit_modified():
            confirm = messagebox.askyesno(
                "Recargar desde disco",
                "Se perderán los cambios no guardados en el editor. ¿Deseas recargar el archivo desde el disco?",
            )
            if not confirm:
                return

        self._open_from_path(self.current_file)

    def advanced_show_sketch_info(self) -> None:
        """Delegado en FileManager para mostrar información técnica y estadísticas del sketch."""
        content = self.editor.get("1.0", "end-1c")
        stats = self.file_manager.get_sketch_stats(
            content=content,
            filepath=self.current_file,
            encoding=self.current_encoding,
        )
        proj = stats["project_info"]
        filepath = self.current_file or "(Sin guardar en disco)"
        project_dir = proj.get("project_dir") or "(Sin carpeta de proyecto)"
        modified = "Sí" if self.editor.edit_modified() else "No"

        info_text = (
            f"Nombre: {os.path.basename(self.current_file) if self.current_file else self._t('new_title')}\n"
            f"Ruta: {filepath}\n"
            f"Carpeta del proyecto: {project_dir}\n"
            f"Codificación: {stats['encoding'].upper()}\n"
            f"Líneas de código: {stats['lines']}\n"
            f"Caracteres: {stats['chars']}\n"
            f"Tamaño en memoria (UTF-8): {stats['size_bytes']} bytes\n"
            f"Cambios sin guardar: {modified}\n"
            f"Carpeta Sketchbook: {proj.get('sketchbook_path')}\n"
            f"Carpeta Bibliotecas: {proj.get('libraries_path')}"
        )
        messagebox.showinfo("Información del Sketch", info_text)

    def advanced_reset_preferences(self) -> None:
        """Restablece la configuración por defecto previa confirmación."""
        confirm = messagebox.askyesno(
            "Restablecer preferencias",
            "¿Deseas restaurar todas las preferencias del módulo Archivo a sus valores originales?",
        )
        if confirm:
            self.config_manager.reset_defaults()
            self._build_menus()
            self.apply_preferences_to_ui()
            messagebox.showinfo("Preferencias", "Se han restablecido las preferencias por defecto.")

    def open_preferences_dialog(self, event=None) -> str:
        """
        Abre la ventana modal de Preferencias (Ctrl+,) contemplando:
        - Ubicación de la carpeta de proyectos (Sketchbook)
        - Ubicación de la carpeta de bibliotecas (Sketchbook/libraries)
        - Idioma de la interfaz (Español / Inglés)
        - Tema visual (Claro / Oscuro)
        - Tamaño de fuente del editor
        - Respaldo automático (.bak) al guardar
        """
        pref_win = tk.Toplevel(self.root)
        pref_win.title("Preferencias — ESP32 IDE")
        pref_win.geometry("580x360")
        pref_win.resizable(False, False)
        pref_win.transient(self.root)
        pref_win.grab_set()

        frame = ttk.Frame(pref_win, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        settings = self.config_manager.settings

        # 1. Ubicación del Sketchbook
        ttk.Label(frame, text="Ubicación del Sketchbook:").grid(row=0, column=0, sticky="w", pady=6)
        sketchbook_var = tk.StringVar(value=settings.get("sketchbook_path", ""))
        sketchbook_entry = ttk.Entry(frame, textvariable=sketchbook_var)
        sketchbook_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8), pady=6)

        # 2. Carpeta de bibliotecas
        ttk.Label(frame, text="Carpeta de bibliotecas:").grid(row=1, column=0, sticky="w", pady=6)
        libraries_var = tk.StringVar(value=self.config_manager.get_libraries_path())
        libraries_entry = ttk.Entry(frame, textvariable=libraries_var)
        libraries_entry.grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=6)

        def browse_sketchbook() -> None:
            old_sketchbook = sketchbook_var.get().strip()
            old_default_lib = os.path.join(old_sketchbook, "libraries") if old_sketchbook else ""
            selected = filedialog.askdirectory(
                title="Seleccionar carpeta Sketchbook",
                initialdir=old_sketchbook or os.getcwd(),
                parent=pref_win,
            )
            if selected:
                sketchbook_var.set(selected)
                current_lib = libraries_var.get().strip()
                if not current_lib or os.path.normcase(current_lib) == os.path.normcase(old_default_lib):
                    libraries_var.set(os.path.join(selected, "libraries"))

        def browse_libraries() -> None:
            selected = filedialog.askdirectory(
                title="Seleccionar carpeta de bibliotecas",
                initialdir=libraries_var.get() or sketchbook_var.get() or os.getcwd(),
                parent=pref_win,
            )
            if selected:
                libraries_var.set(selected)

        ttk.Button(frame, text="Examinar…", command=browse_sketchbook).grid(row=0, column=2, pady=6)
        ttk.Button(frame, text="Examinar…", command=browse_libraries).grid(row=1, column=2, pady=6)

        # 3. Idioma de la interfaz
        ttk.Label(frame, text="Idioma de la interfaz:").grid(row=2, column=0, sticky="w", pady=6)
        lang_map = {"Español (es)": "es", "English (en)": "en"}
        inv_lang_map = {v: k for k, v in lang_map.items()}
        lang_var = tk.StringVar(value=inv_lang_map.get(settings.get("language", "es"), "Español (es)"))
        lang_combo = ttk.Combobox(
            frame,
            textvariable=lang_var,
            values=list(lang_map.keys()),
            state="readonly",
        )
        lang_combo.grid(row=2, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=6)

        # 4. Tema visual
        ttk.Label(frame, text="Tema visual:").grid(row=3, column=0, sticky="w", pady=6)
        theme_map = {"Claro": "claro", "Oscuro": "oscuro"}
        inv_theme_map = {v: k for k, v in theme_map.items()}
        theme_var = tk.StringVar(value=inv_theme_map.get(settings.get("theme", "claro"), "Claro"))
        theme_combo = ttk.Combobox(
            frame,
            textvariable=theme_var,
            values=list(theme_map.keys()),
            state="readonly",
        )
        theme_combo.grid(row=3, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=6)

        # 5. Tamaño de fuente del editor
        ttk.Label(frame, text="Tamaño de fuente (Editor):").grid(row=4, column=0, sticky="w", pady=6)
        font_size_var = tk.IntVar(value=int(settings.get("font_size", 11)))
        font_spin = ttk.Spinbox(frame, from_=8, to=28, textvariable=font_size_var, width=8)
        font_spin.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=6)

        # 6. Opción avanzada: Crear respaldo automático (.bak) al guardar
        auto_bak_var = tk.BooleanVar(value=bool(settings.get("auto_backup_on_save", False)))
        ttk.Checkbutton(
            frame,
            text="Crear copia de respaldo (.bak) automáticamente al guardar",
            variable=auto_bak_var,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=10)

        # Botones Guardar / Cancelar
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, sticky="e", pady=(16, 0))

        def save_preferences() -> None:
            try:
                f_size = max(8, min(28, int(font_size_var.get())))
            except ValueError:
                f_size = 11

            new_sketchbook = sketchbook_var.get().strip() or self.config_manager.default_sketchbook
            new_libraries = libraries_var.get().strip() or os.path.join(new_sketchbook, "libraries")
            settings["sketchbook_path"] = new_sketchbook
            settings["libraries_path"] = new_libraries
            settings["language"] = lang_map.get(lang_var.get(), "es")
            settings["theme"] = theme_map.get(theme_var.get(), "claro")
            settings["font_size"] = f_size
            settings["auto_backup_on_save"] = bool(auto_bak_var.get())

            self.config_manager.save_config()
            self.config_manager.ensure_sketchbook_exists()
            self._build_menus()
            self.apply_preferences_to_ui()
            pref_win.destroy()

        ttk.Button(btn_frame, text="Cancelar", command=pref_win.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="Guardar preferencias", command=save_preferences).pack(side="right")

        return "break"


if __name__ == "__main__":
    app_window = tk.Tk()
    app = IDEApp(app_window)
    app_window.mainloop()

