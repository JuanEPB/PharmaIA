from __future__ import annotations

from typing import Any

from app.repositories.app_profile_repository import app_profile_repository


class AppProfileService:
    def obtener_perfil(self) -> dict[str, Any]:
        empresa = app_profile_repository.obtener_empresa_activa()
        farmacia = app_profile_repository.obtener_farmacia_activa()
        metricas = app_profile_repository.obtener_metricas_operativas()
        metricas_ia = app_profile_repository.obtener_metricas_ia()

        return {
            "app": {
                "nombre": "Pharma Neural Assistant",
                "version": "2.0.0",
                "etapa": "Version 2",
                "estado": "activo",
            },
            "empresa": empresa,
            "farmacia": farmacia,
            "modulos": [
                "inventario",
                "movimientos",
                "compras",
                "reportes",
                "dashboard_predictivo",
                "prediccion_agotamiento",
                "recomendaciones",
                "anomalias",
                "vision",
                "voz",
                "chat_ia",
                "aprendizaje_ia",
                "acciones_conversacionales",
            ],
            "metricas": metricas,
            "ia": {
                "puede_ver": [
                    "resumen de inventario",
                    "medicamentos agotados y bajo stock",
                    "caducidades y productos por caducar",
                    "movimientos de inventario",
                    "ordenes de compra sugeridas",
                    "predicciones de agotamiento",
                    "anomalias del inventario",
                    "memoria conversacional por sesion",
                    "feedback pendiente de aprendizaje",
                    "acciones pendientes y ejecutadas",
                ],
                "metricas": metricas_ia,
            },
            "pendientes_v2": [
                "login y roles JWT",
                "frontend dashboard",
                "exportacion PDF/Excel",
                "normalizacion de nombres de columnas",
                "separacion de contacto de proveedores",
                "logging de produccion",
                "Docker y despliegue",
            ],
        }


app_profile_service = AppProfileService()
