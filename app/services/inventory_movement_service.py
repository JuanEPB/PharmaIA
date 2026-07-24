from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.database_adapter import create_connection
from app.repositories.movement_repository import inventory_movement_repository


VALID_MOVEMENT_TYPES = {"ENTRADA", "SALIDA", "AJUSTE", "DEVOLUCION", "CADUCIDAD"}


class InventoryMovementService:
    @classmethod
    def serialize(cls, value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {str(key): cls.serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls.serialize(item) for item in value]
        return value

    @staticmethod
    def normalize_type(value: str) -> str:
        return str(value or "").strip().upper()

    @staticmethod
    def validate_quantity(quantity: int) -> int:
        try:
            normalized = int(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("La cantidad debe ser un número entero.") from exc
        if normalized <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        return normalized

    @staticmethod
    def calculate_new_stock(movement_type: str, current_stock: int, quantity: int) -> int:
        if movement_type in {"ENTRADA", "DEVOLUCION"}:
            return current_stock + quantity
        if movement_type in {"SALIDA", "CADUCIDAD"}:
            new_stock = current_stock - quantity
            if new_stock < 0:
                raise ValueError("El movimiento produciría un stock negativo.")
            return new_stock
        if movement_type == "AJUSTE":
            return quantity
        raise ValueError("Tipo de movimiento inválido.")

    def registrar_movimiento(
        self,
        medicamento_id: int,
        tipo: str,
        cantidad: int,
        motivo: str | None = None,
        usuario_id: int | None = None,
    ) -> dict[str, Any]:
        normalized_type = self.normalize_type(tipo)
        if normalized_type not in VALID_MOVEMENT_TYPES:
            raise ValueError(
                "Tipo de movimiento inválido. Valores permitidos: "
                + ", ".join(sorted(VALID_MOVEMENT_TYPES))
            )

        normalized_quantity = self.validate_quantity(cantidad)
        try:
            normalized_medicine_id = int(medicamento_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("El medicamento_id debe ser un número entero.") from exc

        connection = create_connection()
        try:
            try:
                connection.start_transaction()
            except AttributeError:
                try:
                    connection.autocommit = False
                except Exception:
                    pass

            medicine = inventory_movement_repository.obtener_medicamento_para_actualizar(
                connection=connection,
                medicamento_id=normalized_medicine_id,
            )
            if not medicine:
                raise ValueError("El medicamento indicado no existe.")

            current_stock = int(medicine.get("stock") or 0)
            new_stock = self.calculate_new_stock(
                movement_type=normalized_type,
                current_stock=current_stock,
                quantity=normalized_quantity,
            )

            inventory_movement_repository.actualizar_stock(
                connection=connection,
                medicamento_id=normalized_medicine_id,
                nuevo_stock=new_stock,
            )

            movement_id = inventory_movement_repository.crear_movimiento(
                connection=connection,
                medicamento_id=normalized_medicine_id,
                tipo=normalized_type,
                cantidad=normalized_quantity,
                stock_anterior=current_stock,
                stock_nuevo=new_stock,
                motivo=str(motivo).strip() if motivo else None,
                usuario_id=usuario_id,
            )
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                connection.close()
            except Exception:
                pass

        movement = inventory_movement_repository.obtener_movimiento(movement_id)
        return {
            "mensaje": "Movimiento registrado correctamente.",
            "movimiento": self.serialize(movement),
        }

    def listar_movimientos(
        self,
        medicamento_id: int | None = None,
        tipo: str | None = None,
        usuario_id: int | None = None,
        limite: int = 100,
        pagina: int = 1,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(int(limite), 500))
        safe_page = max(1, int(pagina))
        normalized_type = None
        if tipo:
            normalized_type = self.normalize_type(tipo)
            if normalized_type not in VALID_MOVEMENT_TYPES:
                raise ValueError("El filtro tipo no es válido.")

        rows = inventory_movement_repository.listar_movimientos(
            medicamento_id=medicamento_id,
            tipo=normalized_type,
            usuario_id=usuario_id,
            limite=safe_limit,
            offset=(safe_page - 1) * safe_limit,
        )
        return {
            "pagina": safe_page,
            "limite": safe_limit,
            "total_resultados": len(rows),
            "movimientos": self.serialize(rows),
        }

    def obtener_historial_medicamento(self, medicamento_id: int, limite: int = 100, pagina: int = 1) -> dict[str, Any]:
        medicine = inventory_movement_repository.obtener_medicamento(medicamento_id)
        if not medicine:
            raise ValueError("El medicamento indicado no existe.")
        result = self.listar_movimientos(
            medicamento_id=medicamento_id,
            limite=limite,
            pagina=pagina,
        )
        result["medicamento"] = self.serialize(medicine)
        return result

    def obtener_ultimo_movimiento(self, medicamento_id: int) -> dict[str, Any]:
        medicine = inventory_movement_repository.obtener_medicamento(medicamento_id)
        if not medicine:
            raise ValueError("El medicamento indicado no existe.")
        movement = inventory_movement_repository.obtener_ultimo_movimiento(medicamento_id)
        return {
            "medicamento": self.serialize(medicine),
            "tiene_movimientos": bool(movement),
            "ultimo_movimiento": self.serialize(movement),
        }


inventory_movement_service = InventoryMovementService()
