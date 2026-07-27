CREATE TABLE IF NOT EXISTS app_ventas_sincronizadas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    venta_local_id VARCHAR(80) NOT NULL,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    fecha DATETIME NULL,
    cliente_nombre VARCHAR(160) NULL,
    farmacia_nombre VARCHAR(160) NULL,
    origen VARCHAR(40) NOT NULL DEFAULT 'app_movil',
    estado VARCHAR(40) NOT NULL DEFAULT 'sincronizada',
    payload JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_app_ventas_local_id (venta_local_id),
    INDEX idx_app_ventas_fecha (fecha),
    INDEX idx_app_ventas_estado (estado)
);
