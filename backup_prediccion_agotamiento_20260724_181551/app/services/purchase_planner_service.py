from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.purchase_planner_repository import (
    purchase_planner_repository,
)
from app.services.conversation_memory import conversation_memory


class PurchasePlannerService:
    @classmethod
    def serialize(cls, value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, dict):
            return {
                str(key): cls.serialize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                cls.serialize(item)
                for item in value
            ]

        return value

    @staticmethod
    def _format_currency(value: float) -> str:
        formatted = f"{value:,.2f}"
        return f"${formatted}"

    def generar_plan(self) -> dict[str, Any]:
        configuration = purchase_planner_repository.obtener_configuracion()

        multiplier = float(
            configuration.get("multiplicador_stock_minimo") or 2
        )

        medicines = (
            purchase_planner_repository
            .obtener_medicamentos_para_compra(
                multiplicador_stock_minimo=multiplier
            )
        )

        total_cost = round(
            sum(
                float(item.get("costo_estimado") or 0)
                for item in medicines
            ),
            2,
        )

        providers = {
            item.get("proveedor_id")
            for item in medicines
        }

        critical_count = sum(
            1
            for item in medicines
            if item.get("nivel_riesgo") in {
                "CRITICO",
                "AGOTADO",
            }
        )

        return {
            "requiere_compra": bool(medicines),
            "total_medicamentos": len(medicines),
            "medicamentos_criticos": critical_count,
            "total_proveedores": len(providers),
            "costo_estimado": total_cost,
            "configuracion": self.serialize(configuration),
            "medicamentos": self.serialize(medicines),
        }

    def generar_sugerencia_automatica(
        self,
        session_id: str,
    ) -> dict[str, Any] | None:
        context = conversation_memory.get(session_id)

        if context.get("accion_pendiente"):
            return None

        plan = self.generar_plan()

        if not plan["requiere_compra"]:
            return None

        configuration = plan.get("configuracion", {})

        if not bool(
            configuration.get("planeacion_automatica", 1)
        ):
            return None

        minimum_amount = float(
            configuration.get("monto_minimo_alerta") or 0
        )

        if float(plan["costo_estimado"]) < minimum_amount:
            return None

        pending_action = {
            "tipo_accion": "CONFIRMAR_PLAN_COMPRA",
            "plan": plan,
        }

        conversation_memory.update(
            session_id,
            accion_pendiente=pending_action,
        )

        return {
            "accion_detectada": True,
            "requiere_confirmacion": True,
            "ejecutada": False,
            "respuesta": (
                f"He detectado {plan['total_medicamentos']} medicamentos "
                "por debajo del stock mínimo. "
                f"{plan['medicamentos_criticos']} están en nivel crítico "
                "o agotados. "
                f"Costo estimado: "
                f"{self._format_currency(plan['costo_estimado'])}. "
                f"Se crearían {plan['total_proveedores']} órdenes "
                "agrupadas por proveedor. "
                "¿Deseas generar la orden de compra? "
                "Escribe «confirmar» o «cancelar»."
            ),
            "plan_compra": plan,
        }

    def ejecutar_plan(
        self,
        session_id: str,
        usuario_id: int | None = None,
    ) -> dict[str, Any]:
        context = conversation_memory.get(session_id)
        pending = context.get("accion_pendiente") or {}

        if pending.get("tipo_accion") != "CONFIRMAR_PLAN_COMPRA":
            raise ValueError(
                "No existe un plan de compra pendiente en esta sesión."
            )

        current_plan = self.generar_plan()

        if not current_plan["requiere_compra"]:
            conversation_memory.update(
                session_id,
                accion_pendiente={},
            )

            return {
                "ejecutada": False,
                "respuesta": (
                    "El inventario cambió y ya no existen medicamentos "
                    "que requieran reposición."
                ),
                "ordenes": [],
            }

        orders = (
            purchase_planner_repository
            .crear_ordenes_desde_plan(
                medicamentos=current_plan["medicamentos"],
                usuario_id=usuario_id,
            )
        )

        total = round(
            sum(
                float(order.get("total_estimado") or 0)
                for order in orders
            ),
            2,
        )

        result = {
            "ejecutada": True,
            "total_ordenes": len(orders),
            "total_estimado": total,
            "ordenes": self.serialize(orders),
        }

        conversation_memory.update(
            session_id,
            accion_pendiente={},
            ultima_accion=result,
        )

        return {
            **result,
            "respuesta": (
                f"Se generaron {len(orders)} órdenes de compra "
                f"en estado BORRADOR por un total estimado de "
                f"{self._format_currency(total)}."
            ),
        }

    def cancelar_plan(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        conversation_memory.update(
            session_id,
            accion_pendiente={},
        )

        return {
            "ejecutada": False,
            "respuesta": (
                "El plan de compra pendiente fue cancelado."
            ),
        }


purchase_planner_service = PurchasePlannerService()
