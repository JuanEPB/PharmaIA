from app.database.connection import get_connection


class MedicamentosRepository:

    @staticmethod
    def obtener_todos():

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""

                SELECT *

                FROM medicamentos

                ORDER BY nombre

            """)

            datos = cursor.fetchall()

            cursor.close()

            return datos


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

                    stock,

                    stock_minimo

                FROM medicamentos

                WHERE stock<=stock_minimo

                ORDER BY stock

            """)

            datos = cursor.fetchall()

            cursor.close()

            return datos


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

                    stock

                FROM medicamentos

                WHERE stock=0

            """)

            datos = cursor.fetchall()

            cursor.close()

            return datos


    @staticmethod
    def buscar(nombre):

        with get_connection() as connection:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(

                """

                SELECT *

                FROM medicamentos

                WHERE nombre LIKE %s

                """,

                (f"%{nombre}%",)

            )

            datos = cursor.fetchall()

            cursor.close()

            return datos
