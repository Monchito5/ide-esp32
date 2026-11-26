-- Opcional: persistencia futura. El módulo actual usa memoria y no requiere BD.
CREATE TABLE IF NOT EXISTS azul_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(12) NOT NULL,
    source VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    job_id VARCHAR(64)
);
