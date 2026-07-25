from __future__ import annotations

import math
import statistics
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.repositories.depletion_prediction_repository import (
    depletion_prediction_repository,
)


class DepletionPredictionService:
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
    def normalize(value: Any) -> str:
        text = str(value or "").strip().lower()
        text = unicodedata.normalize("NFD", text)

        return "".join(
            character
            for character in text
            if unicodedata.category(character) != "Mn"
        )

    @staticmethod
    def _risk_level(
        coverage_days: float | None,
        stock: int,
        configuration: dict[str, Any],
    ) -> str:
        if stock <= 0:
            return "AGOTADO"

        if coverage_days is None:
            return "SIN_DATOS"

        critical = int(
            configuration.get("riesgo_critico_dias") or 7
        )
        high = int(
            configuration.get("riesgo_alto_dias") or 14
        )
        medium = int(
            configuration.get("riesgo_medio_dias") or 30
        )

        if coverage_days <= critical:
            return "CRITICO"

        if coverage_days <= high:
            return "ALTO"

        if coverage_days <= medium:
            return "MEDIO"

        return "BAJO"

    @staticmethod
    def _confidence(
        total_movements: int,
        units_consumed: int,
        variation_coefficient: float | None,
    ) -> str:
        if total_movements < 3 or units_consumed <= 0:
            return "BAJA"

        if variation_coefficient is None:
            return "MEDIA"

        if total_movements >= 10 and variation_coefficient <= 0.5:
            return "ALTA"

        if total_movements >= 5 and variation_coefficient <= 1:
            return "MEDIA"

        return "BAJA"

    @staticmethod
    def _daily_statistics(
        daily_rows: list[dict[str, Any]],
        history_days: int,
    ) -> dict[str, Any]:
        values_by_day = {
            str(row.get("fecha")): float(row.get("unidades") or 0)
            for row in daily_rows
        }

        today = date.today()

        complete_series = []

        for offset in range(history_days):
            current_day = today - timedelta(days=offset)
            complete_series.append(
                values_by_day.get(
                    current_day.isoformat(),
                    values_by_day.get(
                        str(current_day),
                        0.0,
                    ),
                )
            )

        complete_series.reverse()

        average = (
            statistics.fmean(complete_series)
            if complete_series
            else 0.0
        )

        deviation = (
            statistics.pstdev(complete_series)
            if len(complete_series) > 1
            else 0.0
        )

        variation_coefficient = (
            deviation / average
            if average > 0
            else None
        )

        active_values = [
            value
            for value in complete_series
            if value > 0
        ]

        active_day_average = (
            statistics.fmean(active_values)
            if active_values
            else 0.0
        )

        return {
            "promedio_diario": average,
            "desviacion_diaria": deviation,
            "coeficiente_variacion": variation_coefficient,
            "promedio_dia_con_consumo": active_day_average,
            "serie_diaria": complete_series,
        }

    def resolver_medicamento(
        self,
        nombre: str,
    ) -> dict[str, Any]:
        matches = (
            depletion_prediction_repository
            .buscar_medicamentos(nombre)
        )

        if not matches:
            raise ValueError(
                f"No encontré el medicamento '{nombre}'."
            )

        normalized_name = self.normalize(nombre)

        exact_matches = [
            medicine
            for medicine in matches
            if self.normalize(medicine.get("nombre"))
            == normalized_name
        ]

        if len(exact_matches) == 1:
            return exact_matches[0]

        if len(matches) == 1:
            return matches[0]

        options = ", ".join(
            (
                f"{medicine.get('nombre')} "
                f"(lote {medicine.get('lote')})"
            )
            for medicine in matches[:6]
        )

        raise ValueError(
            "Encontré varios registros. Indica el lote o el ID: "
            + options
        )

    def predecir_medicamento(
        self,
        medicamento_id: int,
    ) -> dict[str, Any]:
        configuration = (
            depletion_prediction_repository
            .obtener_configuracion()
        )

        medicine = (
            depletion_prediction_repository
            .obtener_medicamento(medicamento_id)
        )

        if not medicine:
            raise ValueError(
                "El medicamento indicado no existe."
            )

        history_days = max(
            7,
            int(configuration.get("dias_historial") or 30),
        )

        include_expiration = bool(
            configuration.get(
                "incluir_caducidad_como_consumo",
                0,
            )
        )

        historical = (
            depletion_prediction_repository
            .obtener_consumo_historico(
                medicamento_id=medicamento_id,
                dias_historial=history_days,
                incluir_caducidad=include_expiration,
            )
        )

        daily_rows = (
            depletion_prediction_repository
            .obtener_consumo_diario(
                medicamento_id=medicamento_id,
                dias_historial=history_days,
                incluir_caducidad=include_expiration,
            )
        )

        statistics_result = self._daily_statistics(
            daily_rows=daily_rows,
            history_days=history_days,
        )

        average_daily_consumption = float(
            statistics_result["promedio_diario"]
        )

        stock = int(medicine.get("stock") or 0)
        stock_minimum = int(
            medicine.get("stock_minimo") or 0
        )

        coverage_days: float | None = None
        estimated_depletion_date: date | None = None

        if stock <= 0:
            coverage_days = 0.0
            estimated_depletion_date = date.today()

        elif average_daily_consumption > 0:
            coverage_days = stock / average_daily_consumption
            estimated_depletion_date = (
                date.today()
                + timedelta(
                    days=max(
                        0,
                        math.ceil(coverage_days),
                    )
                )
            )

        safety_days = int(
            configuration.get("dias_stock_seguridad") or 7
        )
        target_days = int(
            configuration.get("dias_cobertura_objetivo") or 30
        )

        target_stock = math.ceil(
            average_daily_consumption
            * (
                target_days
                + safety_days
            )
        )

        recommended_quantity = max(
            target_stock - stock,
            0,
        )

        if average_daily_consumption <= 0:
            recommended_quantity = max(
                (stock_minimum * 2) - stock,
                0,
            )

        variation_coefficient = (
            statistics_result["coeficiente_variacion"]
        )

        total_movements = int(
            historical.get("total_movimientos") or 0
        )

        units_consumed = int(
            historical.get("unidades_consumidas") or 0
        )

        risk = self._risk_level(
            coverage_days=coverage_days,
            stock=stock,
            configuration=configuration,
        )

        confidence = self._confidence(
            total_movements=total_movements,
            units_consumed=units_consumed,
            variation_coefficient=variation_coefficient,
        )

        return self.serialize(
            {
                "medicamento": {
                    "id": int(medicine["id"]),
                    "nombre": medicine.get("nombre"),
                    "lote": medicine.get("lote"),
                    "caducidad": medicine.get("caducidad"),
                },
                "stock_actual": stock,
                "stock_minimo": stock_minimum,
                "periodo_analizado_dias": history_days,
                "unidades_consumidas": units_consumed,
                "total_movimientos_salida": total_movements,
                "dias_con_consumo": int(
                    historical.get("dias_con_movimiento") or 0
                ),
                "consumo_promedio_diario": round(
                    average_daily_consumption,
                    2,
                ),
                "promedio_por_dia_con_consumo": round(
                    float(
                        statistics_result[
                            "promedio_dia_con_consumo"
                        ]
                    ),
                    2,
                ),
                "desviacion_diaria": round(
                    float(
                        statistics_result["desviacion_diaria"]
                    ),
                    2,
                ),
                "coeficiente_variacion": (
                    round(
                        float(variation_coefficient),
                        2,
                    )
                    if variation_coefficient is not None
                    else None
                ),
                "cobertura_estimada_dias": (
                    round(coverage_days, 1)
                    if coverage_days is not None
                    else None
                ),
                "fecha_probable_agotamiento": (
                    estimated_depletion_date
                ),
                "nivel_riesgo": risk,
                "confianza_prediccion": confidence,
                "cantidad_compra_recomendada": int(
                    recommended_quantity
                ),
                "cobertura_objetivo_dias": target_days,
                "stock_seguridad_dias": safety_days,
                "tiene_datos_suficientes": (
                    total_movements >= 3
                    and units_consumed > 0
                ),
            }
        )

    def predecir_por_nombre(
        self,
        nombre: str,
    ) -> dict[str, Any]:
        medicine = self.resolver_medicamento(nombre)

        return self.predecir_medicamento(
            int(medicine["id"])
        )

    def predecir_inventario(
        self,
        solo_riesgo: bool = True,
    ) -> dict[str, Any]:
        medicines = (
            depletion_prediction_repository
            .obtener_candidatos_prediccion()
        )

        predictions: list[dict[str, Any]] = []

        for medicine in medicines:
            prediction = self.predecir_medicamento(
                int(medicine["id"])
            )

            if solo_riesgo and prediction["nivel_riesgo"] not in {
                "AGOTADO",
                "CRITICO",
                "ALTO",
                "MEDIO",
            }:
                continue

            predictions.append(prediction)

        risk_order = {
            "AGOTADO": 0,
            "CRITICO": 1,
            "ALTO": 2,
            "MEDIO": 3,
            "BAJO": 4,
            "SIN_DATOS": 5,
        }

        predictions.sort(
            key=lambda item: (
                risk_order.get(
                    item.get("nivel_riesgo"),
                    99,
                ),
                item.get("cobertura_estimada_dias")
                if item.get("cobertura_estimada_dias") is not None
                else float("inf"),
            )
        )

        return {
            "total": len(predictions),
            "predicciones": predictions,
        }

    def construir_respuesta_chat(
        self,
        prediction: dict[str, Any],
    ) -> str:
        medicine = prediction["medicamento"]
        coverage = prediction["cobertura_estimada_dias"]
        depletion_date = prediction["fecha_probable_agotamiento"]

        if coverage is None:
            return (
                f"{medicine['nombre']} — lote {medicine['lote']}. "
                f"Stock actual: {prediction['stock_actual']} unidades. "
                "Aún no hay suficientes salidas registradas para "
                "calcular una fecha confiable de agotamiento. "
                f"Cantidad de compra sugerida con stock mínimo: "
                f"{prediction['cantidad_compra_recomendada']} unidades."
            )

        return (
            f"{medicine['nombre']} — lote {medicine['lote']}. "
            f"Stock actual: {prediction['stock_actual']} unidades. "
            f"Consumo promedio: "
            f"{prediction['consumo_promedio_diario']} unidades diarias. "
            f"Cobertura estimada: {coverage} días. "
            f"Fecha probable de agotamiento: {depletion_date}. "
            f"Nivel de riesgo: {prediction['nivel_riesgo']}. "
            f"Confianza de la predicción: "
            f"{prediction['confianza_prediccion']}. "
            f"Compra recomendada: "
            f"{prediction['cantidad_compra_recomendada']} unidades."
        )


depletion_prediction_service = DepletionPredictionService()
