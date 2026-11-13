# ESP32 IDE — Módulo "Archivo" (Completo)

Implementación completa del módulo **Archivo** para el proyecto **ESP32 IDE**, inspirada en el menú Archivo de **Arduino IDE 2.3.10**. Incluye tanto la aplicación de escritorio en **Python + `tkinter`** ([main.py](main.py)) como los módulos listos para la integración colaborativa con **FastAPI + Flutter** (`integracion_fastapi_flutter/`).

---

## 1. Estructura del proyecto

```text
proyecto de esp32_Archivo/
├── main.py                           # Aplicación completa (Menu Manager, File Manager, Config Manager)
├── config_archivo.json               # Archivo de configuración y preferencias (se genera automáticamente)
├── Sketchbook/                       # Carpeta por defecto para los proyectos del usuario
├── requirements.txt                  # Sin dependencias externas para el prototipo en tkinter
├── README.md                         # Documentación del proyecto
└── integracion_fastapi_flutter/      # Integración lista para la rama develop (FastAPI + Flutter)
    ├── backend/
    │   ├── main_api.py
    │   └── app/modules/archivo/
    │       ├── router.py             # Endpoints REST (/api/archivo/...)
    │       ├── schemas.py            # Contrato JSON (Request / Response)
    │       └── service.py            # Lógica de negocio conectada con ConfigManager
    └── frontend_flutter/
        └── lib/modules/archivo/
            ├── archivo_models.dart   # Modelos Dart y formateo para la UI de Log
            └── archivo_service.dart  # Cliente HTTP para Flutter
```

---

## 2. Alcance implementado en `main.py`

### Menú Archivo y Atajos de Teclado
Todos los atajos están registrados tanto en la ventana principal como directamente en el widget `tk.Text` (`self.editor`) devolviendo `"break"`, evitando que `Ctrl+O` inserte saltos de línea no deseados.

| Opción del Menú | Atajo | Descripción |
|---|---|---|
| **Nuevo Sketch** | `Ctrl+N` | Verifica cambios sin guardar, limpia el editor y empieza un proyecto nuevo (`current_file = None`). |
| **Abrir…** | `Ctrl+O` | Abre archivos `*.ino`, `*.cpp`, `*.c` y `*.h`. Lee en `UTF-8` con *fallback* automático a `Latin-1` para sketches antiguos. |
| **Abierto recientemente ►** | — | Submenú dinámico con los últimos 10 archivos abiertos guardados en `config_archivo.json` y opción para limpiar el historial. |
| **Sketchbook ►** | — | Submenú dinámico que escanea la carpeta `Sketchbook` del usuario y permite abrir cualquier proyecto con un clic. |
| **Ejemplos ►** | — | Submenú organizado en 4 categorías (`01. Básicos`, `02. Digital y PWM`, `03. Sensores y ADC`, `04. WiFi ESP32`). |
| **Cerrar** | `Ctrl+W` | Cierra el sketch actual verificando primero si hay cambios sin guardar (`Sí` / `No` / `Cancelar`). |
| **Guardar** | `Ctrl+S` | Sobrescribe el archivo actual (`self.current_file`) o invoca *Guardar como…* si es un sketch nuevo. |
| **Guardar como…** | `Ctrl+Mayús+S` | Permite elegir nombre y ubicación (agregando `.ino` por defecto) y actualiza el historial y el Sketchbook. |
| **Preferencias…** | `Ctrl+Coma` | Ventana modal para configurar: **Ubicación del Sketchbook**, **Idioma (`Español`/`English`)**, **Tema visual (`Claro`/`Oscuro`)**, **Tamaño de fuente** y **Respaldo automático (`.bak`)**. |
| **Avanzado ►** | — | Submenú con opciones avanzadas: *Mostrar carpeta del Sketch*, *Insertar plantilla base ESP32*, *Crear respaldo (.bak)*, *Recargar desde el disco*, *Información y estadísticas del Sketch* y *Restablecer preferencias*. |
| **Salir** | `Ctrl+Q` | Cierra la aplicación verificando primero si existen cambios sin guardar (también al pulsar la `X` de la ventana). |

---

## 3. Ejecución

### Ejecutar la aplicación de escritorio (`tkinter`)
```powershell
python main.py
```
