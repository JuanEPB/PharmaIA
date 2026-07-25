CREATE TABLE IF NOT EXISTS configuracion_prediccion_agotamiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dias_historial INT NOT NULL DEFAULT 30,
    dias_cobertura_objetivo INT NOT NULL DEFAULT 30,
    dias_stock_seguridad INT NOT NULL DEFAULT 7,
    riesgo_critico_dias INT NOT NULL DEFAULT 7,
    riesgo_alto_dias INT NOT NULL DEFAULT 14,
    riesgo_medio_dias INT NOT NULL DEFAULT 30,
    incluir_caducidad_como_consumo TINYINT(1) NOT NULL DEFAULT 0,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO configuracion_prediccion_agotamiento (
    dias_historial,
    dias_cobertura_objetivo,
    dias_stock_seguridad,
    riesgo_critico_dias,
    riesgo_alto_dias,
    riesgo_medio_dias,
    incluir_caducidad_como_consumo,
    activo
)
SELECT
    30,
    30,
    7,
    7,
    14,
    30,
    0,
    1
WHERE NOT EXISTS (
    SELECT 1
    FROM configuracion_prediccion_agotamiento
);
