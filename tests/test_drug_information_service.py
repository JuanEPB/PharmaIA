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


def test_drug_information_returns_local_fallback(monkeypatch) -> None:
    service = DrugInformationService()

    monkeypatch.setattr(
        service,
        "_find_rxnorm",
        lambda name: {
            "rxcui": None,
            "nombre_normalizado": name,
            "fuente": "RxNorm/NLM",
        },
    )
    monkeypatch.setattr(service, "_find_label", lambda name: {})
    monkeypatch.setattr(
        service,
        "_find_local_medicine",
        lambda name: {
            "id": 7,
            "nombre": "GENOPRAZOL 20 MG CAP",
            "lote": "GNP-01",
            "caducidad": "2027-10-01",
            "stock": 4,
            "stock_minimo": 5,
            "precio": 89.5,
            "proveedor_id": 1,
            "categoria_id": 2,
        },
    )

    result = service.consultar("genoprazol")

    assert result["medicamento_local"]["nombre"] == "GENOPRAZOL 20 MG CAP"
    assert "base local" in result["mensaje_usuario"]
    assert result["recomendaciones_seguras"][0].startswith(
        "El producto esta en bajo stock"
    )


def test_drug_information_returns_clear_message_without_matches(monkeypatch) -> None:
    service = DrugInformationService()

    monkeypatch.setattr(service, "_find_rxnorm", lambda name: {})
    monkeypatch.setattr(service, "_find_label", lambda name: {})
    monkeypatch.setattr(service, "_find_local_medicine", lambda name: None)

    result = service.consultar("medicamento raro")

    assert result["medicamento_local"] is None
    assert "No encontre coincidencias" in result["mensaje_usuario"]
    assert result["recomendaciones_seguras"]
