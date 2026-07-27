from __future__ import annotations

from pathlib import Path

from app.database.connection import get_connection


PROJECT_DIR = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = PROJECT_DIR / "migrations"


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    previous = ""

    for character in sql:
        if character == "'" and previous != "\\" and not in_double_quote:
            in_single_quote = not in_single_quote

        elif character == '"' and previous != "\\" and not in_single_quote:
            in_double_quote = not in_double_quote

        if character == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()

            if statement:
                statements.append(statement)

            current = []
        else:
            current.append(character)

        previous = character

    statement = "".join(current).strip()

    if statement:
        statements.append(statement)

    return statements


def ensure_migrations_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def get_applied_migrations(cursor) -> set[str]:
    cursor.execute(
        "SELECT filename FROM schema_migrations"
    )

    rows = cursor.fetchall()

    return {
        row[0]
        for row in rows
    }


def run_pending_migrations(
    migrations_dir: Path = MIGRATIONS_DIR,
) -> list[str]:
    applied_now: list[str] = []

    migration_files = sorted(
        migrations_dir.glob("*.sql")
    )

    with get_connection() as connection:
        cursor = connection.cursor()

        try:
            ensure_migrations_table(cursor)
            applied = get_applied_migrations(cursor)

            for migration_file in migration_files:
                filename = migration_file.name

                if filename in applied:
                    continue

                sql = migration_file.read_text(
                    encoding="utf-8"
                )

                for statement in split_sql_statements(sql):
                    cursor.execute(statement)

                cursor.execute(
                    """
                    INSERT INTO schema_migrations (filename)
                    VALUES (%s)
                    """,
                    (filename,),
                )

                applied_now.append(filename)

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()

    return applied_now


if __name__ == "__main__":
    migrations = run_pending_migrations()

    if migrations:
        print("Migraciones aplicadas:")

        for migration in migrations:
            print(f"- {migration}")
    else:
        print("No hay migraciones pendientes.")
