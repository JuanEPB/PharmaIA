CREATE TABLE IF NOT EXISTS ordenes_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id INT NULL,
    estado ENUM(
        'BORRADOR',
        'PENDIENTE',
        'APROBADA',
        'CANCELADA',
        'RECIBIDA'
    ) NOT NULL DEFAULT 'BORRADOR',
    total_estimado DECIMAL(12, 2) NOT NULL DEFAULT 0,
    motivo VARCHAR(255) NULL,
    usuario_id INT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_orden_proveedor (proveedor_id),
    INDEX idx_orden_estado (estado),
    INDEX idx_orden_fecha (creado_en)
);

CREATE TABLE IF NOT EXISTS orden_compra_detalles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    medicamento_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12, 2) NOT NULL DEFAULT 0,
    subtotal DECIMAL(12, 2) NOT NULL DEFAULT 0,

    CONSTRAINT fk_detalle_orden
        FOREIGN KEY (orden_id)
        REFERENCES ordenes_compra(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_medicamento
        FOREIGN KEY (medicamento_id)
        REFERENCES medicamentos(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_detalle_orden (orden_id),
    INDEX idx_detalle_medicamento (medicamento_id)
);
