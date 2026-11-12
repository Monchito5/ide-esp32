# IDE ESP32 (Monorepo)

**Version**: 6.0 | **Fecha**: 24 sep. 2026

Monorepo del IDE a la medida para ESP32-S3. El **IDE es el producto**; `herramientas` es un módulo plug-in que este equipo aporta.

## Arquitectura Resumen

| Capa | Ubicación | Responsable |
|------|-----------|-------------|
| Shell IDE (UI) | `apps/ide` | GRIS (base) |
| Core backend (API gateway) | `core/backend` | GRIS (base) |
| Modulos plug-in | `modules/<nombre>` | Cada equipo |
| Contratos compartidos | `shared/contratos` | Todos |
| Esquema SQL | `sql` | Todos |

## Puntos de Entrada

| Componente | Comando |
|------------|---------|
| **IDE (Flutter)** | `cd apps/ide && flutter run -d chrome` |
| **Backend (FastAPI)** | `cd core/backend && python -m ide_core.main` |

No hay más entry points. Los módulos se registran dentro de estos dos.

## Instalación Rápida

1. Entorno virtual (raíz):
   ```bash
   cd ide-esp32
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   pip install -e core/backend
   pip install -e modules/herramientas/backend
   ```

2. Arrancar:
   - Terminal 1: `cd core/backend && python -m ide_core.main`
   - Terminal 2: `cd apps/ide && flutter pub get && flutter run -d chrome`

3. Modplataforma (primera vez):
   ```bash
   flutter config --enable-windows-desktop
   flutter config --enable-macos-desktop
   flutter config --enable-linux-desktop
   ```

## Reglas Críticas

Para todas las convenciones de código (sin `__init__.py`, imports absolutos `ide_core.x`, `herramientas_backend.x`, dependencias en `requirements.txt` raíz, black/isort/formato) consultar `docs/desarrollo/CONVENCIONES_CODIGO.md`.

## Cómo Agregar un Nuevo Módulo

1. Crear `modules/<nuevo>/backend/` con `modulo.py` (`def registrar(app: FastAPI) -> None`).
2. Crear `modules/<nuevo>/frontend/lib/modulo_<nuevo>.dart` implementando `ModuloIde`.
3. Agregar a `MODULOS_REGISTRADOS` en `core/backend/ide_core/config/constants.py`.
4. Registrar frontend en `apps/ide/lib/nucleo/registro_modulos.dart`.
5. Agregar contrato JSON en `shared/contratos/<nuevo>/`.
6. Agregar esquema SQL en `sql/02_schema_<nuevo>.sql`.
7. Si trae dependencias nuevas, agregarlas a `requirements.txt` (raíz).

## Núcleo de Herramientas

### Nuevas Capabilidades Incluidas:
- Integración de **Arduino CLI** para detección de placas y puertos
- Integración de **PlatformIO** para gestión de toolchains, bibliotecas y proyectos
- Integración de **ESP-IDF** para configuración SDK y menuconfig
- Controladores de dominio, aplicación e infraestructura seguros bajo Arquitectura Limpia
- 12 endpoints API bajo `/api/v1/herramientas` para todo el espectro de funcionalidades

### Estructura Renovada (Arquitectura Limpia):

```
modules/herramientas/backend/herramientas_backend/
├── models.py           # Capa de Dominio: Entidades puras (PuertoSerie, Herramienta, Puerto, ConfiguracionESP32)
├── controllers/        # Capa de Adaptadores: FastAPI controllers (arduino.py, puerto.py)
├── routes.py           # 12 endpoints API organizados por funcionalidad
├── modulo.py           # Punto de entrada: registrar(app)
├── application/        # Casos de uso (use_cases.py)
├── infrastructure/     # Implementaciones concretas (Arduino, PlatformIO, ESP-IDF)
│   ├── arduino/
│   │   └── cli_service.py
│   ├── platformio/
│   │   └── manager.py
│   └── esp_idf/
│       └── configurator.py
└── shared/             # Utilidades y constantes
```

### Endpoints API Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/puertos` | GET | Listar puertos serie disponibles |
| `/arduino/version` | GET | Obtener versión de Arduino CLI |
| `/arduino/placas` | GET | Listar placas detectadas |
| `/reportes/flash` | GET | Resumen de flasheo realizado |
| `/esp-idf/version` | GET | Versión de ESP-IDF instalada |
| `/esp-idf/sdkconfig` | GET | Configuración actual del SDK |
| `/esp-idf/menuconfig` | GET | Menú de configuración interactivo |
| `/platformio/estado` | GET | Estado de PlatformIO instalado |
| `/platformio/iniciar` | POST | Inicializar proyecto PlatformIO |
| `/platformio/compilar` | POST | Compilar proyecto PlatformIO |
| `/platformio/flashear` | POST | Flashear firmware al puerto especificado |
| `/platformio/puertos-disponibles` | GET | Puertos serie disponibles via PlatformIO |

---

**Ultima actualizacion**: 24 sep. 2026