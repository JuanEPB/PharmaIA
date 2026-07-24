from app.database.connection import get_connection


def agregar_stock_minimo():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'medicamentos'
              AND COLUMN_NAME = 'stock_minimo'
        """)

        existe = cursor.fetchone()[0] > 0

        if not existe:
            cursor.execute("""
                ALTER TABLE medicamentos
                ADD COLUMN stock_minimo INT NOT NULL DEFAULT 10
                AFTER stock
            """)

            connection.commit()

            print(
                "Columna stock_minimo creada correctamente."
            )
        else:
            print(
                "La columna stock_minimo ya existe."
            )

        cursor.execute("""
            SELECT
                id,
                nombre,
                stock,
                stock_minimo
            FROM medicamentos
            ORDER BY nombre
        """)

        medicamentos = cursor.fetchall()

        print("")
        print("Medicamentos registrados:")
        print("")

        for medicamento in medicamentos:
            print(medicamento)

        cursor.close()


if __name__ == "__main__":
    agregar_stock_minimo()
