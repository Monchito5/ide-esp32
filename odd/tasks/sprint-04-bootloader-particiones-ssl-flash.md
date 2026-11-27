# Sprint 4 — Bootloader, Particiones, Certificados SSL (NVS) y Flasheo Completo

**Objetivo**: Implementar la grabación de bootloader, generación/edición de tablas de particiones, empaquetado de certificados SSL en NVS, flasheo completo orquestado (físico con `esptool v5.7.0` y con bootloader emulado + verificación SHA-256/`verify-flash`) e historial persistente en SQLite.
**Rama**: `develop` | **Estrategia**: `single-pr` (preguntar antes de commit/push según AGENTS.md) | **Runners**: `pytest` y `flutter test`
**Forecast**: ~750 authored changed lines

## Specs

- S1: Grabación de Bootloader (`POST /api/v1/herramientas/esptool/bootloader`): soporta `esptool` físico (`write-flash` en `0x0` para S3/C3/C6 y `0x1000` para ESP32/S2) y bootloader emulado ("5. Realizar pruebas de flasheo — Utilizar el bootloader emulado y esptool para verificar las operaciones de Flash"), validando cabecera mágica `0xE9` e `image-info`.
- S2: Gestión de Tablas de Particiones (`GET /api/v1/herramientas/particiones/plantillas`, `POST /api/v1/herramientas/particiones/generar`, `POST /api/v1/herramientas/particiones/parsear`): plantillas oficiales Espressif (`single_app`, `single_app_ssl_nvs`, `factory_ota`), conversión CSV <-> `.bin` usando `gen_esp32part.py` de ESP-IDF (con generador binario `0xAA50` compatible como respaldo) y detección de solapamientos.
- S3: Certificados SSL en NVS (`POST /api/v1/herramientas/certificados/generar-nvs`): validación de PEM X.509 (`ca_cert`, `client_cert`, `client_key`) y generación de imagen binaria NVS (`0x9000`) mediante `nvs_partition_gen.py` de ESP-IDF (con respaldo determinista para entornos CI).
- S4: Flasheo Completo Orquestado + Verificación + Historial SQL (`POST /api/v1/herramientas/esptool/flash-completo`, `POST /api/v1/herramientas/esptool/verificar-flash`, `GET /api/v1/herramientas/historial-flash`): secuencia completa (`bootloader` + `partition-table` + `nvs_ssl` + `app`), verificación `verify-flash` / readback SHA-256 y persistencia en SQLite (`sql/09_schema_sprint4_flash.sql`).
- S5: Interfaz Flutter (`LayoutPrincipal`, `dialogos_flash_sprint4.dart` y `ApiHerramientas`) con paneles interactivos para Grabar Bootloader, Tabla de Particiones, Certificados SSL (NVS) y Wizard de Flasheo Completo + pruebas unitarias e integración en Python y Flutter.

## Tasks

- T1 [S1, S2, S3] inline — Backend de tablas de particiones (`particiones.py`), certificados SSL NVS (`certificados.py`) y grabación de bootloader — done (13/13 herramientas pytest green)
- T2 [S4] inline — Orquestación de flasheo completo (`esptool_service.py`), verificación SHA-256/`verify-flash` y persistencia SQL (`09_schema_sprint4_flash.sql`) — done (58/58 backend pytest green)
- T3 [S5] inline — UI Flutter (`dialogos_flash_sprint4.dart` + `layout_principal.dart` + `api_herramientas.dart`), contratos JSON y pruebas de widgets — done (pendiente confirmación de commit/push)

## Log

- L1: "5. Realizar pruebas de flasheo — Utilizar el bootloader emulado y esptool para verificar las operaciones de Flash. [...] Adjunto lo que falta hasta el sprint 6: [...] Grabar Bootloader, Certificados SSL y Particiones, Flasheo completo"
- L2 (2026-11-26): Usuario autoriza inicio del Sprint 4 ("si"). Verificados en `E:\DATOS\PROGRAMAS\esp\.espressif\v6.1.1`: `esptool v5.7.0`, `gen_esp32part.py` y `nvs_partition_gen.py`.
- L3 (2026-11-26): Completados T1, T2 y T3. Corregido `08_schema_azul.sql` a sintaxis SQLite estándar (`INTEGER PRIMARY KEY AUTOINCREMENT`) para que los 11 esquemas SQL apliquen sin fricción. Corregido overflow horizontal en `DropdownButtonFormField` con `isExpanded: true`.
