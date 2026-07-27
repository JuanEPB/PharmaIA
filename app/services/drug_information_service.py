from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import urlopen


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
        data = self._get_json(url)
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

    def consultar(self, medicine_name: str) -> dict:
        clean_name = " ".join(str(medicine_name or "").split())

        if not clean_name:
            raise ValueError("El nombre del medicamento es requerido.")

        rxnorm = {}
        label = {}
        errors: list[str] = []

        try:
            rxnorm = self._find_rxnorm(clean_name)
        except Exception as exc:
            errors.append(f"RxNorm no disponible: {exc}")

        try:
            label = self._find_label(
                rxnorm.get("nombre_normalizado") or clean_name
            )
        except Exception as exc:
            errors.append(f"openFDA no disponible: {exc}")

        return {
            "consulta": clean_name,
            "normalizacion": rxnorm,
            "informacion": label,
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
