from app.database.migration_runner import split_sql_statements


def test_split_sql_statements_keeps_semicolon_inside_text() -> None:
    sql = """
    CREATE TABLE demo (mensaje TEXT);
    INSERT INTO demo (mensaje) VALUES ('hola; mundo');
    """

    statements = split_sql_statements(sql)

    assert len(statements) == 2
    assert "CREATE TABLE demo" in statements[0]
    assert "'hola; mundo'" in statements[1]
