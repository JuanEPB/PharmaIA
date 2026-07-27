from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.anomaly_detection_service import (
    anomaly_detection_service,
)
from app.services.executive_report_service import executive_report_service
from app.services.purchase_planner_service import purchase_planner_service
from app.services.recommendation_service import recommendation_service


class AutonomousAgentService:
    @staticmethod
    def _action(
        action_type: str,
        description: str,
        priority: str,
        executable: bool = False,
    ) -> dict[str, Any]:
        return {
            "tipo": action_type,
            "descripcion": description,
            "prioridad": priority,
            "ejecutable": executable,
        }

    def planificar_ciclo(
        self,
        autorizar_acciones: bool = False,
        usuario_id: int | None = None,
        sesion_id: str = "agente-autonomo",
    ) -> dict[str, Any]:
        report = executive_report_service.generar_reporte(
            limite=5
        )
        recommendations = (
            recommendation_service.generar_recomendaciones(
                limite=10
            )
        )
        anomalies = anomaly_detection_service.detectar_anomalias(
            limite=100
        )
        purchase_plan = purchase_planner_service.generar_plan()

        actions: list[dict[str, Any]] = []

        if anomalies.get("anomalias_criticas", 0) > 0:
            actions.append(
                self._action(
                    action_type="REVISAR_ANOMALIAS",
                    description=(
                        "Bloquear automatizaciones de inventario y "
                        "revisar anomalías críticas."
                    ),
                    priority="CRITICA",
                )
            )

        if purchase_plan.get("requiere_compra"):
            actions.append(
                self._action(
                    action_type="GENERAR_ORDENES_COMPRA",
                    description=(
                        "Crear órdenes de compra en borrador para "
                        "medicamentos bajo mínimo."
                    ),
                    priority="ALTA",
                    executable=True,
                )
            )

        if recommendations.get("recomendaciones"):
            actions.append(
                self._action(
                    action_type="NOTIFICAR_RECOMENDACIONES",
                    description=(
                        "Enviar recomendaciones prioritarias al "
                        "responsable de inventario."
                    ),
                    priority="MEDIA",
                )
            )

        executed: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []

        for action in actions:
            if not action["ejecutable"]:
                blocked.append(
                    {
                        **action,
                        "motivo": (
                            "Acción informativa o requiere revisión "
                            "humana."
                        ),
                    }
                )
                continue

            if not autorizar_acciones:
                blocked.append(
                    {
                        **action,
                        "motivo": (
                            "Modo seguro activo; ejecución no "
                            "autorizada."
                        ),
                    }
                )
                continue

            if action["tipo"] == "GENERAR_ORDENES_COMPRA":
                executed.append(
                    {
                        **action,
                        "resultado": (
                            purchase_planner_service.ejecutar_plan(
                                session_id=sesion_id,
                                usuario_id=usuario_id,
                            )
                        ),
                    }
                )

        return {
            "fecha": datetime.now(timezone.utc).isoformat(),
            "modo": (
                "AUTORIZADO"
                if autorizar_acciones
                else "SEGURO"
            ),
            "estado": report.get("estado"),
            "puntaje_riesgo": report.get("puntaje_riesgo"),
            "acciones_planificadas": actions,
            "acciones_ejecutadas": executed,
            "acciones_bloqueadas": blocked,
            "reporte": report,
            "recomendaciones": recommendations,
            "anomalias": anomalies,
            "plan_compra": purchase_plan,
        }


autonomous_agent_service = AutonomousAgentService()
