ALTER TABLE medicamentos
    ADD COLUMN IF NOT EXISTS stock_minimo INT NOT NULL DEFAULT 10
    AFTER stock;

ALTER TABLE medicamentos
    ADD COLUMN IF NOT EXISTS farmacia_id INT NULL
    AFTER id;

UPDATE medicamentos
SET farmacia_id = (
    SELECT id
    FROM farmacia
    ORDER BY id
    LIMIT 1
)
WHERE farmacia_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM farmacia
  );

ALTER TABLE medicamentos
    MODIFY precio DECIMAL(12, 2) NOT NULL DEFAULT 0.00;

CREATE INDEX IF NOT EXISTS idx_medicamentos_nombre
    ON medicamentos (nombre);

CREATE INDEX IF NOT EXISTS idx_medicamentos_lote
    ON medicamentos (lote);

CREATE INDEX IF NOT EXISTS idx_medicamentos_caducidad
    ON medicamentos (caducidad);

CREATE INDEX IF NOT EXISTS idx_medicamentos_stock
    ON medicamentos (stock);

CREATE INDEX IF NOT EXISTS idx_medicamentos_stock_minimo
    ON medicamentos (stock_minimo);

CREATE INDEX IF NOT EXISTS idx_medicamentos_farmacia
    ON medicamentos (farmacia_id);

CREATE INDEX IF NOT EXISTS idx_medicamentos_farmacia_nombre
    ON medicamentos (farmacia_id, nombre);

CREATE INDEX IF NOT EXISTS idx_medicamentos_farmacia_caducidad
    ON medicamentos (farmacia_id, caducidad);

ALTER TABLE venta
    ADD COLUMN IF NOT EXISTS farmacia_id INT NULL
    AFTER fecha;

CREATE INDEX IF NOT EXISTS idx_venta_fecha
    ON venta (fecha);

CREATE INDEX IF NOT EXISTS idx_venta_usuario
    ON venta (usuarioId);

CREATE INDEX IF NOT EXISTS idx_venta_farmacia
    ON venta (farmacia_id);

CREATE INDEX IF NOT EXISTS idx_venta_detalle_medicamento
    ON venta_detalle (medicamentoId);

CREATE INDEX IF NOT EXISTS idx_pedidos_estatus
    ON pedidos (estatus);

CREATE INDEX IF NOT EXISTS idx_pedidos_fecha
    ON pedidos (fecha_pedido);
