from unittest.mock import patch

from app.services.autonomous_agent_service import AutonomousAgentService


def test_autonomous_agent_safe_mode_blocks_execution() -> None:
    service = AutonomousAgentService()

    with patch(
        "app.services.autonomous_agent_service."
        "executive_report_service.generar_reporte",
        return_value={
            "estado": "CRITICO",
            "puntaje_riesgo": 90,
        },
    ), patch(
        "app.services.autonomous_agent_service."
        "recommendation_service.generar_recomendaciones",
        return_value={
            "recomendaciones": [
                {
                    "accion": "Comprar",
                }
            ]
        },
    ), patch(
        "app.services.autonomous_agent_service."
        "anomaly_detection_service.detectar_anomalias",
        return_value={
            "anomalias_criticas": 0,
        },
    ), patch(
        "app.services.autonomous_agent_service."
        "purchase_planner_service.generar_plan",
        return_value={
            "requiere_compra": True,
        },
    ):
        result = service.planificar_ciclo(
            autorizar_acciones=False
        )

    assert result["modo"] == "SEGURO"
    assert result["acciones_ejecutadas"] == []
    assert any(
        action["tipo"] == "GENERAR_ORDENES_COMPRA"
        for action in result["acciones_bloqueadas"]
    )


def test_autonomous_agent_plans_anomaly_review() -> None:
    service = AutonomousAgentService()

    with patch(
        "app.services.autonomous_agent_service."
        "executive_report_service.generar_reporte",
        return_value={
            "estado": "CRITICO",
            "puntaje_riesgo": 95,
        },
    ), patch(
        "app.services.autonomous_agent_service."
        "recommendation_service.generar_recomendaciones",
        return_value={
            "recomendaciones": [],
        },
    ), patch(
        "app.services.autonomous_agent_service."
        "anomaly_detection_service.detectar_anomalias",
        return_value={
            "anomalias_criticas": 2,
        },
    ), patch(
        "app.services.autonomous_agent_service."
        "purchase_planner_service.generar_plan",
        return_value={
            "requiere_compra": False,
        },
    ):
        result = service.planificar_ciclo()

    assert result["acciones_planificadas"][0]["tipo"] == "REVISAR_ANOMALIAS"
    assert result["acciones_planificadas"][0]["prioridad"] == "CRITICA"
