CREATE TABLE IF NOT EXISTS configuracion_compras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dias_cobertura_objetivo INT NOT NULL DEFAULT 30,
    multiplicador_stock_minimo DECIMAL(6, 2) NOT NULL DEFAULT 2.00,
    monto_minimo_alerta DECIMAL(12, 2) NOT NULL DEFAULT 0,
    planeacion_automatica TINYINT(1) NOT NULL DEFAULT 1,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO configuracion_compras (
    dias_cobertura_objetivo,
    multiplicador_stock_minimo,
    monto_minimo_alerta,
    planeacion_automatica
)
SELECT
    30,
    2.00,
    0,
    1
WHERE NOT EXISTS (
    SELECT 1
    FROM configuracion_compras
);
