-- Archivo: sql/06_schema_simulacion.sql
-- Esquema del modulo Simulacion

CREATE TABLE IF NOT EXISTS simulacion_sesiones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id       TEXT    NOT NULL UNIQUE,
    nombre          TEXT    NOT NULL,
    chip            TEXT    NOT NULL DEFAULT 'ESP32-S3',
    motor           TEXT    NOT NULL DEFAULT 'esp_emulator',
    estado          TEXT    NOT NULL DEFAULT 'creada',
    firmware_cargado TEXT,
    firmware_version TEXT,
    fecha_creacion  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultimo_cambio TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulacion_componentes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id       TEXT    NOT NULL,
    componente_id   TEXT    NOT NULL,
    tipo            TEXT    NOT NULL,
    puerto          TEXT    NOT NULL,
    estado          TEXT    NOT NULL DEFAULT 'inactivo',
    valor           INTEGER NOT NULL DEFAULT 0,
    fecha_creacion  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES simulacion_sesiones(sesion_id)
);

CREATE TABLE IF NOT EXISTS simulacion_eventos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id       TEXT    NOT NULL,
    tipo            TEXT    NOT NULL,
    mensaje         TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    datos           TEXT,
    FOREIGN KEY (sesion_id) REFERENCES simulacion_sesiones(sesion_id)
);

CREATE TABLE IF NOT EXISTS simulacion_uart (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id       TEXT    NOT NULL,
    direccion       TEXT    NOT NULL DEFAULT 'entrada',
    mensaje         TEXT    NOT NULL,
    timestamp       TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES simulacion_sesiones(sesion_id)
);