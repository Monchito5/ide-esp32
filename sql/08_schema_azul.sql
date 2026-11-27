-- Archivo: sql/08_schema_azul.sql
-- Esquema SQLite compatible para persistencia de logs del modulo Azul.

CREATE TABLE IF NOT EXISTS azul_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level       TEXT NOT NULL,
    source      TEXT NOT NULL,
    message     TEXT NOT NULL,
    job_id      TEXT
);
