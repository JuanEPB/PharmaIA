CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicamento_id INT NOT NULL,
    tipo ENUM('ENTRADA','SALIDA','AJUSTE','DEVOLUCION','CADUCIDAD') NOT NULL,
    cantidad INT NOT NULL,
    stock_anterior INT NOT NULL,
    stock_nuevo INT NOT NULL,
    motivo VARCHAR(255) NULL,
    usuario_id INT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimiento_medicamento
        FOREIGN KEY (medicamento_id)
        REFERENCES medicamentos(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    INDEX idx_movimientos_medicamento (medicamento_id),
    INDEX idx_movimientos_tipo (tipo),
    INDEX idx_movimientos_fecha (creado_en),
    INDEX idx_movimientos_usuario (usuario_id)
);
