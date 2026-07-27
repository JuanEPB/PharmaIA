from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.movement_repository import (
    inventory_movement_repository,
)


class AnomalyDetectionService:
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
    def _integer(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _severity(score: int) -> str:
        if score >= 90:
            return "CRITICA"
        if score >= 70:
            return "ALTA"
        if score >= 40:
            return "MEDIA"
        return "BAJA"

    def _detect_in_movement(
        self,
        movement: dict[str, Any],
    ) -> list[dict[str, Any]]:
        anomalies: list[dict[str, Any]] = []

        movement_type = str(movement.get("tipo") or "").upper()
        quantity = self._integer(movement.get("cantidad"))
        previous_stock = self._integer(movement.get("stock_anterior"))
        new_stock = self._integer(movement.get("stock_nuevo"))
        medicine = str(movement.get("medicamento") or "Medicamento")

        base = {
            "movimiento_id": movement.get("id"),
            "medicamento_id": movement.get("medicamento_id"),
            "medicamento": medicine,
            "tipo_movimiento": movement_type,
            "cantidad": quantity,
            "stock_anterior": previous_stock,
            "stock_nuevo": new_stock,
            "fecha": movement.get("creado_en"),
        }

        if new_stock < 0:
            anomalies.append(
                {
                    **base,
                    "tipo_anomalia": "STOCK_NEGATIVO",
                    "severidad": "CRITICA",
                    "puntaje": 100,
                    "descripcion": (
                        f"{medicine} terminó con stock negativo."
                    ),
                }
            )

        expected_stock: int | None = None

        if movement_type in {"ENTRADA", "DEVOLUCION"}:
            expected_stock = previous_stock + quantity
        elif movement_type in {"SALIDA", "CADUCIDAD"}:
            expected_stock = previous_stock - quantity
        elif movement_type == "AJUSTE":
            expected_stock = quantity

        if expected_stock is not None and expected_stock != new_stock:
            anomalies.append(
                {
                    **base,
                    "tipo_anomalia": "STOCK_INCONSISTENTE",
                    "severidad": "ALTA",
                    "puntaje": 85,
                    "descripcion": (
                        "El stock resultante no coincide con el "
                        "tipo de movimiento y la cantidad registrada."
                    ),
                    "stock_esperado": expected_stock,
                }
            )

        if (
            movement_type in {"SALIDA", "CADUCIDAD"}
            and previous_stock > 0
            and quantity >= max(10, previous_stock * 0.8)
        ):
            score = 90 if quantity >= previous_stock else 75
            anomalies.append(
                {
                    **base,
                    "tipo_anomalia": "SALIDA_ELEVADA",
                    "severidad": self._severity(score),
                    "puntaje": score,
                    "descripcion": (
                        f"{medicine} tuvo una salida muy alta "
                        "respecto al stock anterior."
                    ),
                }
            )

        if (
            movement_type == "AJUSTE"
            and previous_stock > 0
            and abs(new_stock - previous_stock)
            >= max(10, previous_stock * 0.5)
        ):
            anomalies.append(
                {
                    **base,
                    "tipo_anomalia": "AJUSTE_BRUSCO",
                    "severidad": "MEDIA",
                    "puntaje": 55,
                    "descripcion": (
                        f"{medicine} tuvo un ajuste de stock "
                        "considerablemente diferente al stock previo."
                    ),
                }
            )

        return anomalies

    def detectar_anomalias(
        self,
        limite: int = 100,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(limite, 500))

        movements = inventory_movement_repository.listar_movimientos(
            limite=safe_limit,
            offset=0,
        )

        anomalies: list[dict[str, Any]] = []

        for movement in movements:
            anomalies.extend(self._detect_in_movement(movement))

        anomalies.sort(
            key=lambda item: item.get("puntaje", 0),
            reverse=True,
        )

        critical_count = sum(
            1
            for item in anomalies
            if item.get("severidad") == "CRITICA"
        )

        return self.serialize(
            {
                "total_movimientos_analizados": len(movements),
                "total_anomalias": len(anomalies),
                "anomalias_criticas": critical_count,
                "estado": (
                    "REQUIERE_REVISION"
                    if anomalies
                    else "SIN_ANOMALIAS"
                ),
                "anomalias": anomalies,
            }
        )


anomaly_detection_service = AnomalyDetectionService()
