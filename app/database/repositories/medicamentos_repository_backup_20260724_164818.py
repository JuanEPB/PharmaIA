from app.database.connection import get_connection


class MedicamentosRepository:
    """
    Repositorio encargado de ejecutar consultas SQL
    relacionadas con medicamentos.
    """

    @staticmethod
    def obtener_todos():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    lote,
                    caducidad,
                    stock,
                    stock_minimo,
                    precio,
                    proveedorId,
                    categoriaId
                FROM medicamentos
                ORDER BY nombre
            """)

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def obtener_bajo_stock():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    lote,
                    stock,
                    stock_minimo,
                    caducidad
                FROM medicamentos
                WHERE stock <= stock_minimo
                ORDER BY stock ASC, nombre ASC
            """)

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def obtener_agotados():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    lote,
                    stock,
                    stock_minimo,
                    caducidad
                FROM medicamentos
                WHERE stock <= 0
                ORDER BY nombre
            """)

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def buscar(nombre):

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    lote,
                    caducidad,
                    stock,
                    stock_minimo,
                    precio,
                    proveedorId,
                    categoriaId
                FROM medicamentos
                WHERE nombre LIKE %s
                ORDER BY nombre
                """,
                (f"%{nombre}%",),
            )

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def obtener_caducados():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    lote,
                    caducidad,
                    stock
                FROM medicamentos
                WHERE caducidad < CURDATE()
                ORDER BY caducidad ASC
            """)

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def obtener_por_caducar(dias=30):

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT
                    id,
                    nombre,
                    lote,
                    caducidad,
                    stock,
                    DATEDIFF(caducidad, CURDATE()) AS dias_restantes
                FROM medicamentos
                WHERE caducidad >= CURDATE()
                  AND caducidad <= DATE_ADD(
                      CURDATE(),
                      INTERVAL %s DAY
                  )
                ORDER BY caducidad ASC
                """,
                (dias,),
            )

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def obtener_caducidad_mes_actual():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    lote,
                    caducidad,
                    stock,
                    DATEDIFF(caducidad, CURDATE()) AS dias_restantes
                FROM medicamentos
                WHERE YEAR(caducidad) = YEAR(CURDATE())
                  AND MONTH(caducidad) = MONTH(CURDATE())
                ORDER BY caducidad ASC
            """)

            medicamentos = cursor.fetchall()

            cursor.close()

            return medicamentos

    @staticmethod
    def obtener_resumen():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_medicamentos,
                    COALESCE(SUM(stock), 0) AS unidades_totales,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN stock <= stock_minimo
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS bajo_stock,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN stock <= 0
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS agotados,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN caducidad < CURDATE()
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS caducados,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN caducidad >= CURDATE()
                                AND caducidad <= DATE_ADD(
                                    CURDATE(),
                                    INTERVAL 30 DAY
                                )
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS por_caducar
                FROM medicamentos
            """)

            resumen = cursor.fetchone()

            cursor.close()

            return resumen
