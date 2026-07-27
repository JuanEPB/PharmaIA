UPDATE medicamentos
SET nombre = CONCAT('MEDICAMENTO SIN NOMBRE ', id)
WHERE nombre IS NULL
   OR TRIM(nombre) = '';

UPDATE medicamentos
SET lote = CONCAT('SIN-LOTE-', id)
WHERE lote IS NULL
   OR TRIM(lote) = '';

UPDATE medicamentos
SET caducidad = DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
WHERE caducidad IS NULL
   OR caducidad = '0000-00-00';

UPDATE medicamentos
SET stock = 0
WHERE stock < 0;

UPDATE medicamentos
SET stock_minimo = 10
WHERE stock_minimo < 0;

UPDATE medicamentos
SET precio = 0.00
WHERE precio < 0;

UPDATE usuarios
SET email = CONCAT('usuario-', id, '@example.local')
WHERE email IS NULL
   OR TRIM(email) = '';

UPDATE usuarios
SET nombre = CONCAT('Usuario ', id)
WHERE nombre IS NULL
   OR TRIM(nombre) = '';

UPDATE usuarios
SET apellido = 'Sin apellido'
WHERE apellido IS NULL
   OR TRIM(apellido) = '';

UPDATE proveedores
SET nombre = CONCAT('Proveedor ', id)
WHERE nombre IS NULL
   OR TRIM(nombre) = '';

CREATE INDEX IF NOT EXISTS idx_historial_exportacion_fecha
    ON historial_exportacion (fecha);

CREATE INDEX IF NOT EXISTS idx_historial_importacion_fecha
    ON historial_importacion (fecha);

CREATE INDEX IF NOT EXISTS idx_historial_importaciones_fecha
    ON historial_importaciones (fecha);
