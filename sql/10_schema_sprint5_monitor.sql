-- Archivo: sql/10_schema_sprint5_monitor.sql
-- Esquema SQLite del Sprint 5 para eventos del Monitor Serie, muestras de Plotter y exportacion de logs.

CREATE TABLE IF NOT EXISTS herramientas_eventos_serie (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id       TEXT    NOT NULL,
    puerto          TEXT    NOT NULL,
    baudrate        INTEGER NOT NULL DEFAULT 115200,
    direccion       TEXT    NOT NULL DEFAULT 'RX',
    nivel           TEXT    NOT NULL DEFAULT 'INFO',
    linea           TEXT    NOT NULL,
    canales_json    TEXT,
    fecha           TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eventos_serie_fecha
    ON herramientas_eventos_serie (fecha DESC);

CREATE INDEX IF NOT EXISTS idx_eventos_serie_sesion
    ON herramientas_eventos_serie (sesion_id, id ASC);
