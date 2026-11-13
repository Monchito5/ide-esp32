-- Archivo: sql/02_schema_editor.sql
-- Esquema del modulo Editor (Equipo Rojo - Arduino IDE 2.3.10).

CREATE TABLE IF NOT EXISTS editor_configuracion (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id              INTEGER DEFAULT 1,
    tamanio_fuente          INTEGER NOT NULL DEFAULT 14,
    tamanio_tabulacion      INTEGER NOT NULL DEFAULT 2,
    usar_espacios           INTEGER NOT NULL DEFAULT 1,
    resaltado_sintaxis      INTEGER NOT NULL DEFAULT 1,
    auto_formato_guardar    INTEGER NOT NULL DEFAULT 0,
    tema_editor             TEXT NOT NULL DEFAULT 'monokai',
    fecha_actualizacion     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS editor_historial_busqueda (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    termino                 TEXT NOT NULL,
    reemplazo               TEXT,
    sensible_mayusculas     INTEGER NOT NULL DEFAULT 0,
    palabra_completa        INTEGER NOT NULL DEFAULT 0,
    fecha                   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
