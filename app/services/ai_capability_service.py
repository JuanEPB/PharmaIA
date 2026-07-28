from __future__ import annotations

from typing import Any

from app.core.permissions import AuthenticatedUser


class AiCapabilityService:
    CAPABILITIES: list[dict[str, Any]] = [
        {
            "id": "chat_inventario",
            "nombre": "Chat de inventario",
            "estado": "funciona",
            "descripcion": (
                "Responde preguntas sobre stock, caducidad, precios, "
                "categorias, proveedores y resumen del inventario."
            ),
            "permiso": "ai:read",
            "ruta": "/chat",
        },
        {
            "id": "memoria_conversacional",
            "nombre": "Memoria por sesion",
            "estado": "funciona",
            "descripcion": (
                "Mantiene contexto para preguntas de seguimiento dentro "
                "de la misma sesion."
            ),
            "permiso": "ai:read",
            "ruta": "/chat/context/{sesion_id}",
        },
        {
            "id": "plan_compras",
            "nombre": "Planeador de compras",
            "estado": "funciona",
            "descripcion": (
                "Detecta medicamentos bajo minimo y genera ordenes de "
                "compra en borrador con confirmacion."
            ),
            "permiso": "ai:execute",
            "ruta": "/chat",
        },
        {
            "id": "prediccion_agotamiento",
            "nombre": "Prediccion de agotamiento",
            "estado": "funciona",
            "descripcion": (
                "Calcula riesgo y cobertura estimada de medicamentos "
                "segun stock y movimientos."
            ),
            "permiso": "ai:read",
            "ruta": "/predicciones/agotamiento",
        },
        {
            "id": "recomendaciones",
            "nombre": "Recomendaciones IA",
            "estado": "funciona",
            "descripcion": (
                "Prioriza riesgos por caducidad, bajo stock, "
                "agotamiento, compras y anomalias."
            ),
            "permiso": "ai:read",
            "ruta": "/recomendaciones",
        },
        {
            "id": "agente_autonomo",
            "nombre": "Agente autonomo",
            "estado": "funciona_modo_seguro",
            "descripcion": (
                "Planifica acciones. Solo ejecuta operaciones si el "
                "usuario tiene permiso y autoriza la ejecucion."
            ),
            "permiso": "ai:execute",
            "ruta": "/agente/autonomo/ciclo",
        },
        {
            "id": "aprendizaje_feedback",
            "nombre": "Aprendizaje por feedback",
            "estado": "parcial",
            "descripcion": (
                "Registra feedback del usuario. Falta usarlo en un "
                "flujo formal de reentrenamiento aprobado."
            ),
            "permiso": "learning:review",
            "ruta": "/aprendizaje/eventos",
        },
        {
            "id": "notificaciones_ia",
            "nombre": "Notificaciones inteligentes",
            "estado": "pendiente",
            "descripcion": (
                "Falta generar avisos automaticos para la app cuando "
                "haya caducidad, bajo stock o agotamiento probable."
            ),
            "permiso": "ai:read",
            "ruta": None,
        },
        {
            "id": "dashboard_app",
            "nombre": "Dashboard visual para app",
            "estado": "pendiente",
            "descripcion": (
                "Falta construir pantallas para mostrar alertas, "
                "predicciones, compras sugeridas y acciones IA."
            ),
            "permiso": "inventory:read",
            "ruta": None,
        },
    ]

    NEXT_STEPS = [
        "Construir dashboard visual en la app.",
        "Agregar notificaciones inteligentes por riesgo.",
        "Crear login real con JWT y usuarios de base de datos.",
        "Mostrar historial de decisiones IA en la app.",
        "Agregar explicaciones detalladas en cada recomendacion.",
        "Formalizar reentrenamiento con feedback aprobado.",
    ]

    def obtener_capacidades(
        self,
        user: AuthenticatedUser,
    ) -> dict[str, Any]:
        capabilities = []

        for capability in self.CAPABILITIES:
            permission = capability.get("permiso")
            enabled = not permission or user.can(str(permission))

            capabilities.append(
                {
                    **capability,
                    "habilitado_para_usuario": enabled,
                }
            )

        return {
            "usuario": {
                "id": user.user_id,
                "rol": user.role,
                "permisos": sorted(user.permissions),
            },
            "capacidades": capabilities,
            "siguientes_mejoras": self.NEXT_STEPS,
            "reglas_seguridad": [
                "La IA no debe ejecutar compras sin confirmacion.",
                "La IA no debe modificar stock sin permiso de escritura.",
                "La revision de aprendizaje requiere rol supervisor o admin.",
                "Las rutas protegidas requieren API key cuando la auth esta activa.",
            ],
        }


ai_capability_service = AiCapabilityService()
