from __future__ import annotations

import importlib
import os
from contextlib import contextmanager
from typing import Any, Generator


class DatabaseConnectionError(RuntimeError):
    pass


def _try_project_connection() -> Any | None:
    """
    Busca una función get_connection() existente dentro del proyecto.
    """

    candidates = (
        ("app.database.connection", "get_connection"),
        ("app.database.database", "get_connection"),
        ("app.database.db", "get_connection"),
        ("app.database", "get_connection"),
        ("app.db.connection", "get_connection"),
        ("app.db", "get_connection"),
    )

    for module_name, function_name in candidates:
        try:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name, None)

            if callable(function):
                return function()

        except (ImportError, AttributeError):
            continue
        except Exception:
            continue

    return None


def _create_mysql_connection() -> Any:
    try:
        import mysql.connector
    except ImportError as exc:
        raise DatabaseConnectionError(
            "No se encontró mysql-connector-python. "
            "Instálalo con: pip install mysql-connector-python"
        ) from exc

    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv(
        "DB_NAME",
        os.getenv("DB_DATABASE", "pharmacontrol"),
    )

    try:
        return mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
        )

    except Exception as exc:
        raise DatabaseConnectionError(
            "No fue posible conectarse a MySQL. "
            "Verifica DB_HOST, DB_PORT, DB_USER, DB_PASSWORD y DB_NAME. "
            f"Detalle: {exc}"
        ) from exc


def create_connection() -> Any:
    project_connection = _try_project_connection()

    if project_connection is not None:
        return project_connection

    return _create_mysql_connection()


@contextmanager
def database_connection() -> Generator[Any, None, None]:
    connection = create_connection()

    try:
        yield connection
    finally:
        try:
            connection.close()
        except Exception:
            pass


@contextmanager
def dictionary_cursor(
    connection: Any,
) -> Generator[Any, None, None]:
    cursor = None

    try:
        try:
            cursor = connection.cursor(dictionary=True)
        except TypeError:
            cursor = connection.cursor()

        yield cursor

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
