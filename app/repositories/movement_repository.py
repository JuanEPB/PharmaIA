from __future__ import annotations

from typing import Any

from app.repositories.database_adapter import create_connection


class InventoryMovementRepository:
    @staticmethod
    def _is_missing_table_error(error: Exception) -> bool:
        errno = getattr(error, "errno", None)
        message = str(error).lower()

        return errno == 1146 or (
            "movimientos_inventario" in message
            and (
                "doesn't exist" in message
                or "does not exist" in message
                or "no such table" in message
            )
        )

    @staticmethod
    def _dictionary_cursor(connection: Any) -> Any:
        try:
            return connection.cursor(dictionary=True)
        except TypeError:
            return connection.cursor()

    @staticmethod
    def _row_to_dict(cursor: Any, row: Any) -> dict[str, Any]:
        if row is None:
            return {}
        if isinstance(row, dict):
            return row
        description = getattr(cursor, "description", None)
        if not description:
            return {}
        return dict(zip([column[0] for column in description], row))

    def obtener_medicamento_para_actualizar(self, connection: Any, medicamento_id: int) -> dict[str, Any]:
        cursor = self._dictionary_cursor(connection)
        try:
            cursor.execute(
                """
                SELECT id, nombre, lote, caducidad, stock, stock_minimo,
                       precio, proveedorId, categoriaId
                FROM medicamentos
                WHERE id = %s
                FOR UPDATE
                """,
                (medicamento_id,),
            )
            return self._row_to_dict(cursor, cursor.fetchone())
        finally:
            cursor.close()

    def actualizar_stock(self, connection: Any, medicamento_id: int, nuevo_stock: int) -> None:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE medicamentos SET stock = %s WHERE id = %s",
                (nuevo_stock, medicamento_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("No se pudo actualizar el stock del medicamento.")
        finally:
            cursor.close()

    def crear_movimiento(
        self,
        connection: Any,
        medicamento_id: int,
        tipo: str,
        cantidad: int,
        stock_anterior: int,
        stock_nuevo: int,
        motivo: str | None,
        usuario_id: int | None,
    ) -> int:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO movimientos_inventario (
                    medicamento_id, tipo, cantidad, stock_anterior,
                    stock_nuevo, motivo, usuario_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    medicamento_id,
                    tipo,
                    cantidad,
                    stock_anterior,
                    stock_nuevo,
                    motivo,
                    usuario_id,
                ),
            )
            if not cursor.lastrowid:
                raise RuntimeError("No se pudo obtener el ID del movimiento.")
            return int(cursor.lastrowid)
        finally:
            cursor.close()

    def obtener_medicamento(self, medicamento_id: int) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._dictionary_cursor(connection)
        try:
            cursor.execute(
                """
                SELECT id, nombre, lote, caducidad, stock, stock_minimo,
                       precio, proveedorId, categoriaId
                FROM medicamentos
                WHERE id = %s
                """,
                (medicamento_id,),
            )
            return self._row_to_dict(cursor, cursor.fetchone())
        finally:
            cursor.close()
            connection.close()

    def obtener_movimiento(self, movimiento_id: int) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._dictionary_cursor(connection)
        try:
            cursor.execute(
                """
                SELECT mi.id, mi.medicamento_id, m.nombre AS medicamento,
                       m.lote, mi.tipo, mi.cantidad, mi.stock_anterior,
                       mi.stock_nuevo, mi.motivo, mi.usuario_id, mi.creado_en
                FROM movimientos_inventario AS mi
                INNER JOIN medicamentos AS m ON m.id = mi.medicamento_id
                WHERE mi.id = %s
                """,
                (movimiento_id,),
            )
            return self._row_to_dict(cursor, cursor.fetchone())
        finally:
            cursor.close()
            connection.close()

    def listar_movimientos(
        self,
        medicamento_id: int | None = None,
        tipo: str | None = None,
        usuario_id: int | None = None,
        limite: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        connection = create_connection()
        cursor = self._dictionary_cursor(connection)
        conditions: list[str] = []
        parameters: list[Any] = []

        if medicamento_id is not None:
            conditions.append("mi.medicamento_id = %s")
            parameters.append(medicamento_id)
        if tipo is not None:
            conditions.append("mi.tipo = %s")
            parameters.append(tipo)
        if usuario_id is not None:
            conditions.append("mi.usuario_id = %s")
            parameters.append(usuario_id)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        parameters.extend([limite, offset])

        query = f"""
            SELECT mi.id, mi.medicamento_id, m.nombre AS medicamento,
                   m.lote, mi.tipo, mi.cantidad, mi.stock_anterior,
                   mi.stock_nuevo, mi.motivo, mi.usuario_id, mi.creado_en
            FROM movimientos_inventario AS mi
            INNER JOIN medicamentos AS m ON m.id = mi.medicamento_id
            {where_clause}
            ORDER BY mi.creado_en DESC, mi.id DESC
            LIMIT %s OFFSET %s
        """

        try:
            cursor.execute(query, tuple(parameters))
            return [self._row_to_dict(cursor, row) for row in cursor.fetchall()]
        except Exception as exc:
            if self._is_missing_table_error(exc):
                return []
            raise
        finally:
            cursor.close()
            connection.close()

    def obtener_ultimo_movimiento(self, medicamento_id: int) -> dict[str, Any]:
        connection = create_connection()
        cursor = self._dictionary_cursor(connection)
        try:
            cursor.execute(
                """
                SELECT mi.id, mi.medicamento_id, m.nombre AS medicamento,
                       m.lote, mi.tipo, mi.cantidad, mi.stock_anterior,
                       mi.stock_nuevo, mi.motivo, mi.usuario_id, mi.creado_en
                FROM movimientos_inventario AS mi
                INNER JOIN medicamentos AS m ON m.id = mi.medicamento_id
                WHERE mi.medicamento_id = %s
                ORDER BY mi.creado_en DESC, mi.id DESC
                LIMIT 1
                """,
                (medicamento_id,),
            )
            return self._row_to_dict(cursor, cursor.fetchone())
        except Exception as exc:
            if self._is_missing_table_error(exc):
                return {}
            raise
        finally:
            cursor.close()
            connection.close()


inventory_movement_repository = InventoryMovementRepository()
