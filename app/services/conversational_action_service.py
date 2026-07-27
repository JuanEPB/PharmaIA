from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.conversational_action_repository import (
    conversational_action_repository,
)
from app.services.conversation_memory import conversation_memory
from app.services.inventory_movement_service import (
    inventory_movement_service,
)
from app.services.purchase_planner_service import purchase_planner_service


class ConversationalActionService:
    """
    Interpreta instrucciones operativas escritas en lenguaje natural.

    Por seguridad, ninguna acción de escritura se ejecuta inmediatamente.
    Primero se almacena como acción pendiente y se solicita confirmación.
    """

    CONFIRMATION_WORDS = {
        "confirmar",
        "confirmo",
        "si confirmar",
        "sí confirmar",
        "si hazlo",
        "sí hazlo",
        "hazlo",
        "aceptar",
        "ejecutar",
    }

    CANCELLATION_WORDS = {
        "cancelar",
        "cancela",
        "no",
        "no cancelar",
        "olvidalo",
        "olvídalo",
        "detener",
    }

    @staticmethod
    def normalize(value: Any) -> str:
        text = str(value or "").strip().lower()
        text = unicodedata.normalize("NFD", text)

        text = "".join(
            character
            for character in text
            if unicodedata.category(character) != "Mn"
        )
        text = re.sub(r"[^a-z0-9ñ\s-]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

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

    def _is_confirmation(self, message: str) -> bool:
        normalized = self.normalize(message)
        return normalized in {
            self.normalize(word)
            for word in self.CONFIRMATION_WORDS
        }

    def _is_cancellation(self, message: str) -> bool:
        normalized = self.normalize(message)
        return normalized in {
            self.normalize(word)
            for word in self.CANCELLATION_WORDS
        }

    def _parse_stock_action(
        self,
        message: str,
    ) -> dict[str, Any] | None:
        normalized = self.normalize(message)

        entry_pattern = re.compile(
            r"^(?:agrega|agregar|anade|anadir|suma|sumar|ingresa|"
            r"ingresar|registra|registrar)\s+"
            r"(?P<cantidad>\d+)\s*"
            r"(?:cajas?|unidades?|piezas?)?\s+"
            r"(?:de\s+)?(?P<medicamento>.+?)"
            r"(?:\s+por\s+(?P<motivo>.+))?$",
            flags=re.IGNORECASE,
        )

        exit_pattern = re.compile(
            r"^(?:descuenta|descontar|resta|restar|retira|retirar|"
            r"vende|vender|salida\s+de)\s+"
            r"(?P<cantidad>\d+)\s*"
            r"(?:cajas?|unidades?|piezas?)?\s+"
            r"(?:de\s+)?(?P<medicamento>.+?)"
            r"(?:\s+por\s+(?P<motivo>.+))?$",
            flags=re.IGNORECASE,
        )

        for movement_type, pattern in (
            ("ENTRADA", entry_pattern),
            ("SALIDA", exit_pattern),
        ):
            match = pattern.match(normalized)

            if not match:
                continue

            medicine = str(
                match.group("medicamento") or ""
            ).strip(" .,:;")

            reason = (
                str(match.group("motivo")).strip()
                if match.group("motivo")
                else (
                    "Entrada registrada mediante asistente"
                    if movement_type == "ENTRADA"
                    else "Salida registrada mediante asistente"
                )
            )

            return {
                "tipo_accion": "MOVIMIENTO_INVENTARIO",
                "tipo_movimiento": movement_type,
                "cantidad": int(match.group("cantidad")),
                "medicamento_consulta": medicine,
                "motivo": reason,
            }

        return None

    def _parse_purchase_order_action(
        self,
        message: str,
    ) -> dict[str, Any] | None:
        normalized = self.normalize(message)

        required_phrases = (
            "orden de compra",
            "medicamentos criticos",
        )

        if all(
            phrase in normalized
            for phrase in required_phrases
        ):
            return {
                "tipo_accion": "GENERAR_ORDEN_CRITICOS",
            }

        return None

    def _resolve_medicine(
        self,
        action: dict[str, Any],
    ) -> dict[str, Any]:
        query = str(
            action.get("medicamento_consulta") or ""
        ).strip()

        matches = (
            conversational_action_repository
            .buscar_medicamento_por_nombre(query)
        )

        if not matches:
            raise ValueError(
                f"No encontré un medicamento llamado '{query}'."
            )

        exact_matches = [
            medicine
            for medicine in matches
            if self.normalize(medicine.get("nombre"))
            == self.normalize(query)
        ]

        if len(exact_matches) == 1:
            return exact_matches[0]

        if len(matches) == 1:
            return matches[0]

        names = ", ".join(
            str(item.get("nombre"))
            for item in matches[:5]
        )

        raise ValueError(
            "La instrucción es ambigua. Encontré varias coincidencias: "
            f"{names}. Escribe el nombre exacto."
        )

    def _build_confirmation(
        self,
        action: dict[str, Any],
    ) -> dict[str, Any]:
        action_type = action["tipo_accion"]

        if action_type == "MOVIMIENTO_INVENTARIO":
            movement = action["tipo_movimiento"]
            verb = (
                "agregar"
                if movement == "ENTRADA"
                else "descontar"
            )

            return {
                "accion_detectada": True,
                "requiere_confirmacion": True,
                "ejecutada": False,
                "respuesta": (
                    f"Voy a {verb} {action['cantidad']} unidades de "
                    f"{action['medicamento_nombre']}. "
                    f"Stock actual: {action['stock_actual']}. "
                    f"Stock resultante: {action['stock_resultante']}. "
                    "Escribe «confirmar» para ejecutar o «cancelar»."
                ),
                "accion_pendiente": action,
            }

        return {
            "accion_detectada": True,
            "requiere_confirmacion": True,
            "ejecutada": False,
            "respuesta": (
                f"Encontré {action['total_medicamentos']} medicamentos "
                f"críticos y se generarán "
                f"{action['total_ordenes_estimadas']} órdenes de compra "
                "en estado BORRADOR, agrupadas por proveedor. "
                "Escribe «confirmar» para ejecutar o «cancelar»."
            ),
            "accion_pendiente": action,
        }

    def _prepare_action(
        self,
        action: dict[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        if action["tipo_accion"] == "MOVIMIENTO_INVENTARIO":
            medicine = self._resolve_medicine(action)

            current_stock = int(
                medicine.get("stock") or 0
            )

            resulting_stock = (
                inventory_movement_service.calculate_new_stock(
                    movement_type=action["tipo_movimiento"],
                    current_stock=current_stock,
                    quantity=int(action["cantidad"]),
                )
            )

            action.update(
                {
                    "medicamento_id": int(medicine["id"]),
                    "medicamento_nombre": str(
                        medicine["nombre"]
                    ),
                    "stock_actual": current_stock,
                    "stock_resultante": resulting_stock,
                }
            )

        elif action["tipo_accion"] == "GENERAR_ORDEN_CRITICOS":
            medicines = (
                conversational_action_repository
                .obtener_medicamentos_criticos()
            )

            if not medicines:
                return {
                    "accion_detectada": True,
                    "requiere_confirmacion": False,
                    "ejecutada": False,
                    "respuesta": (
                        "No hay medicamentos críticos que requieran "
                        "una orden de compra."
                    ),
                }

            provider_ids = {
                item.get("proveedor_id")
                for item in medicines
            }

            action.update(
                {
                    "total_medicamentos": len(medicines),
                    "total_ordenes_estimadas": len(provider_ids),
                }
            )

        conversation_memory.update(
            session_id,
            accion_pendiente=action,
        )

        return self._build_confirmation(action)

    def _execute_pending_action(
        self,
        session_id: str,
        pending: dict[str, Any],
        usuario_id: int | None,
    ) -> dict[str, Any]:
        action_type = pending.get("tipo_accion")

        if action_type == "CONFIRMAR_PLAN_COMPRA":
            return purchase_planner_service.ejecutar_plan(
                session_id=session_id,
                usuario_id=usuario_id,
            )

        if action_type == "MOVIMIENTO_INVENTARIO":
            result = inventory_movement_service.registrar_movimiento(
                medicamento_id=int(pending["medicamento_id"]),
                tipo=str(pending["tipo_movimiento"]),
                cantidad=int(pending["cantidad"]),
                motivo=str(pending.get("motivo") or ""),
                usuario_id=usuario_id,
            )

            conversation_memory.update(
                session_id,
                accion_pendiente={},
                ultima_accion=result,
            )

            movement = result.get("movimiento", {})

            return {
                "accion_detectada": True,
                "requiere_confirmacion": False,
                "ejecutada": True,
                "respuesta": (
                    "Inventario actualizado correctamente. "
                    f"{movement.get('medicamento')}: "
                    f"{movement.get('stock_anterior')} → "
                    f"{movement.get('stock_nuevo')} unidades."
                ),
                "resultado": self.serialize(result),
            }

        if action_type == "GENERAR_ORDEN_CRITICOS":
            orders = (
                conversational_action_repository
                .crear_ordenes_para_criticos(
                    usuario_id=usuario_id
                )
            )

            conversation_memory.update(
                session_id,
                accion_pendiente={},
                ultima_accion={
                    "ordenes": orders,
                },
            )

            total = sum(
                float(order.get("total_estimado") or 0)
                for order in orders
            )

            return {
                "accion_detectada": True,
                "requiere_confirmacion": False,
                "ejecutada": True,
                "respuesta": (
                    f"Se generaron {len(orders)} órdenes de compra "
                    f"en estado BORRADOR por un total estimado de "
                    f"${total:,.2f}."
                ),
                "resultado": {
                    "total_ordenes": len(orders),
                    "total_estimado": round(total, 2),
                    "ordenes": self.serialize(orders),
                },
            }

        raise ValueError(
            "La acción pendiente no es válida."
        )

    def process(
        self,
        message: str,
        session_id: str,
        usuario_id: int | None = None,
    ) -> dict[str, Any] | None:
        clean_message = str(message or "").strip()
        clean_session_id = str(session_id or "").strip()

        context = conversation_memory.get(clean_session_id)
        pending = context.get("accion_pendiente")

        if pending:
            if self._is_confirmation(clean_message):
                return self._execute_pending_action(
                    session_id=clean_session_id,
                    pending=pending,
                    usuario_id=usuario_id,
                )

            if self._is_cancellation(clean_message):
                if pending.get("tipo_accion") == "CONFIRMAR_PLAN_COMPRA":
                    return purchase_planner_service.cancelar_plan(
                        clean_session_id
                    )

                conversation_memory.update(
                    clean_session_id,
                    accion_pendiente={},
                )

                return {
                    "accion_detectada": True,
                    "requiere_confirmacion": False,
                    "ejecutada": False,
                    "respuesta": (
                        "La acción pendiente fue cancelada."
                    ),
                }

        action = (
            self._parse_stock_action(clean_message)
            or self._parse_purchase_order_action(clean_message)
        )

        if not action:
            return None

        return self._prepare_action(
            action=action,
            session_id=clean_session_id,
        )


conversational_action_service = ConversationalActionService()

