from app.services.drug_information_service import DrugInformationService


def test_drug_information_returns_medical_disclaimer(monkeypatch) -> None:
    service = DrugInformationService()

    monkeypatch.setattr(
        service,
        "_find_rxnorm",
        lambda name: {
            "rxcui": "123",
            "nombre_normalizado": name,
            "fuente": "RxNorm/NLM",
        },
    )
    monkeypatch.setattr(
        service,
        "_find_label",
        lambda name: {
            "indicaciones": ["Uso de apoyo"],
            "fuente": "openFDA",
        },
    )

    result = service.consultar("Paracetamol")

    assert result["consulta"] == "Paracetamol"
    assert "No sustituye" in result["aviso_medico"]
    assert "RxNorm" in result["fuentes"][0]
