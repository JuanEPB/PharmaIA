from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.inventory_repository import (
    inventory_repository,
)


class InventoryStatisticsService:
    @classmethod
    def serialize(cls, value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, dict):
            return {
                key: cls.serialize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                cls.serialize(item)
                for item in value
            ]

        return value

    @staticmethod
    def _integer(
        value: Any,
    ) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _float(
        value: Any,
    ) -> float:
        try:
            return round(float(value or 0), 2)
        except (TypeError, ValueError):
            return 0.0

    def obtener_resumen(
        self,
    ) -> dict[str, Any]:
        raw = inventory_repository.obtener_resumen()

        total = self._integer(
            raw.get("total_medicamentos")
        )

        agotados = self._integer(
            raw.get("agotados")
        )

        bajo_stock = self._integer(
            raw.get("bajo_stock")
        )

        caducados = self._integer(
            raw.get("caducados")
        )

        por_caducar = self._integer(
            raw.get("por_caducar_30_dias")
        )

        medicamentos_con_alerta = (
            agotados
            + bajo_stock
            + caducados
            + por_caducar
        )

        porcentaje_alerta = (
            round(
                medicamentos_con_alerta
                / total
                * 100,
                2,
            )
            if total > 0
            else 0.0
        )

        return {
            "total_medicamentos": total,
            "unidades_disponibles": self._integer(
                raw.get("unidades_disponibles")
            ),
            "agotados": agotados,
            "bajo_stock": bajo_stock,
            "caducados": caducados,
            "por_caducar_30_dias": por_caducar,
            "valor_total_inventario": self._float(
                raw.get("valor_total_inventario")
            ),
            "promedio_stock": self._float(
                raw.get("promedio_stock")
            ),
            "precio_promedio": self._float(
                raw.get("precio_promedio")
            ),
            "medicamentos_con_alerta": medicamentos_con_alerta,
            "porcentaje_con_alerta": porcentaje_alerta,
            "estado_general": self._calculate_general_status(
                agotados=agotados,
                bajo_stock=bajo_stock,
                caducados=caducados,
                total=total,
            ),
        }

    @staticmethod
    def _calculate_general_status(
        agotados: int,
        bajo_stock: int,
        caducados: int,
        total: int,
    ) -> str:
        if total == 0:
            return "SIN_DATOS"

        critical = agotados + caducados

        if critical > 0:
            return "CRITICO"

        if bajo_stock > 0:
            return "PRECAUCION"

        return "NORMAL"

    def obtener_alertas(
        self,
        limite: int = 100,
    ) -> list[dict[str, Any]]:
        safe_limit = max(
            1,
            min(limite, 500),
        )

        rows = inventory_repository.obtener_alertas(
            safe_limit
        )

        alerts: list[dict[str, Any]] = []

        for row in rows:
            serialized = self.serialize(row)

            state = str(
                serialized.get("estado", "NORMAL")
            )

            quantity = self._integer(
                serialized.get("cantidad_recomendada")
            )

            serialized["recomendacion"] = (
                self._build_recommendation(
                    state=state,
                    medicine=str(
                        serialized.get(
                            "nombre",
                            "Medicamento",
                        )
                    ),
                    quantity=quantity,
                    days=self._integer(
                        serialized.get(
                            "dias_para_caducar"
                        )
                    ),
                )
            )

            serialized["prioridad"] = (
                self._priority(state)
            )

            alerts.append(serialized)

        return alerts

    @staticmethod
    def _priority(
        state: str,
    ) -> int:
        priorities = {
            "CADUCADO": 1,
            "AGOTADO": 2,
            "CRITICO": 3,
            "PRECAUCION": 4,
            "PROXIMO_A_CADUCAR": 5,
            "NORMAL": 6,
        }

        return priorities.get(
            state,
            6,
        )

    @staticmethod
    def _build_recommendation(
        state: str,
        medicine: str,
        quantity: int,
        days: int,
    ) -> str:
        if state == "CADUCADO":
            return (
                f"Retirar {medicine} del inventario disponible "
                "y registrar la baja por caducidad."
            )

        if state == "AGOTADO":
            return (
                f"Solicitar al menos {max(quantity, 1)} unidades "
                f"de {medicine}."
            )

        if state == "CRITICO":
            return (
                f"Realizar una reposición prioritaria de "
                f"{max(quantity, 1)} unidades de {medicine}."
            )

        if state == "PRECAUCION":
            return (
                f"Programar la reposición de "
                f"{max(quantity, 1)} unidades de {medicine}."
            )

        if state == "PROXIMO_A_CADUCAR":
            return (
                f"Revisar la rotación de {medicine}; "
                f"caduca en aproximadamente {days} días."
            )

        return "El inventario se encuentra dentro de los niveles esperados."

    def obtener_categorias(
        self,
    ) -> list[dict[str, Any]]:
        return self.serialize(
            inventory_repository
            .obtener_estadisticas_categorias()
        )

    def obtener_proveedores(
        self,
    ) -> list[dict[str, Any]]:
        return self.serialize(
            inventory_repository
            .obtener_estadisticas_proveedores()
        )

    def obtener_ranking_stock(
        self,
        limite: int = 10,
    ) -> dict[str, Any]:
        safe_limit = max(
            1,
            min(limite, 100),
        )

        return {
            "mayor_stock": self.serialize(
                inventory_repository.obtener_mayor_stock(
                    safe_limit
                )
            ),
            "menor_stock": self.serialize(
                inventory_repository.obtener_menor_stock(
                    safe_limit
                )
            ),
        }


inventory_statistics_service = InventoryStatisticsService()
