-- Archivo: sql/08_schema_menu_log.sql
-- Esquema SQLite compatible para persistencia de logs del modulo Menu-Log.

CREATE TABLE IF NOT EXISTS menu_log_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level       TEXT NOT NULL,
    source      TEXT NOT NULL,
    message     TEXT NOT NULL,
    job_id      TEXT
);
