from __future__ import annotations

import re
from datetime import date
from typing import Any


class VisionLabelService:
    DATE_PATTERNS = (
        r"\b(?P<day>\d{1,2})[/-](?P<month>\d{1,2})[/-](?P<year>\d{2,4})\b",
        r"\b(?P<year>\d{4})[/-](?P<month>\d{1,2})[/-](?P<day>\d{1,2})\b",
    )

    @staticmethod
    def _normalize_year(value: str) -> int:
        year = int(value)
        if year < 100:
            return 2000 + year
        return year

    @classmethod
    def _parse_date(cls, text: str) -> str | None:
        for pattern in cls.DATE_PATTERNS:
            match = re.search(pattern, text)
            if not match:
                continue

            try:
                parsed = date(
                    cls._normalize_year(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                )
            except ValueError:
                continue

            return parsed.isoformat()

        return None

    @staticmethod
    def _extract_lot(text: str) -> str | None:
        match = re.search(
            r"\b(?:lote|lot|batch)\s*[:#-]?\s*([A-Z0-9-]{3,30})",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return match.group(1).strip().upper()

    @staticmethod
    def _extract_name(text: str) -> str | None:
        lines = [
            line.strip(" .,:;-")
            for line in text.splitlines()
            if line.strip()
        ]

        ignored = {
            "lote",
            "caducidad",
            "vence",
            "fecha",
        }

        for line in lines:
            normalized = line.lower()
            if any(word in normalized for word in ignored):
                continue
            if len(line) < 3:
                continue
            return line

        return None

    def analizar_etiqueta(
        self,
        texto: str,
        origen: str | None = None,
    ) -> dict[str, Any]:
        clean_text = str(texto or "").strip()

        if not clean_text:
            raise ValueError(
                "Debes proporcionar texto reconocido de la etiqueta."
            )

        lot = self._extract_lot(clean_text)
        expiration = self._parse_date(clean_text)
        name = self._extract_name(clean_text)

        missing = []
        if not name:
            missing.append("nombre")
        if not lot:
            missing.append("lote")
        if not expiration:
            missing.append("caducidad")

        confidence = round(
            (
                int(bool(name))
                + int(bool(lot))
                + int(bool(expiration))
            )
            / 3,
            2,
        )

        return {
            "origen": origen,
            "texto_analizado": clean_text,
            "medicamento_detectado": name,
            "lote_detectado": lot,
            "caducidad_detectada": expiration,
            "confianza": confidence,
            "requiere_revision": bool(missing),
            "campos_faltantes": missing,
            "sugerencia": (
                "Validar los campos detectados antes de registrar "
                "el medicamento en inventario."
                if not missing
                else (
                    "La etiqueta requiere revisión manual porque "
                    "faltan campos clave."
                )
            ),
        }


vision_label_service = VisionLabelService()
