-- Archivo: sql/07_schema_archivo.sql
-- Esquema para persistencia del modulo Archivo (recientes y preferencias).

CREATE TABLE IF NOT EXISTS archivo_recientes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_sketch       TEXT NOT NULL,
    ruta_absoluta       TEXT NOT NULL UNIQUE,
    es_directorio       INTEGER NOT NULL DEFAULT 0,
    ultimo_acceso       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS archivo_preferencias (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    clave               TEXT NOT NULL UNIQUE,
    valor               TEXT NOT NULL,
    tipo_dato           TEXT NOT NULL DEFAULT 'string',
    fecha_modificacion  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_archivo_recientes_acceso ON archivo_recientes(ultimo_acceso DESC);
