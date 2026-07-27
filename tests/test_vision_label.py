from app.services.vision_label_service import VisionLabelService


def test_label_analysis_extracts_medicine_lot_and_expiration() -> None:
    service = VisionLabelService()

    result = service.analizar_etiqueta(
        texto=(
            "Paracetamol 500 mg\n"
            "Lote: PAR-2026\n"
            "Caducidad 15/08/2027"
        ),
        origen="foto-etiqueta.jpg",
    )

    assert result["medicamento_detectado"] == "Paracetamol 500 mg"
    assert result["lote_detectado"] == "PAR-2026"
    assert result["caducidad_detectada"] == "2027-08-15"
    assert result["confianza"] == 1
    assert result["requiere_revision"] is False


def test_label_analysis_marks_missing_fields() -> None:
    service = VisionLabelService()

    result = service.analizar_etiqueta(
        texto="Ibuprofeno 400 mg"
    )

    assert result["medicamento_detectado"] == "Ibuprofeno 400 mg"
    assert result["requiere_revision"] is True
    assert "lote" in result["campos_faltantes"]
    assert "caducidad" in result["campos_faltantes"]
