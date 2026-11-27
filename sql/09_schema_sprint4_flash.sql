-- Archivo: sql/09_schema_sprint4_flash.sql
-- Esquema extendido del Sprint 4 para historial detallado de flasheo, particiones y certificados SSL NVS.

CREATE TABLE IF NOT EXISTS herramientas_operaciones_flash (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    puerto          TEXT    NOT NULL,
    chip_target     TEXT    NOT NULL DEFAULT 'esp32s3',
    modo            TEXT    NOT NULL DEFAULT 'emulado',
    tipo_operacion  TEXT    NOT NULL,
    offsets_json    TEXT    NOT NULL DEFAULT '{}',
    sha256_resumen  TEXT,
    verificado      INTEGER NOT NULL DEFAULT 0,
    exitoso         INTEGER NOT NULL DEFAULT 0,
    salida          TEXT,
    fecha           TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_operaciones_flash_fecha
    ON herramientas_operaciones_flash (fecha DESC);
