# Archivo: modules/archivo/backend/archivo_backend/config.py
"""
Configuracion, preferencias y gestor headless de archivos (FileManager) del modulo Archivo.

Compartido entre el backend FastAPI y el prototipo de escritorio (main.py),
sin requerir dependencias de interfaz grafica al importarse desde el servidor.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Dict, List, Optional, Tuple

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

    CATEGORIES: Dict[str, Dict[str, str]] = {
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

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, "config_archivo.json")
        self.default_sketchbook = os.path.join(self.base_dir, "Sketchbook")
        self.settings = self._get_default_settings()
        self.load_config()
        self.ensure_sketchbook_exists()

    def _get_default_settings(self) -> Dict:
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

    def load_config(self) -> Dict:
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

    def reset_defaults(self) -> Dict:
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
        recent: List[str] = self.settings.get("recent_files", [])
        if norm_path in recent:
            recent.remove(norm_path)
        recent.insert(0, norm_path)
        self.settings["recent_files"] = recent[: self.MAX_RECENT_FILES]
        self.save_config()

    def remove_recent_file(self, filepath: str) -> None:
        norm_path = os.path.abspath(filepath)
        recent: List[str] = self.settings.get("recent_files", [])
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

    def list_sketchbook_projects_detailed(self) -> List[Dict]:
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        projects: List[Dict] = []
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
                    main_sub: Optional[str] = None
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

    def list_sketchbook_projects(self) -> List[Tuple[str, str]]:
        """
        Devuelve una lista de tuplas (nombre_visible, ruta_archivo) con los
        proyectos dentro de la carpeta Sketchbook del usuario.
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

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()

    def validate_extension(self, filepath: str) -> bool:
        if not filepath:
            return False
        ext = os.path.splitext(str(filepath).strip())[1].lower()
        return ext in SUPPORTED_EXTENSIONS

    def resolve_open_path(self, path: str) -> str:
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

    def read_file(self, path: str) -> Tuple[str, str, str]:
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
        auto_backup: Optional[bool] = None,
    ) -> Tuple[str, List[str]]:
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

        generated_files: List[str] = [resolved_path]
        if should_backup and os.path.exists(resolved_path):
            bak_path = f"{resolved_path}.bak"
            shutil.copy2(resolved_path, bak_path)
            generated_files.append(bak_path)

        with open(resolved_path, "w", encoding="utf-8", newline="") as f_obj:
            f_obj.write(content)

        self.config_manager.add_recent_file(resolved_path)
        return resolved_path, generated_files

    def create_backup(self, filepath: str, content_override: Optional[str] = None) -> str:
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

    def get_project_info(self, filepath: Optional[str]) -> Dict:
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
                main_file: Optional[str] = preferred_ino
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

        project_files: List[str] = []
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
        content: Optional[str] = None,
        filepath: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> Dict:
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
