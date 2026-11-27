# ESP32 IDE — Módulo "Archivo"

Implementación local completa del módulo **Archivo** para el proyecto **ESP32 IDE**, inspirada en el menú Archivo de **Arduino IDE 2.3.10** y lista para conectarse con el módulo **Sketch / Compilación** y **Flasheo**. Incluye tanto la aplicación de escritorio en **Python + `tkinter`** ([main.py](main.py), sin dependencias externas ni funciones en la nube) como la capa de integración **FastAPI + Flutter** (`integracion_fastapi_flutter/` y `backend/archivo_backend/`).

---

## 1. Arquitectura del Módulo

El núcleo compartido vive sin dependencias externas en `main.py` (y replicado de forma headless en `backend/archivo_backend/config.py`):

- **`ConfigManager`**:
  - Gestiona rutas multiplataforma, `config_archivo.json`, la carpeta **`Sketchbook/`** y la subcarpeta **`Sketchbook/libraries/`**.
  - Mantiene el historial LIFO de archivos recientes (máximo 10).
  - Excluye carpetas ocultas (`.git`, `.vscode`, `.idea`, etc.) y directorios reservados (`RESERVED_DIRS`: `libraries`, `build`, `.git`, `__pycache__`, `.vscode`, `.idea`) al escanear proyectos, priorizando `<carpeta>.ino` en subcarpetas de 1 nivel.
- **`FileManager`**:
  - Gestor *headless* reutilizable por `IDEApp` (`tkinter`) y por `ArchivoService` (FastAPI).
  - Valida extensiones permitidas (`SUPPORTED_EXTENSIONS = (".ino", ".cpp", ".c", ".h")`).
  - Lee archivos en **UTF-8** con *fallback* automático a **Latin-1** y soporta abrir carpetas de proyecto directamente.
  - Al guardar un `.ino` nuevo con `create_project_folder=True`, organiza automáticamente en `Sketchbook/<Proyecto>/<Proyecto>.ino` sin mover archivos `.ino` ya existentes.
  - Crea archivos secundarios dentro del proyecto validando que no exista *path traversal*, genera respaldos `.bak` y expone `get_project_info()` y `get_sketch_stats()` para el compilador.
- **`ExamplesCatalog`**:
  - Catálogo de ejemplos ESP32 en 4 categorías (`01. Básicos`, `02. Digital y PWM`, `03. Sensores y ADC`, `04. WiFi ESP32`).
- **`IDEApp`**:
  - Interfaz de escritorio en `tkinter` con menú Archivo completo, control de cambios sin guardar, ventana de Preferencias (incluyendo `Sketchbook` y `Carpeta de bibliotecas`), menú Avanzado y atajos de teclado vinculados en ventana y editor.

---

## 2. Estructura de Carpetas y Proyectos

```text
modules/archivo/
├── main.py                                   # Núcleo compartido (ConfigManager, FileManager, ExamplesCatalog) + GUI tkinter
├── config_archivo.json                       # Preferencias locales (incluye sketchbook_path y libraries_path)
├── README.md                                 # Documentación del módulo
├── Sketchbook/
│   ├── libraries/                            # Bibliotecas locales del usuario (excluida del listado de proyectos)
│   └── <Proyecto>/
│       ├── <Proyecto>.ino                    # Archivo principal del sketch
│       └── <secundario>.h / .cpp / .c        # Archivos adicionales del proyecto
├── tests/
│   └── test_archivo.py                       # Suite unitaria e integración (unittest)
├── backend/archivo_backend/                  # Adaptador registrado en el backend del monorepo (/api/v1/archivo)
├── frontend/                                 # Cliente y vista Flutter del monorepo
└── integracion_fastapi_flutter/
    ├── backend/
    │   ├── main_api.py
    │   └── app/modules/archivo/
    │       ├── router.py                     # Endpoints REST (/api/archivo/...)
    │       ├── schemas.py                    # Contrato JSON (Request / Response)
    │       └── service.py                    # Lógica de negocio conectada con ConfigManager y FileManager
    └── frontend_flutter/
        └── lib/modules/archivo/
            ├── archivo_models.dart           # Modelos Dart (ProjectInfo, IDEPreferences, ArchivoActionResponse, etc.)
            └── archivo_service.dart          # Cliente HTTP Dart (ArchivoApiService)
```

---

## 3. Endpoints REST (Integración Sketch / Compilación / Flutter)

> Nota: en el servidor independiente (`integracion_fastapi_flutter/backend/main_api.py`) el prefijo es `/api/archivo`, mientras que en el backend unificado del monorepo (`backend/archivo_backend/router.py`) el prefijo es `/api/v1/archivo`.

### Gestión Local de Archivos, Proyectos y Preferencias

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/archivo/nuevo` | Inicializa un sketch nuevo con `DEFAULT_SKETCH_TEMPLATE` y devuelve `ProjectInfo`. |
| `POST` | `/api/archivo/abrir` | Abre un archivo soportado o una carpeta de proyecto (UTF-8 con fallback Latin-1). |
| `POST` | `/api/archivo/guardar` | Guarda el contenido en disco (`create_project_folder` opcional) y genera `.bak` si aplica. |
| `POST` | `/api/archivo/cerrar` | Cierra el sketch activo y limpia el estado actual en memoria. |
| `GET` | `/api/archivo/actual` | Devuelve la información (`ProjectInfo`) y archivos del proyecto activo. |
| `GET` | `/api/archivo/proyecto/archivos` | Lista los archivos del proyecto activo o de la ruta `project_path` indicada por query. |
| `POST` | `/api/archivo/proyecto/archivo` | Crea un archivo secundario (`.h`, `.cpp`, `.c`, `.ino`) dentro del proyecto validando *path traversal*. |
| `GET` | `/api/archivo/submenus` | Devuelve recientes, proyectos detallados del `Sketchbook`, categorías de ejemplos, `sketchbook_path` y `libraries_path`. |
| `DELETE` | `/api/archivo/recientes` | Limpia el historial de archivos recientes. |
| `GET` | `/api/archivo/preferencias` | Obtiene la configuración actual (`config_archivo.json`). |
| `PUT` | `/api/archivo/preferencias` | Actualiza preferencias (deriva `libraries_path` si llega vacío o nulo). |
| `POST` | `/api/archivo/preferencias/restablecer` | Restablece las preferencias por defecto y asegura `Sketchbook/` y `libraries/`. |
| `POST` | `/api/archivo/avanzado/respaldo` | Genera manualmente una copia de respaldo `.bak`. |
| `POST` | `/api/archivo/avanzado/info` | Devuelve estadísticas del sketch (`lines`, `chars`, `size_bytes`, `encoding`) y `project_info`. |

### Puente ESP-IDF para Compilación (`Sketch`) y Flasheo

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/archivo/espidf/preparar` | Recibe archivos vía `UploadFile` y crea el workspace ESP-IDF (`CMakeLists.txt` + `main/`). |
| `GET` | `/api/archivo/espidf/{project_id}/ruta-compilador` | Entrega la ruta absoluta del proyecto temporal al módulo Sketch / Compilación. |
| `POST` | `/api/archivo/espidf/entregar-resultados` | Recolecta binarios `.bin` (con *offsets* ESP32 y Base64 opcional) y logs para Flutter/Log. |
| `GET` | `/api/archivo/espidf/{project_id}/descargar-bin` | Descarga directa de un binario `.bin` mediante `rel_path`. |
| `DELETE` | `/api/archivo/espidf/{project_id}` | Limpia el workspace temporal de ESP-IDF al finalizar. |

---

## 4. Ejecución y Pruebas

### Ejecutar la aplicación de escritorio (`tkinter`)
```powershell
cd modules\archivo
python main.py
```

### Ejecutar el servidor FastAPI independiente (opcional)
```powershell
cd modules\archivo
uvicorn integracion_fastapi_flutter.backend.main_api:app --reload --port 8000
```

### Ejecutar la suite de pruebas (`unittest`)
Desde la carpeta del módulo o desde la raíz del monorepo:
```powershell
python -m unittest discover -s tests -v
```
