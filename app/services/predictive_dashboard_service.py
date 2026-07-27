from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.services.depletion_prediction_service import (
    depletion_prediction_service,
)
from app.services.inventory_statistics_service import (
    inventory_statistics_service,
)
from app.services.purchase_planner_service import purchase_planner_service


class PredictiveDashboardService:
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
    def _risk_score(
        summary: dict[str, Any],
        predictions: list[dict[str, Any]],
        purchase_plan: dict[str, Any],
    ) -> int:
        total = max(
            int(summary.get("total_medicamentos") or 0),
            1,
        )

        critical_inventory = (
            int(summary.get("agotados") or 0)
            + int(summary.get("caducados") or 0)
        )

        critical_predictions = sum(
            1
            for prediction in predictions
            if prediction.get("nivel_riesgo")
            in {"AGOTADO", "CRITICO", "ALTO"}
        )

        purchase_pressure = int(
            purchase_plan.get("total_medicamentos") or 0
        )

        score = round(
            (
                critical_inventory * 35
                + critical_predictions * 25
                + purchase_pressure * 15
            )
            / total
        )

        return max(
            0,
            min(score, 100),
        )

    @staticmethod
    def _status_from_score(score: int) -> str:
        if score >= 70:
            return "CRITICO"

        if score >= 40:
            return "ALTO"

        if score >= 15:
            return "PRECAUCION"

        return "NORMAL"

    @staticmethod
    def _top_predictions(
        predictions: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        return predictions[:limit]

    @staticmethod
    def _build_recommendations(
        summary: dict[str, Any],
        alerts: list[dict[str, Any]],
        predictions: list[dict[str, Any]],
        purchase_plan: dict[str, Any],
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []

        if int(summary.get("caducados") or 0) > 0:
            recommendations.append(
                {
                    "prioridad": "ALTA",
                    "tipo": "CADUCIDAD",
                    "accion": (
                        "Retirar medicamentos caducados y registrar "
                        "la baja de inventario."
                    ),
                }
            )

        if purchase_plan.get("requiere_compra"):
            recommendations.append(
                {
                    "prioridad": "ALTA",
                    "tipo": "COMPRA",
                    "accion": (
                        "Revisar el plan de compras y confirmar "
                        "órdenes para medicamentos críticos."
                    ),
                    "total_medicamentos": purchase_plan.get(
                        "total_medicamentos"
                    ),
                    "costo_estimado": purchase_plan.get(
                        "costo_estimado"
                    ),
                }
            )

        if predictions:
            first_prediction = predictions[0]
            medicine = first_prediction.get(
                "medicamento",
                {},
            )

            recommendations.append(
                {
                    "prioridad": "MEDIA",
                    "tipo": "AGOTAMIENTO",
                    "accion": (
                        "Dar seguimiento al medicamento con menor "
                        "cobertura estimada."
                    ),
                    "medicamento": medicine.get("nombre"),
                    "nivel_riesgo": first_prediction.get(
                        "nivel_riesgo"
                    ),
                    "cobertura_estimada_dias": (
                        first_prediction.get(
                            "cobertura_estimada_dias"
                        )
                    ),
                }
            )

        if alerts:
            recommendations.append(
                {
                    "prioridad": "MEDIA",
                    "tipo": "ALERTAS",
                    "accion": (
                        "Atender primero las alertas con prioridad "
                        "más alta del inventario."
                    ),
                    "total_alertas": len(alerts),
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "prioridad": "BAJA",
                    "tipo": "OPERACION",
                    "accion": (
                        "Mantener monitoreo periódico; no hay "
                        "riesgos relevantes en este momento."
                    ),
                }
            )

        return recommendations

    @staticmethod
    def _executive_summary(
        status: str,
        score: int,
        summary: dict[str, Any],
        alerts: list[dict[str, Any]],
        predictions: list[dict[str, Any]],
        purchase_plan: dict[str, Any],
    ) -> str:
        return (
            f"Estado predictivo: {status}. "
            f"Puntaje de riesgo: {score}/100. "
            f"Inventario: {summary.get('total_medicamentos', 0)} "
            "medicamentos registrados, "
            f"{summary.get('agotados', 0)} agotados, "
            f"{summary.get('bajo_stock', 0)} con bajo stock y "
            f"{summary.get('caducados', 0)} caducados. "
            f"Alertas activas: {len(alerts)}. "
            f"Predicciones de riesgo: {len(predictions)}. "
            f"Compra sugerida: "
            f"{purchase_plan.get('total_medicamentos', 0)} "
            "medicamentos por un estimado de "
            f"${float(purchase_plan.get('costo_estimado') or 0):,.2f}."
        )

    def obtener_dashboard(
        self,
        limite: int = 10,
    ) -> dict[str, Any]:
        safe_limit = max(
            1,
            min(limite, 50),
        )

        summary = inventory_statistics_service.obtener_resumen()
        alerts = inventory_statistics_service.obtener_alertas(
            safe_limit
        )
        predictions_result = (
            depletion_prediction_service.predecir_inventario(
                solo_riesgo=True
            )
        )
        predictions = predictions_result.get(
            "predicciones",
            [],
        )
        purchase_plan = purchase_planner_service.generar_plan()

        top_predictions = self._top_predictions(
            predictions,
            safe_limit,
        )
        score = self._risk_score(
            summary=summary,
            predictions=top_predictions,
            purchase_plan=purchase_plan,
        )
        status = self._status_from_score(score)
        recommendations = self._build_recommendations(
            summary=summary,
            alerts=alerts,
            predictions=top_predictions,
            purchase_plan=purchase_plan,
        )

        return self.serialize(
            {
                "estado_predictivo": status,
                "puntaje_riesgo": score,
                "resumen": summary,
                "indicadores": {
                    "alertas_activas": len(alerts),
                    "predicciones_riesgo": len(top_predictions),
                    "medicamentos_para_compra": (
                        purchase_plan.get("total_medicamentos", 0)
                    ),
                    "costo_compra_estimado": (
                        purchase_plan.get("costo_estimado", 0)
                    ),
                },
                "alertas": alerts,
                "predicciones": top_predictions,
                "plan_compra": purchase_plan,
                "recomendaciones": recommendations,
                "resumen_ejecutivo": self._executive_summary(
                    status=status,
                    score=score,
                    summary=summary,
                    alerts=alerts,
                    predictions=top_predictions,
                    purchase_plan=purchase_plan,
                ),
            }
        )


predictive_dashboard_service = PredictiveDashboardService()
