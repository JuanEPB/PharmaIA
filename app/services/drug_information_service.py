from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from app.services.inventory_service import inventory_service


class DrugInformationService:
    RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"

    @staticmethod
    def _get_json(url: str, timeout: int = 6) -> dict:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _find_rxnorm(self, medicine_name: str) -> dict:
        url = (
            f"{self.RXNORM_BASE_URL}/drugs.json?"
            f"name={quote(medicine_name)}"
        )
        data = self._get_json(url)
        groups = data.get("drugGroup", {}).get("conceptGroup", [])

        for group in groups:
            concepts = group.get("conceptProperties") or []
            if concepts:
                concept = concepts[0]
                return {
                    "rxcui": concept.get("rxcui"),
                    "nombre_normalizado": concept.get("name"),
                    "tipo": concept.get("tty"),
                    "fuente": "RxNorm/NLM",
                }

        return {
            "rxcui": None,
            "nombre_normalizado": medicine_name,
            "tipo": None,
            "fuente": "RxNorm/NLM",
        }

    def _find_label(self, medicine_name: str) -> dict:
        query = quote(f'openfda.brand_name:"{medicine_name}"')
        url = f"{self.OPENFDA_LABEL_URL}?search={query}&limit=1"
        try:
            data = self._get_json(url)
        except HTTPError as exc:
            if exc.code == 404:
                return {}
            raise

        results = data.get("results") or []

        if not results:
            return {}

        label = results[0]
        return {
            "indicaciones": (label.get("indications_and_usage") or [])[:1],
            "advertencias": (label.get("warnings") or label.get("warnings_and_cautions") or [])[:1],
            "no_usar_en": (label.get("do_not_use") or [])[:1],
            "fuente": "openFDA",
        }

    @staticmethod
    def _clean_local_medicine(record: dict | None) -> dict | None:
        if not record:
            return None

        return {
            "id": record.get("id"),
            "nombre": record.get("nombre"),
            "lote": record.get("lote"),
            "caducidad": str(record.get("caducidad") or ""),
            "stock": record.get("stock"),
            "stock_minimo": record.get("stock_minimo"),
            "precio": float(record.get("precio") or 0),
            "proveedor_id": record.get("proveedorId"),
            "categoria_id": record.get("categoriaId"),
        }

    def _find_local_medicine(self, medicine_name: str) -> dict | None:
        results = inventory_service.buscar(medicine_name)
        if not results:
            return None

        return self._clean_local_medicine(results[0])

    @staticmethod
    def _build_safe_recommendations(local_medicine: dict | None) -> list[str]:
        recommendations = [
            "Verifica disponibilidad, lote, caducidad y precio antes de vender.",
            "No uses esta consulta para diagnosticar, recetar o cambiar dosis.",
            "Si el cliente pregunta por uso medico, deriva con un profesional de salud.",
        ]

        if local_medicine:
            stock = int(local_medicine.get("stock") or 0)
            stock_minimo = int(local_medicine.get("stock_minimo") or 0)
            if stock <= 0:
                recommendations.insert(0, "El producto aparece agotado en la base local.")
            elif stock <= stock_minimo:
                recommendations.insert(0, "El producto esta en bajo stock; considera reposicion.")
            else:
                recommendations.insert(0, "El producto aparece disponible en inventario local.")

        return recommendations

    def consultar(self, medicine_name: str) -> dict:
        clean_name = " ".join(str(medicine_name or "").split())

        if not clean_name:
            raise ValueError("El nombre del medicamento es requerido.")

        rxnorm = {}
        label = {}
        local_medicine = None
        errors: list[str] = []

        try:
            rxnorm = self._find_rxnorm(clean_name)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append(f"RxNorm no disponible: {exc}")

        try:
            label = self._find_label(
                rxnorm.get("nombre_normalizado") or clean_name
            )
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append(f"openFDA no disponible: {exc}")

        try:
            local_medicine = self._find_local_medicine(clean_name)
        except Exception as exc:
            errors.append(f"Base local no disponible: {exc}")

        if label:
            user_message = (
                "Encontre informacion externa de apoyo y la combine con "
                "validaciones operativas de farmacia."
            )
        elif local_medicine:
            user_message = (
                "No encontre etiqueta externa para este nombre, pero si datos "
                "en la base local de pharmacontrol."
            )
        else:
            user_message = (
                "No encontre coincidencias externas ni locales. Revisa el nombre, "
                "abreviaturas o presentacion del medicamento."
            )

        return {
            "consulta": clean_name,
            "normalizacion": rxnorm,
            "informacion": label,
            "medicamento_local": local_medicine,
            "recomendaciones_seguras": self._build_safe_recommendations(
                local_medicine
            ),
            "mensaje_usuario": user_message,
            "errores": errors,
            "aviso_medico": (
                "Informacion solo de apoyo. No sustituye diagnostico, "
                "receta ni indicacion de un profesional de salud."
            ),
            "fuentes": [
                "RxNorm/National Library of Medicine",
                "openFDA/Food and Drug Administration",
            ],
        }


drug_information_service = DrugInformationService()
