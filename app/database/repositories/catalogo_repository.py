from app.database.connection import get_connection


class CatalogoRepository:
    """
    Repositorio para consultas relacionadas con categorías,
    proveedores, precios y estadísticas.

    Detecta automáticamente el nombre de las columnas
    descriptivas de las tablas categorias y proveedores.
    """

    COLUMNAS_NOMBRE = (
        "nombre",
        "name",
        "categoria",
        "proveedor",
        "razonSocial",
        "razon_social",
        "descripcion",
    )

    @classmethod
    def _tabla_existe(cls, connection, tabla):
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            """,
            (tabla,),
        )

        existe = cursor.fetchone()[0] > 0
        cursor.close()

        return existe

    @classmethod
    def _obtener_columnas(cls, connection, tabla):
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """,
            (tabla,),
        )

        columnas = [
            fila[0]
            for fila in cursor.fetchall()
        ]

        cursor.close()

        return columnas

    @classmethod
    def _resolver_tabla(cls, connection, opciones):
        for tabla in opciones:
            if cls._tabla_existe(connection, tabla):
                return tabla

        return None

    @classmethod
    def _resolver_columna_nombre(
        cls,
        connection,
        tabla,
    ):
        columnas = cls._obtener_columnas(
            connection,
            tabla,
        )

        for candidata in cls.COLUMNAS_NOMBRE:
            if candidata in columnas:
                return candidata

        columnas_validas = [
            columna
            for columna in columnas
            if columna.lower() != "id"
        ]

        if columnas_validas:
            return columnas_validas[0]

        return None

    @classmethod
    def _configuracion_catalogos(cls, connection):
        tabla_categorias = cls._resolver_tabla(
            connection,
            (
                "categorias",
                "categoria",
            ),
        )

        tabla_proveedores = cls._resolver_tabla(
            connection,
            (
                "proveedores",
                "proveedor",
            ),
        )

        columna_categoria = None
        columna_proveedor = None

        if tabla_categorias:
            columna_categoria = (
                cls._resolver_columna_nombre(
                    connection,
                    tabla_categorias,
                )
            )

        if tabla_proveedores:
            columna_proveedor = (
                cls._resolver_columna_nombre(
                    connection,
                    tabla_proveedores,
                )
            )

        return {
            "tabla_categorias": tabla_categorias,
            "columna_categoria": columna_categoria,
            "tabla_proveedores": tabla_proveedores,
            "columna_proveedor": columna_proveedor,
        }

    @classmethod
    def obtener_inventario_detallado(cls):
        with get_connection() as connection:
            config = cls._configuracion_catalogos(
                connection
            )

            tabla_categorias = config[
                "tabla_categorias"
            ]

            columna_categoria = config[
                "columna_categoria"
            ]

            tabla_proveedores = config[
                "tabla_proveedores"
            ]

            columna_proveedor = config[
                "columna_proveedor"
            ]

            categoria_select = (
                f"c.`{columna_categoria}` AS categoria"
                if tabla_categorias
                and columna_categoria
                else "NULL AS categoria"
            )

            proveedor_select = (
                f"p.`{columna_proveedor}` AS proveedor"
                if tabla_proveedores
                and columna_proveedor
                else "NULL AS proveedor"
            )

            categoria_join = (
                f"""
                LEFT JOIN `{tabla_categorias}` c
                    ON c.id = m.categoriaId
                """
                if tabla_categorias
                and columna_categoria
                else ""
            )

            proveedor_join = (
                f"""
                LEFT JOIN `{tabla_proveedores}` p
                    ON p.id = m.proveedorId
                """
                if tabla_proveedores
                and columna_proveedor
                else ""
            )

            consulta = f"""
                SELECT
                    m.id,
                    m.nombre,
                    m.lote,
                    m.caducidad,
                    m.stock,
                    m.stock_minimo,
                    m.precio,
                    m.proveedorId,
                    m.categoriaId,
                    {categoria_select},
                    {proveedor_select}
                FROM medicamentos m
                {categoria_join}
                {proveedor_join}
                ORDER BY m.nombre
            """

            cursor = connection.cursor(dictionary=True)
            cursor.execute(consulta)

            resultados = cursor.fetchall()
            cursor.close()

            return resultados

    @classmethod
    def buscar_por_categoria(cls, categoria):
        with get_connection() as connection:
            config = cls._configuracion_catalogos(
                connection
            )

            tabla = config["tabla_categorias"]
            columna = config["columna_categoria"]

            if not tabla or not columna:
                return []

            tabla_proveedores = config[
                "tabla_proveedores"
            ]

            columna_proveedor = config[
                "columna_proveedor"
            ]

            proveedor_select = (
                f"p.`{columna_proveedor}` AS proveedor"
                if tabla_proveedores
                and columna_proveedor
                else "NULL AS proveedor"
            )

            proveedor_join = (
                f"""
                LEFT JOIN `{tabla_proveedores}` p
                    ON p.id = m.proveedorId
                """
                if tabla_proveedores
                and columna_proveedor
                else ""
            )

            consulta = f"""
                SELECT
                    m.id,
                    m.nombre,
                    m.lote,
                    m.caducidad,
                    m.stock,
                    m.stock_minimo,
                    m.precio,
                    c.`{columna}` AS categoria,
                    {proveedor_select}
                FROM medicamentos m
                INNER JOIN `{tabla}` c
                    ON c.id = m.categoriaId
                {proveedor_join}
                WHERE c.`{columna}` LIKE %s
                ORDER BY m.nombre
            """

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                consulta,
                (f"%{categoria}%",),
            )

            resultados = cursor.fetchall()
            cursor.close()

            return resultados

    @classmethod
    def buscar_por_proveedor(cls, proveedor):
        with get_connection() as connection:
            config = cls._configuracion_catalogos(
                connection
            )

            tabla = config["tabla_proveedores"]
            columna = config["columna_proveedor"]

            if not tabla or not columna:
                return []

            tabla_categorias = config[
                "tabla_categorias"
            ]

            columna_categoria = config[
                "columna_categoria"
            ]

            categoria_select = (
                f"c.`{columna_categoria}` AS categoria"
                if tabla_categorias
                and columna_categoria
                else "NULL AS categoria"
            )

            categoria_join = (
                f"""
                LEFT JOIN `{tabla_categorias}` c
                    ON c.id = m.categoriaId
                """
                if tabla_categorias
                and columna_categoria
                else ""
            )

            consulta = f"""
                SELECT
                    m.id,
                    m.nombre,
                    m.lote,
                    m.caducidad,
                    m.stock,
                    m.stock_minimo,
                    m.precio,
                    p.`{columna}` AS proveedor,
                    {categoria_select}
                FROM medicamentos m
                INNER JOIN `{tabla}` p
                    ON p.id = m.proveedorId
                {categoria_join}
                WHERE p.`{columna}` LIKE %s
                ORDER BY m.nombre
            """

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                consulta,
                (f"%{proveedor}%",),
            )

            resultados = cursor.fetchall()
            cursor.close()

            return resultados

    @classmethod
    def obtener_resumen_por_categoria(cls):
        with get_connection() as connection:
            config = cls._configuracion_catalogos(
                connection
            )

            tabla = config["tabla_categorias"]
            columna = config["columna_categoria"]

            if not tabla or not columna:
                return []

            consulta = f"""
                SELECT
                    c.id AS categoria_id,
                    c.`{columna}` AS categoria,
                    COUNT(m.id) AS total_medicamentos,
                    COALESCE(SUM(m.stock), 0)
                        AS unidades_totales,
                    COALESCE(SUM(m.stock * m.precio), 0)
                        AS valor_inventario
                FROM `{tabla}` c
                LEFT JOIN medicamentos m
                    ON m.categoriaId = c.id
                GROUP BY
                    c.id,
                    c.`{columna}`
                ORDER BY total_medicamentos DESC,
                         categoria ASC
            """

            cursor = connection.cursor(dictionary=True)
            cursor.execute(consulta)

            resultados = cursor.fetchall()
            cursor.close()

            return resultados

    @classmethod
    def obtener_resumen_por_proveedor(cls):
        with get_connection() as connection:
            config = cls._configuracion_catalogos(
                connection
            )

            tabla = config["tabla_proveedores"]
            columna = config["columna_proveedor"]

            if not tabla or not columna:
                return []

            consulta = f"""
                SELECT
                    p.id AS proveedor_id,
                    p.`{columna}` AS proveedor,
                    COUNT(m.id) AS total_medicamentos,
                    COALESCE(SUM(m.stock), 0)
                        AS unidades_totales,
                    COALESCE(SUM(m.stock * m.precio), 0)
                        AS valor_inventario
                FROM `{tabla}` p
                LEFT JOIN medicamentos m
                    ON m.proveedorId = p.id
                GROUP BY
                    p.id,
                    p.`{columna}`
                ORDER BY total_medicamentos DESC,
                         proveedor ASC
            """

            cursor = connection.cursor(dictionary=True)
            cursor.execute(consulta)

            resultados = cursor.fetchall()
            cursor.close()

            return resultados

    @classmethod
    def obtener_medicamento_mas_caro(cls):
        inventario = cls.obtener_inventario_detallado()

        if not inventario:
            return None

        return max(
            inventario,
            key=lambda medicamento: float(
                medicamento.get("precio") or 0
            ),
        )

    @classmethod
    def obtener_medicamento_mas_barato(cls):
        inventario = cls.obtener_inventario_detallado()

        if not inventario:
            return None

        return min(
            inventario,
            key=lambda medicamento: float(
                medicamento.get("precio") or 0
            ),
        )

    @classmethod
    def obtener_medicamento_menor_stock(cls):
        inventario = cls.obtener_inventario_detallado()

        if not inventario:
            return None

        return min(
            inventario,
            key=lambda medicamento: int(
                medicamento.get("stock") or 0
            ),
        )

    @classmethod
    def obtener_medicamento_mayor_stock(cls):
        inventario = cls.obtener_inventario_detallado()

        if not inventario:
            return None

        return max(
            inventario,
            key=lambda medicamento: int(
                medicamento.get("stock") or 0
            ),
        )

    @classmethod
    def proveedores_con_caducidad(cls, dias=30):
        with get_connection() as connection:
            config = cls._configuracion_catalogos(
                connection
            )

            tabla = config["tabla_proveedores"]
            columna = config["columna_proveedor"]

            if not tabla or not columna:
                return []

            consulta = f"""
                SELECT
                    p.id AS proveedor_id,
                    p.`{columna}` AS proveedor,
                    COUNT(m.id) AS medicamentos_por_caducar,
                    MIN(m.caducidad)
                        AS caducidad_mas_proxima
                FROM `{tabla}` p
                INNER JOIN medicamentos m
                    ON m.proveedorId = p.id
                WHERE m.caducidad >= CURDATE()
                  AND m.caducidad <= DATE_ADD(
                      CURDATE(),
                      INTERVAL %s DAY
                  )
                GROUP BY
                    p.id,
                    p.`{columna}`
                ORDER BY caducidad_mas_proxima ASC
            """

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                consulta,
                (dias,),
            )

            resultados = cursor.fetchall()
            cursor.close()

            return resultados
