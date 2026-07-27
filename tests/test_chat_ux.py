from app.routes import build_welcome_response


def test_welcome_response_includes_options() -> None:
    result = build_welcome_response(
        "sesion-test"
    )

    assert result["sesion_id"] == "sesion-test"
    assert "Hola" in result["respuesta"]
    assert result["contexto"]["tipo"] == "BIENVENIDA"
    assert len(result["opciones"]) >= 5
    assert {
        "dashboard_predictivo",
        "plan_compras",
        "alertas",
        "agotamiento",
        "reporte",
    }.issubset(
        {
            option["id"]
            for option in result["opciones"]
        }
    )
