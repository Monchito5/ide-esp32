"""
ESP32 IDE - Módulo de Archivo (Prototipo completo inspirado en Arduino IDE 2.3.10)
==================================================================================

Este módulo implementa todas las funciones del menú Archivo descritas en la
documentación de investigación y técnica del proyecto ESP32 IDE:

1. Arquitectura dividida en gestores:
   - ConfigManager: Rutas multiplataforma, carpeta Sketchbook, historial de
     archivos recientes y persistencia de Preferencias en JSON.
   - ExamplesCatalog: Catálogo de ejemplos básicos para ESP32 organizados por
     categorías.
   - IDEApp (Menu Manager + File Manager + Editor de prueba): Interfaz principal,
     menú Archivo completo, submenús secundarios, ventana de Preferencias,
     menú Avanzado, control de cambios sin guardar y atajos de teclado.

2. Correcciones aplicadas respecto al prototipo inicial:
   - Registro de atajos también sobre el widget Text (self.editor) retornando
     "break" directamente para evitar que Ctrl+O inserte saltos de línea.
   - Verificación de cambios sin guardar (edit_modified) antes de Nuevo, Abrir,
     Cerrar, cargar Ejemplos y Salir.
   - Lectura en UTF-8 con respaldo automático (fallback) a Latin-1 para sketches
     antiguos y mensajes de error detallados según la excepción.

Para ejecutar:
    ruta_archivo.py
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
            "01_Lectura_Boton": """// Ejemplo: Lectura de botón con resistencia pull-up interna
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
    - Carpeta de proyectos (Sketchbook)
    - Historial de proyectos recientes
    - Preferencias generales del IDE
    """

    MAX_RECENT_FILES = 10

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

    def ensure_sketchbook_exists(self) -> None:
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        try:
            os.makedirs(sketchbook_dir, exist_ok=True)
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

    def list_sketchbook_projects(self) -> list[tuple[str, str]]:
        """
        Devuelve una lista de tuplas (nombre_visible, ruta_archivo) con los
        proyectos dentro de la carpeta Sketchbook del usuario.
        """
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        projects: list[tuple[str, str]] = []
        if not os.path.isdir(sketchbook_dir):
            return projects

        try:
            for entry in sorted(os.listdir(sketchbook_dir)):
                full_path = os.path.join(sketchbook_dir, entry)
                if os.path.isfile(full_path) and entry.endswith((".ino", ".cpp", ".c", ".h")):
                    projects.append((entry, full_path))
                elif os.path.isdir(full_path):
                    # Busca archivo principal .ino dentro de la subcarpeta del sketch
                    for sub in sorted(os.listdir(full_path)):
                        if sub.endswith((".ino", ".cpp", ".c", ".h")):
                            projects.append((f"{entry}/{sub}", os.path.join(full_path, sub)))
        except Exception:
            pass
        return projects


class IDEApp:
    """
    Clase principal que integra la interfaz de prueba del editor, el menú Archivo
    completo, los submenús dinámicos, las preferencias y los atajos de teclado.
    """

    def __init__(self, root: tk.Tk, config_manager: ConfigManager | None = None):
        self.root = root
        self.config_manager = config_manager or ConfigManager()

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

        # Aplicar tema visual configurado e inicializar con el editor vacío
        self.apply_preferences_to_ui()
        self._load_content_into_editor("", filepath=None)

    # -------------------------------------------------------------------------
    # Traducción e interfaz
    # -------------------------------------------------------------------------
    def _t(self, key: str) -> str:
        lang = self.config_manager.settings.get("language", "es")
        lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["es"])
        return lang_dict.get(key, key)

    def _build_menus(self) -> None:
        """Construye la barra de menú siguiendo la estructura de Arduino IDE 2.3.10."""
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
            # Usuario presionó Cancelar
            return False
        if response is True:
            # Usuario presionó Sí: intentamos guardar
            return self._perform_save_and_confirm()
        # Usuario presionó No: descartar cambios
        return True

    def _perform_save_and_confirm(self) -> bool:
        if self.current_file:
            return self.write_to_file(self.current_file)
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
        """Limpia el editor y empieza un proyecto nuevo sin archivo asociado."""
        if not self.check_unsaved_changes():
            return "break"

        self._load_content_into_editor("", filepath=None)
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
        """Lee un archivo desde disco manejando codificaciones y errores detallados."""
        try:
            used_encoding = "utf-8"
            try:
                with open(filepath, "r", encoding="utf-8") as f_obj:
                    content = f_obj.read()
            except UnicodeDecodeError:
                # Respaldo automático a Latin-1 (Sección 13 de documentación técnica)
                used_encoding = "latin-1"
                with open(filepath, "r", encoding="latin-1") as f_obj:
                    content = f_obj.read()

            self._load_content_into_editor(
                content,
                filepath=filepath,
                encoding=used_encoding,
            )
            self.config_manager.add_recent_file(filepath)
            self.refresh_recent_menu()
            return True

        except FileNotFoundError:
            messagebox.showerror(
                "Archivo no encontrado",
                f"El archivo no existe en la ruta especificada:\n{filepath}",
            )
            self.config_manager.remove_recent_file(filepath)
            self.refresh_recent_menu()
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
        """Guarda el archivo actual o invoca Guardar como si aún no tiene ruta."""
        if self.current_file:
            self.write_to_file(self.current_file)
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
            return self.write_to_file(filepath)
        return False

    def write_to_file(self, target_path: str) -> bool:
        """Escribe el contenido del editor en disco y actualiza el estado."""
        try:
            if self.config_manager.settings.get("auto_backup_on_save") and os.path.exists(target_path):
                shutil.copy2(target_path, target_path + ".bak")

            text_content = self.editor.get("1.0", "end-1c")
            with open(target_path, "w", encoding="utf-8", newline="") as f_obj:
                f_obj.write(text_content)

            self.current_file = target_path
            self.current_encoding = "utf-8"
            self.editor.edit_modified(False)
            self.config_manager.add_recent_file(target_path)
            self.refresh_recent_menu()
            self.refresh_sketchbook_menu()
            self.update_title()
            return True

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
        Restablece el editor a un estado limpio sin archivo activo.
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
    # Menú Avanzado y Ventana de Preferencias (Sección 13)
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
        """Crea un archivo de respaldo (.bak) del sketch actual."""
        if not self.current_file:
            messagebox.showwarning(
                "Respaldo de Sketch",
                "Primero debes guardar el sketch en disco antes de generar un archivo de respaldo (.bak).",
            )
            return

        backup_path = f"{self.current_file}.bak"
        try:
            text_content = self.editor.get("1.0", "end-1c")
            with open(backup_path, "w", encoding="utf-8", newline="") as f:
                f.write(text_content)
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
        """Muestra información técnica y estadísticas del sketch actual."""
        content = self.editor.get("1.0", "end-1c")
        lines = content.count("\n") + 1 if content else 0
        chars = len(content)
        size_bytes = len(content.encode("utf-8"))
        filepath = self.current_file or "(Sin guardar en disco)"
        modified = "Sí" if self.editor.edit_modified() else "No"

        info_text = (
            f"Nombre: {os.path.basename(self.current_file) if self.current_file else self._t('new_title')}\n"
            f"Ruta: {filepath}\n"
            f"Codificación: {self.current_encoding.upper()}\n"
            f"Líneas de código: {lines}\n"
            f"Caracteres: {chars}\n"
            f"Tamaño en memoria (UTF-8): {size_bytes} bytes\n"
            f"Cambios sin guardar: {modified}\n"
            f"Carpeta Sketchbook: {self.config_manager.settings.get('sketchbook_path')}"
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
        - Idioma de la interfaz (Español / Inglés)
        - Tema visual (Claro / Oscuro)
        - Tamaño de fuente del editor
        - Respaldo automático (.bak) al guardar
        """
        pref_win = tk.Toplevel(self.root)
        pref_win.title("Preferencias — ESP32 IDE")
        pref_win.geometry("540x300")
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

        def browse_sketchbook() -> None:
            selected = filedialog.askdirectory(
                title="Seleccionar carpeta Sketchbook",
                initialdir=sketchbook_var.get() or os.getcwd(),
                parent=pref_win,
            )
            if selected:
                sketchbook_var.set(selected)

        ttk.Button(frame, text="Examinar…", command=browse_sketchbook).grid(row=0, column=2, pady=6)

        # 2. Idioma de la interfaz
        ttk.Label(frame, text="Idioma de la interfaz:").grid(row=1, column=0, sticky="w", pady=6)
        lang_map = {"Español (es)": "es", "English (en)": "en"}
        inv_lang_map = {v: k for k, v in lang_map.items()}
        lang_var = tk.StringVar(value=inv_lang_map.get(settings.get("language", "es"), "Español (es)"))
        lang_combo = ttk.Combobox(
            frame,
            textvariable=lang_var,
            values=list(lang_map.keys()),
            state="readonly",
        )
        lang_combo.grid(row=1, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=6)

        # 3. Tema visual
        ttk.Label(frame, text="Tema visual:").grid(row=2, column=0, sticky="w", pady=6)
        theme_map = {"Claro": "claro", "Oscuro": "oscuro"}
        inv_theme_map = {v: k for k, v in theme_map.items()}
        theme_var = tk.StringVar(value=inv_theme_map.get(settings.get("theme", "claro"), "Claro"))
        theme_combo = ttk.Combobox(
            frame,
            textvariable=theme_var,
            values=list(theme_map.keys()),
            state="readonly",
        )
        theme_combo.grid(row=2, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=6)

        # 4. Tamaño de fuente del editor
        ttk.Label(frame, text="Tamaño de fuente (Editor):").grid(row=3, column=0, sticky="w", pady=6)
        font_size_var = tk.IntVar(value=int(settings.get("font_size", 11)))
        font_spin = ttk.Spinbox(frame, from_=8, to=28, textvariable=font_size_var, width=8)
        font_spin.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=6)

        # 5. Opción avanzada: Crear respaldo automático (.bak) al guardar
        auto_bak_var = tk.BooleanVar(value=bool(settings.get("auto_backup_on_save", False)))
        ttk.Checkbutton(
            frame,
            text="Crear copia de respaldo (.bak) automáticamente al guardar",
            variable=auto_bak_var,
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=10)

        # Botones Guardar / Cancelar
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="e", pady=(16, 0))

        def save_preferences() -> None:
            try:
                f_size = max(8, min(28, int(font_size_var.get())))
            except ValueError:
                f_size = 11

            settings["sketchbook_path"] = sketchbook_var.get().strip() or self.config_manager.default_sketchbook
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
