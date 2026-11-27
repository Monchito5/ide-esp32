# Sprint 3 — Detección de Placa Espressif y Compilación Nativa ESP-IDF

**Objetivo**: Implementar la detección automática de placas ESP32 (USB VID/PID Espressif + sondeo opcional `esptool`) y el flujo completo de compilación nativa con Espressif ESP-IDF (`Archivo` -> `Sketch` -> `Azul` -> `Flutter`), eliminando la dependencia de Arduino CLI.
**Rama**: `develop` | **Estrategia**: `single-pr` | **Runners**: `pytest` y `flutter test`
**Forecast**: ~550 authored changed lines

## Specs

- S1: Detección nativa de placa ESP32 sin depender de Arduino CLI: catálogo de perfiles compatibles ("ESP32-S3 DevKitC-1, ESP32-C3 u otro perfil compatible"), identificación por VID/PID USB oficial de Espressif (`0x303A`) y puentes UART (`0x10C4`, `0x1A86`, `0x0403`), más sondeo opcional con `esptool` (`chip_id`), expuesto en `GET /api/v1/herramientas/placas-soportadas`, `GET /api/v1/herramientas/detectar-placa` y `GET /api/v1/herramientas/puertos`.
- S2: Diagnóstico y localización multiplataforma del toolchain de Espressif (`ESP-IDF` / `idf.py` y `esptool`) soportando estructura EIM (`IDF_TOOLS_PATH`, `IDF_PYTHON_ENV_PATH`, `IDF_PYTHON_CHECK_CONSTRAINTS=no`) y buscando en `IDF_PATH`, `ESPRESSIF_PATH` y unidades locales (`C:/`, `E:/`), expuesto en `GET /api/v1/herramientas/esp-idf/estado` y `GET /api/v1/herramientas/esp-idf/version`.
- S3: Pipeline end-to-end de compilación nativa ESP-IDF ("integrando herramientas de compilación especifica de esp32, tales como Expressif y ESP-IDF con el motivo de no depender de Arduino CLI"): endpoint `POST /api/v1/sketch/compilar-codigo` que estructura el código fuente en un proyecto CMake ESP-IDF válido mediante `archivo_backend`, ejecuta `compilar_proyecto` con el `target` seleccionado (`esp32s3`, `esp32c3`, `esp32`, etc.), publica eventos en `azul_backend` y devuelve logs + binarios `.bin` con sus offsets de flash; conexión del adaptador de compilación de `azul_backend` en `ide_core`.
- S4: Integración en Flutter (`LayoutPrincipal` y `ApiHerramientas`): selector de placas reales de Espressif con su `target` ESP-IDF, autodetección real contra `/api/v1/herramientas/detectar-placa`, plantilla C nativa de ESP-IDF (`app_main`) y botón/menú "Verificar / Compilar" conectado a `/api/v1/sketch/compilar-codigo` mostrando logs y artefactos `.bin` reales en la consola.
- S5: Contratos JSON (`shared/contratos/herramientas/api_v1.json`, `shared/contratos/sketch/api_v1.json`) y suite de pruebas unitarias e integración en Python y Flutter en verde, sin crear ningún archivo `__init__.py`.

## Tasks

- T1 [S1, S2] inline — Detección nativa de placa Espressif y soporte EIM ESP-IDF v6.1.1 / esptool v5.7.0 en `herramientas_backend` — done (8/8 pytest green + validado en vivo con ESP-IDF v6.1.1)
- T2 [S3] inline — Pipeline end-to-end ESP-IDF (`sketch_backend` + `archivo_backend` + `azul_backend` + `ide_core`) — done (9/9 pytest green)
- T3 [S4, S5] inline — Integración frontend Flutter (`core/frontend` + `herramientas/frontend`), contratos JSON y pruebas — done (53/53 pytest green, 6/6 flutter test green, 0 analyze issues)

## Log

- L1: "La ejecución web/escritorio funciona correctamente, podemos avanzar con el Sprint 3. Recordar que estamos integrando herramientas de compilación especifica de esp32, tales como Expressif y ESP-IDF con el motivo de no depender de Arduino CLI."
- L2 (2026-11-26): Creado documento ODD de Sprint 3 y actualizado Plan Integral reemplazando la dependencia en Arduino CLI por Espressif (`ESP-IDF` + `esptool`).
- L3 (2026-11-26): "Actualmente ya está instalado ESP-IDF y Expressif, expresiff se encuentra en: E:\DATOS\PROGRAMAS\esp\.espressif y en el dispositivo local se encuentra instalación de esp-idf o incluso puedes buscar en ambos dispositivos C:/ y E:/. Basado en lo anterior puedes continuar, sube tus cambios a la rama remota."
- L4 (2026-11-26): Verificada instalación real de Espressif Installation Manager (EIM) con ESP-IDF v6.1.1 y esptool v5.7.0 (más QEMU Xtensa/RISC-V). Integrado soporte nativo de variables EIM (`IDF_TOOLS_PATH`, `IDF_PYTHON_ENV_PATH`, `IDF_PYTHON_CHECK_CONSTRAINTS=no`). Validado en vivo y empaquetado en work-unit commits hacia `origin/develop`.
