from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.services.anomaly_detection_service import (
    anomaly_detection_service,
)
from app.services.depletion_prediction_service import (
    depletion_prediction_service,
)
from app.services.inventory_statistics_service import (
    inventory_statistics_service,
)
from app.services.purchase_planner_service import purchase_planner_service


class RecommendationService:
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
    def _priority_score(priority: str) -> int:
        return {
            "CRITICA": 100,
            "ALTA": 80,
            "MEDIA": 50,
            "BAJA": 20,
        }.get(priority, 10)

    @staticmethod
    def _app_fields(
        explanation: str,
        action: str,
        blocks_actions: bool = False,
    ) -> dict[str, Any]:
        return {
            "explicacion_app": explanation,
            "accion_app": action,
            "bloquea_acciones": blocks_actions,
        }

    def generar_recomendaciones(
        self,
        limite: int = 10,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(limite, 50))

        summary = inventory_statistics_service.obtener_resumen()
        alerts = inventory_statistics_service.obtener_alertas(
            safe_limit
        )
        predictions = (
            depletion_prediction_service.predecir_inventario(
                solo_riesgo=True
            ).get("predicciones", [])
        )
        purchase_plan = purchase_planner_service.generar_plan()
        anomalies = anomaly_detection_service.detectar_anomalias(
            limite=100
        )

        recommendations = []

        if anomalies.get("anomalias_criticas", 0) > 0:
            recommendations.append(
                {
                    "prioridad": "CRITICA",
                    "tipo": "ANOMALIA",
                    "accion": (
                        "Revisar anomalias criticas antes de "
                        "confirmar compras o ajustes nuevos."
                    ),
                    "impacto": (
                        "Puede existir error operativo o stock "
                        "inconsistente."
                    ),
                    **self._app_fields(
                        explanation=(
                            "La IA encontro valores fuera de lo normal. "
                            "Revisa antes de autorizar compras o ajustes."
                        ),
                        action="Abrir revision de anomalias",
                        blocks_actions=True,
                    ),
                    "total": anomalies.get("anomalias_criticas"),
                }
            )

        if int(summary.get("caducados") or 0) > 0:
            recommendations.append(
                {
                    "prioridad": "CRITICA",
                    "tipo": "CADUCIDAD",
                    "accion": (
                        "Retirar medicamentos caducados del inventario "
                        "disponible y registrar baja por caducidad."
                    ),
                    "impacto": "Reduce riesgo sanitario y operativo.",
                    **self._app_fields(
                        explanation=(
                            "Hay medicamentos vencidos. No deben "
                            "venderse ni contarse como stock disponible."
                        ),
                        action="Ver medicamentos caducados",
                        blocks_actions=True,
                    ),
                    "total": summary.get("caducados"),
                }
            )

        if purchase_plan.get("requiere_compra"):
            recommendations.append(
                {
                    "prioridad": "ALTA",
                    "tipo": "COMPRA",
                    "accion": (
                        "Generar ordenes de compra en borrador para "
                        "medicamentos bajo minimo."
                    ),
                    "impacto": (
                        "Disminuye riesgo de agotamiento en productos "
                        "criticos."
                    ),
                    **self._app_fields(
                        explanation=(
                            "La IA comparo stock actual contra stock "
                            "minimo y detecto productos que necesitan "
                            "reposicion."
                        ),
                        action="Revisar plan de compra",
                    ),
                    "total": purchase_plan.get("total_medicamentos"),
                    "costo_estimado": purchase_plan.get(
                        "costo_estimado"
                    ),
                }
            )

        for prediction in predictions[:safe_limit]:
            if prediction.get("nivel_riesgo") not in {
                "AGOTADO",
                "CRITICO",
                "ALTO",
            }:
                continue

            medicine = prediction.get("medicamento", {})

            recommendations.append(
                {
                    "prioridad": "ALTA",
                    "tipo": "AGOTAMIENTO",
                    "accion": (
                        "Reponer o validar disponibilidad del "
                        "medicamento con riesgo de agotamiento."
                    ),
                    "impacto": (
                        "Evita ruptura de stock en operacion diaria."
                    ),
                    **self._app_fields(
                        explanation=(
                            "El stock disponible puede no alcanzar para "
                            "la demanda estimada. Prioriza su reposicion."
                        ),
                        action="Ver prediccion de agotamiento",
                    ),
                    "medicamento": medicine.get("nombre"),
                    "nivel_riesgo": prediction.get("nivel_riesgo"),
                    "cobertura_estimada_dias": prediction.get(
                        "cobertura_estimada_dias"
                    ),
                    "cantidad_compra_recomendada": prediction.get(
                        "cantidad_compra_recomendada"
                    ),
                }
            )

        if alerts:
            recommendations.append(
                {
                    "prioridad": "MEDIA",
                    "tipo": "ALERTAS",
                    "accion": (
                        "Atender alertas de inventario ordenadas por "
                        "prioridad."
                    ),
                    "impacto": (
                        "Mejora la respuesta ante bajo stock y "
                        "caducidades proximas."
                    ),
                    **self._app_fields(
                        explanation=(
                            "Hay alertas activas que requieren revision "
                            "operativa desde la app."
                        ),
                        action="Abrir alertas de inventario",
                    ),
                    "total": len(alerts),
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "prioridad": "BAJA",
                    "tipo": "MONITOREO",
                    "accion": (
                        "Mantener revision periodica del inventario."
                    ),
                    "impacto": (
                        "El inventario no muestra riesgos relevantes."
                    ),
                    **self._app_fields(
                        explanation=(
                            "La IA no encontro riesgos importantes con "
                            "los datos actuales."
                        ),
                        action="Ver resumen de inventario",
                    ),
                }
            )

        recommendations.sort(
            key=lambda item: self._priority_score(
                item.get("prioridad", "")
            ),
            reverse=True,
        )

        limited = recommendations[:safe_limit]

        return self.serialize(
            {
                "total": len(limited),
                "total_generadas": len(recommendations),
                "recomendaciones": limited,
                "fuentes": {
                    "alertas": len(alerts),
                    "predicciones": len(predictions),
                    "anomalias": anomalies.get(
                        "total_anomalias",
                        0,
                    ),
                    "plan_compra": bool(
                        purchase_plan.get("requiere_compra")
                    ),
                },
            }
        )


recommendation_service = RecommendationService()
