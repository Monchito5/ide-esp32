# Arquitectura del Monorepo IDE ESP32

El producto es el **IDE**. Cada capacidad funcional es un **modulo plug-in**.

## Capas

1. **apps/ide** — Shell Flutter. Layout, navegación y punto de entrada UI.
   - Registra instancias de módulos en `nucleo/registro_modulos.dart`.
   - Docs: `apps/ide/lib/nucleo/registro_modulos.dart`.

2. **core/backend** — FastAPI. API gateway que agrega las rutas de todos los módulos.
   - Registra módulos en `config/registro_modulos.py` mediante `MODULOS_REGISTRADOS`.
   - Punto de entrada: `core/backend/python -m ide_core.main`.
   - Docs: `core/backend/ide_core/main.py`, `core/backend/ide_core/config/setup.py`.

3. **core/frontend** — Librería Dart `ide_core`. Define el contrato `ModuloIde`,
   el `LayoutPrincipal` y los temas.
   - Docs: `core/frontend/lib/ide_core.dart`, `core/frontend/lib/nucleo/modulo_ide.dart`.

4. **modules/<nombre>** — Módulo plug-in.
   - **Backend**: paquete Python con `modulo.py` (`def registrar(app: FastAPI) -> None`).
   - **Frontend**: paquete Dart con una clase que implementa `ModuloIde` (nombre: `Modulo<Nombre>`).
   - Docs: `modules/<nombre>/backend/modulo.py`, `modules/<nombre>/frontend/lib/modulo_<nombre>.dart`.

5. **shared/contratos** — Contratos JSON entre frontend y backend.
   - Core: `shared/contratos/core/api_v1.json` (prefijo `/api/v1`).
   - Módulo: `shared/contratos/<modulo>/api_v1.json` (prefijo `/api/v1/<modulo>`).

6. **sql/** — Esquema por módulo, aplicado en orden léxico sobre SQLite.
   - Docs: `sql/01_schema_core.sql`, `sql/02_schema_herramientas.sql`, etc.

## Flujo de Arranque

### Backend (UNICO punto de entrada)

```
cd core/backend
python -m ide_core.main
  -> AppConfig.establecer_conexion()   # crea BD + aplica SQL desde sql/
  -> AppConfig.iniciar_app()           # arranca uvicorn
       -> crear_app()
            -> configurar_rutas_base()          # /api/v1/salud, /api/v1/modulos
            -> registrar_modulos(app)           # carga MODULOS_REGISTRADOS
                 -> import herramientas_backend.modulo
                 -> herramientas_backend.modulo.registrar(app)
                      -> app.include_router(router)  # /api/v1/herramientas/*
```

### Frontend (UNICO punto de entrada)

```
cd apps/ide
flutter run -d chrome    # o windows / macos / linux
  -> main()                        # apps/ide/lib/main.dart
  -> construirModulos()            # nucleo/registro_modulos.dart
  -> RegistroModulos([...])        # instancias de ModuloIde
  -> IdeApp -> LayoutPrincipal
```

## Dependencias

TODAS las dependencias del monorepo viven en la RAÍZ:

- `requirements.txt` — producción (core + modulos).
- `requirements-dev.txt` — desarrollo y pruebas.

Un unico `venv/` en la raiz sirve a todo el monorepo.

## Referencia a Convenciones

Para convenciones de código (black, isort, pylint, sin `__init__.py`, imports absolutamente centralizados, dependencias en root `requirements.txt`), ver `docs/desarrollo/CONVENCIONES_CODIGO.md`.