# Archivo: modules/archivo/backend/archivo_backend/config.py
"""
Configuracion y preferencias del modulo Archivo.

Extraído del prototipo tkinter (ruta_archivo.py) para uso independiente
del backend FastAPI, sin dependencia cruzada con la aplicacion de escritorio.
"""

import json
import os
from typing import Dict, List, Optional

DEFAULT_SKETCH_TEMPLATE = """// Sketch para ESP32
// Configura aqui tus pines y constantes

void setup() {
  // Inicializacion: se ejecuta una sola vez al encender o reiniciar la placa
  Serial.begin(115200);
}

void loop() {
  // Codigo principal: se ejecuta repetidamente

}
"""

FILE_TYPES = [
    ("Archivos Arduino/C++", "*.ino *.cpp *.c *.h"),
    ("Sketch de Arduino (*.ino)", "*.ino"),
    ("Codigo C/C++ (*.cpp;*.c;*.h)", "*.cpp *.c *.h"),
]

TRANSLATIONS = {
    "es": {
        "menu_file": "Archivo",
        "new_sketch": "Nuevo Sketch",
        "open": "Abrir...",
        "recent": "Abierto recientemente",
        "sketchbook": "Sketchbook",
        "examples": "Ejemplos",
        "close": "Cerrar",
        "save": "Guardar",
        "save_as": "Guardar como...",
        "preferences": "Preferencias...",
        "advanced": "Avanzado",
        "exit": "Salir",
        "no_recent": "(Sin archivos recientes)",
        "clear_recent": "Borrar historial de recientes",
        "empty_sketchbook": "(Carpeta Sketchbook vacia)",
        "open_sketchbook_dir": "Abrir carpeta Sketchbook...",
        "refresh_sketchbook": "Actualizar lista de Sketchbook",
        "adv_show_folder": "Mostrar carpeta del Sketch",
        "adv_insert_template": "Insertar plantilla base ESP32",
        "adv_backup": "Crear respaldo del Sketch (.bak)",
        "adv_info": "Informacion y estadisticas del Sketch...",
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
        "open": "Open...",
        "recent": "Open Recent",
        "sketchbook": "Sketchbook",
        "examples": "Examples",
        "close": "Close",
        "save": "Save",
        "save_as": "Save As...",
        "preferences": "Preferences...",
        "advanced": "Advanced",
        "exit": "Quit",
        "no_recent": "(No recent files)",
        "clear_recent": "Clear recent history",
        "empty_sketchbook": "(Empty Sketchbook folder)",
        "open_sketchbook_dir": "Open Sketchbook folder...",
        "refresh_sketchbook": "Refresh Sketchbook list",
        "adv_show_folder": "Show Sketch Folder",
        "adv_insert_template": "Insert ESP32 Base Template",
        "adv_backup": "Create Sketch Backup (.bak)",
        "adv_info": "Sketch Information & Statistics...",
        "adv_reload": "Reload File from Disk",
        "adv_reset_prefs": "Reset Default Preferences",
        "new_title": "New Sketch",
        "status_ready": "Ready",
        "status_modified": "Modified (unsaved)",
        "status_saved": "Saved",
    },
}


class ExamplesCatalog:
    """Catalogo de ejemplos integrados organizados por categoria para ESP32."""

    CATEGORIES: Dict[str, Dict[str, str]] = {
        "01. Basicos": {
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
            "03_Monitor_Serial": """// Ejemplo: Comunicacion por puerto serie en ESP32
int contador = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("=== ESP32 Inicializado ===");
}

void loop() {
  Serial.print("Ciclo de ejecucion #");
  Serial.println(contador++);
  delay(2000);
}
""",
        },
        "02. Digital y PWM": {
            "01_Lectura_Boton": """// Ejemplo: Lectura de boton con resistencia pull-up interna
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
            "01_Lectura_ADC_12Bits": """// Ejemplo: Lectura analogica (ADC de 12 bits: 0 a 4095 en ESP32)
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
    Gestiona la configuracion del sistema de archivos del modulo Archivo:
    - Rutas multiplataforma
    - Carpeta de proyectos (Sketchbook)
    - Historial de proyectos recientes
    - Preferencias generales del IDE
    """

    MAX_RECENT_FILES = 10

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

    def ensure_sketchbook_exists(self) -> None:
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        try:
            os.makedirs(sketchbook_dir, exist_ok=True)
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

    def list_sketchbook_projects(self) -> List[tuple]:
        """
        Devuelve una lista de tuplas (nombre_visible, ruta_archivo) con los
        proyectos dentro de la carpeta Sketchbook del usuario.
        """
        sketchbook_dir = self.settings.get("sketchbook_path") or self.default_sketchbook
        projects: List[tuple] = []
        if not os.path.isdir(sketchbook_dir):
            return projects

        try:
            for entry in sorted(os.listdir(sketchbook_dir)):
                full_path = os.path.join(sketchbook_dir, entry)
                if os.path.isfile(full_path) and entry.endswith((".ino", ".cpp", ".c", ".h")):
                    projects.append((entry, full_path))
                elif os.path.isdir(full_path):
                    for sub in sorted(os.listdir(full_path)):
                        if sub.endswith((".ino", ".cpp", ".c", ".h")):
                            projects.append((f"{entry}/{sub}", os.path.join(full_path, sub)))
        except Exception:
            pass
        return projects
