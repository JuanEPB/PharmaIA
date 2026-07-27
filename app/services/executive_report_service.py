from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.services.predictive_dashboard_service import (
    predictive_dashboard_service,
)
from app.services.recommendation_service import recommendation_service


class ExecutiveReportService:
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
    def _headline(status: str) -> str:
        headlines = {
            "CRITICO": (
                "El inventario requiere atención inmediata."
            ),
            "ALTO": (
                "El inventario presenta riesgos relevantes."
            ),
            "PRECAUCION": (
                "El inventario se mantiene operativo con puntos "
                "por atender."
            ),
            "NORMAL": (
                "El inventario se encuentra estable."
            ),
        }

        return headlines.get(
            status,
            "El inventario requiere revisión."
        )

    def generar_reporte(
        self,
        limite: int = 5,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(limite, 20))

        dashboard = predictive_dashboard_service.obtener_dashboard(
            limite=safe_limit
        )
        recommendations = (
            recommendation_service.generar_recomendaciones(
                limite=safe_limit
            )
        )

        status = str(
            dashboard.get("estado_predictivo") or "SIN_DATOS"
        )
        score = int(
            dashboard.get("puntaje_riesgo") or 0
        )
        summary = dashboard.get("resumen", {})
        indicators = dashboard.get("indicadores", {})

        top_actions = [
            item.get("accion")
            for item in recommendations.get(
                "recomendaciones",
                [],
            )
            if item.get("accion")
        ][:safe_limit]

        narrative = (
            f"{self._headline(status)} "
            f"Estado predictivo: {status} con puntaje "
            f"{score}/100. "
            f"Hay {summary.get('total_medicamentos', 0)} "
            "medicamentos registrados, "
            f"{summary.get('agotados', 0)} agotados, "
            f"{summary.get('bajo_stock', 0)} con bajo stock, "
            f"{summary.get('caducados', 0)} caducados y "
            f"{summary.get('por_caducar_30_dias', 0)} próximos "
            "a caducar. "
            f"El plan de compra estima "
            f"{indicators.get('medicamentos_para_compra', 0)} "
            "medicamentos por "
            f"${float(indicators.get('costo_compra_estimado') or 0):,.2f}. "
            f"Se generaron {recommendations.get('total', 0)} "
            "acciones recomendadas."
        )

        return self.serialize(
            {
                "titulo": "Reporte Ejecutivo IA de Inventario",
                "fecha": date.today(),
                "estado": status,
                "puntaje_riesgo": score,
                "resumen": narrative,
                "metricas_clave": {
                    "total_medicamentos": summary.get(
                        "total_medicamentos",
                        0,
                    ),
                    "alertas_activas": indicators.get(
                        "alertas_activas",
                        0,
                    ),
                    "predicciones_riesgo": indicators.get(
                        "predicciones_riesgo",
                        0,
                    ),
                    "costo_compra_estimado": indicators.get(
                        "costo_compra_estimado",
                        0,
                    ),
                },
                "acciones_prioritarias": top_actions,
                "dashboard": dashboard,
                "recomendaciones": recommendations,
            }
        )


executive_report_service = ExecutiveReportService()
