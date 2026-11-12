# AGENTS.md - IDE ESP32 Monorepo

This file provides compact, high-signal guidance for OpenCode agents working in this repository. Every line has been verified against the codebase.

## Quickstart

### 1. Environment
```bash
cd ide-esp32
python -m venv venv
# Windows
venv\Scripts\Activate.ps1
# Linux/macOS
source venv/bin/activate
pip install -r requirements-dev.txt
pip install -e core/backend
pip install -e modules/herramientas/backend
```

### 2. Start the backend
```bash
cd core/backend
python -m ide_core.main   # runs on http://127.0.0.1:8765
```

### 3. Start the IDE (Flutter)
```bash
cd apps/ide
flutter pub get
flutter run -d chrome     # web
# or: flutter run -d windows/macos/linux  # desktop
```

## Architecture

- **Monorepo**: Python (FastAPI) backend + Flutter/Dart frontend
- `core/backend/ide_core/` — base API gateway + module registry
- `modules/herramientas/` — plug-in module (backend + frontend)
- `apps/ide/` — Flutter shell UI (the single entry point)
- `shared/contratos/` — FE/BE JSON contracts
- `sql/` — versioned SQL schemas (applied in lexicographic order)

## Critical Conventions (PEP 420 / namespace packages)

- **NO `__init__.py` files** allowed (enforced by CI; see `.github/workflows/ci-python.yml:41-43`)
- **Absolute imports only**, using the single package name:
  - `from ide_core.config.constants import X`
  - `from herramientas_backend.controllers.x import y`
- Dependencies are **centralized in root** `requirements*.txt` — do NOT create `requirements.txt` inside `core/` or `modules/`

## Module Management

Each module must expose:
- **Backend**: `modules/<nombre>/backend/modulo.py` with `def registrar(app: FastAPI) -> None`
- **Frontend**: `modules/<nombre>/frontend/lib/modulo_<nombre>.dart` implementing `ModuloIde`

After adding a new module:
1. Add to `MODULOS_REGISTRADOS` list in `core/backend/ide_core/config/constants.py`
2. Register frontend in `apps/ide/lib/nucleo/registro_modulos.dart`
3. Add contract JSON in `shared/contratos/<nuevo>/`
4. Add SQL schema in `sql/02_schema_<nuevo>.sql`
5. If new deps, add to root `requirements.txt`

## Running Tests

```bash
# Core backend tests
cd core/backend
pytest pruebas/ -v

# Herramientas module tests
cd modules/herramientas/backend
pytest pruebas/ -v
```

CI runs: `black --check`, `isort --check-only`, then pytest for both packages.

## Key Entry Points

| Component | Command |
|-----------|---------|
| **Backend (FastAPI)** | `cd core/backend && python -m ide_core.main` |
| **IDE Flutter** | `cd apps/ide && flutter run -d chrome` |

## Environment

- `.env.ejemplo` has config vars: `DEBUG`, `LOG_LEVEL`, `API_HOST`, `API_PORT` (8765), `ARDUINO_CLI_PATH`, `PUERTO_DEFECTO`, `VELOCIDAD_DEFECTO`, `TIMEOUT_PUERTO`
- API base: `http://127.0.0.1:8765/api/v1/herramientas` (moduloHerramientas routes)
- SQLite DB at `ide.db` (root datos/ folder); schemas auto-applied on startup from `sql/` in lexicographic order