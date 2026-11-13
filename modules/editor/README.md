# Modulo Editor (Equipo Rojo)

**Equipo responsable**: Equipo Rojo (Víctor Gael Solorzano Sánchez, Cesar Josué Soto Langarica, Claudio Nathaniel Suárez del Real Ramírez)  
**Referencia**: Arduino IDE 2.3.10 — Proyecto ESP32 IDE  
**Version**: 1.0.0  

Modulo plug-in del IDE ESP32 que implementa la experiencia de edicion de codigo fuente C/C++/Arduino con soporte completo para las funciones del menú **Edit**, atajos de teclado, resaltado de sintaxis y busqueda/reemplazo.

---

## Estructura

```
modules/editor/
├── backend/                  # Paquete Python: editor_backend (PEP 420)
│   ├── editor_backend/
│   │   ├── modulo.py         # API pública: registrar(app)
│   │   ├── routes.py         # Endpoints FastAPI (/api/v1/editor/*)
│   │   ├── models.py         # Entidades de dominio
│   │   └── controllers/      # Format, Search y Config controllers
│   ├── pruebas/unitarias/    # Tests de backend
│   └── pyproject.toml
├── frontend/                 # Paquete Dart/Flutter: editor_ui
│   ├── lib/
│   │   ├── editor_ui.dart    # Export público del paquete
│   │   ├── modulo_editor.dart # Implementa ModuloIde
│   │   ├── nucleo/           # EditManager, SearchManager, SyntaxHighlighter, EditorState, ShortcutManager
│   │   ├── servicios/        # ApiEditor (HTTP client)
│   │   └── ui/               # VistaEditor, MenuEditWidget, FindReplaceBar, diálogos
│   ├── test/                 # Tests unitarios Flutter
│   └── pubspec.yaml
└── README.md
```

---

## Distribución de Responsabilidades (Equipo Rojo)

| Integrante | Rol | Responsabilidades Principales |
|---|---|---|
| **Víctor** | **Dev A** | Núcleo del editor, Sistema Undo/Redo (`EditManager`), Comment / Uncomment, integración del menú Edit y documentación técnica. |
| **César** | **Dev B** | Resaltado de sintaxis C/C++ (`CppSyntaxHighlighterController`), Cut/Copy/Paste, Copy for Forum (Markdown), motor de búsqueda (Find, Next, Previous). |
| **Nathaniel** | **Dev C** | Configuración de atajos de teclado (`EditorShortcutWrapper`), Select All, Go to Line (`DialogoIrALinea`), Indentación, Diálogos de búsqueda/reemplazo, ajuste de tamaño de fuente y pruebas unitarias. |

---

## Requerimientos y Casos de Prueba Cubiertos

* **REQ-001 / REQ-002**: Undo y Redo con historial de cambios (`canUndo`, `canRedo`).
* **REQ-003 / REQ-005 / REQ-006**: Cut, Copy y Paste mediante portapapeles del sistema (`Clipboard`).
* **REQ-004 / REQ-014 / REQ-015 / REQ-016**: Búsqueda interactiva, Find Next, Find Previous (con navegación circular) y Use Selection for Find.
* **REQ-007**: Select All.
* **REQ-008 / REQ-022**: Go to Line con validación de rangos 1..N.
* **REQ-009**: Copy for Forum (generación automática de bloque Markdown ` ```cpp `).
* **REQ-010**: Comment / Uncomment (toggle dinámico de `//`).
* **REQ-011 / REQ-012**: Aumentar y disminuir sangría (2 espacios estándar).
* **REQ-013**: Auto Format para C/C++ (indentación por bloques y llaves `{ }`).
* **REQ-017**: Replace in Files sobre archivos del proyecto (`.ino`, `.cpp`, `.h`).
* **REQ-018 / REQ-019**: Ajuste visual de tamaño de fuente con límites (8pt - 36pt).
* **REQ-020 / REQ-021**: Atajos de teclado coherentes y unificados con el menú Edit.

---

## Registro en el Monorepo

* **Backend**: Registrado en `core/backend/ide_core/config/constants.py` en `MODULOS_REGISTRADOS`.
* **Frontend**: Registrado en `apps/ide/lib/nucleo/registro_modulos.dart` en `construirModulos()`.
* **Esquema SQL**: `sql/02_schema_editor.sql`.
* **Contrato API**: `shared/contratos/editor/api_v1.json`.
