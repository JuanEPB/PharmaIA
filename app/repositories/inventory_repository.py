from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.repositories.database_adapter import (
    database_connection,
    dictionary_cursor,
)


class InventoryRepository:
    """
    Consultas agregadas del inventario farmacéutico.

    La tabla principal utilizada es medicamentos y contempla:

    id
    nombre
    lote
    caducidad
    stock
    stock_minimo
    precio
    proveedorId
    categoriaId
    """

    @staticmethod
    def _normalize_row(
        cursor: Any,
        row: Any,
    ) -> dict[str, Any]:
        if row is None:
            return {}

        if isinstance(row, dict):
            return row

        description = getattr(cursor, "description", None)

        if not description:
            return {}

        columns = [
            column[0]
            for column in description
        ]

        return dict(zip(columns, row))

    def _fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> dict[str, Any]:
        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(query, parameters)
                row = cursor.fetchone()

                return self._normalize_row(cursor, row)

    def _fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        with database_connection() as connection:
            with dictionary_cursor(connection) as cursor:
                cursor.execute(query, parameters)
                rows = cursor.fetchall()

                return [
                    self._normalize_row(cursor, row)
                    for row in rows
                ]

    def obtener_resumen(self) -> dict[str, Any]:
        query = """
            SELECT
                COUNT(*) AS total_medicamentos,

                COALESCE(SUM(stock), 0)
                    AS unidades_disponibles,

                COALESCE(
                    SUM(
                        CASE
                            WHEN stock = 0 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS agotados,

                COALESCE(
                    SUM(
                        CASE
                            WHEN stock > 0
                                AND stock <= stock_minimo
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS bajo_stock,

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
                                AND caducidad
                                    <= DATE_ADD(
                                        CURDATE(),
                                        INTERVAL 30 DAY
                                    )
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS por_caducar_30_dias,

                COALESCE(
                    SUM(
                        stock * precio
                    ),
                    0
                ) AS valor_total_inventario,

                COALESCE(
                    AVG(stock),
                    0
                ) AS promedio_stock,

                COALESCE(
                    AVG(precio),
                    0
                ) AS precio_promedio

            FROM medicamentos
        """

        return self._fetch_one(query)

    def obtener_alertas(
        self,
        limite: int = 100,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                m.id,
                m.nombre,
                m.lote,
                m.caducidad,
                m.stock,
                m.stock_minimo,
                m.precio,
                m.proveedorId AS proveedor_id,
                m.categoriaId AS categoria_id,

                CASE
                    WHEN m.caducidad < CURDATE()
                        THEN 'CADUCADO'

                    WHEN m.stock = 0
                        THEN 'AGOTADO'

                    WHEN m.stock <= GREATEST(
                        1,
                        FLOOR(m.stock_minimo * 0.5)
                    )
                        THEN 'CRITICO'

                    WHEN m.stock <= m.stock_minimo
                        THEN 'PRECAUCION'

                    WHEN m.caducidad <= DATE_ADD(
                        CURDATE(),
                        INTERVAL 30 DAY
                    )
                        THEN 'PROXIMO_A_CADUCAR'

                    ELSE 'NORMAL'
                END AS estado,

                DATEDIFF(
                    m.caducidad,
                    CURDATE()
                ) AS dias_para_caducar,

                GREATEST(
                    (m.stock_minimo * 2) - m.stock,
                    0
                ) AS cantidad_recomendada

            FROM medicamentos AS m

            WHERE
                m.caducidad < CURDATE()

                OR m.stock <= m.stock_minimo

                OR m.caducidad <= DATE_ADD(
                    CURDATE(),
                    INTERVAL 30 DAY
                )

            ORDER BY
                CASE
                    WHEN m.caducidad < CURDATE() THEN 1
                    WHEN m.stock = 0 THEN 2
                    WHEN m.stock <= GREATEST(
                        1,
                        FLOOR(m.stock_minimo * 0.5)
                    ) THEN 3
                    WHEN m.stock <= m.stock_minimo THEN 4
                    ELSE 5
                END,

                m.stock ASC,
                m.caducidad ASC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (limite,),
        )

    def obtener_estadisticas_categorias(
        self,
    ) -> list[dict[str, Any]]:
        """
        Funciona aunque la tabla categorías no esté disponible,
        utilizando primero una consulta con JOIN y después una
        consulta agrupada únicamente por categoriaId.
        """

        query_with_join = """
            SELECT
                m.categoriaId AS categoria_id,

                COALESCE(
                    c.nombre,
                    CONCAT(
                        'Categoría ',
                        m.categoriaId
                    )
                ) AS categoria,

                COUNT(*) AS total_medicamentos,

                COALESCE(
                    SUM(m.stock),
                    0
                ) AS unidades,

                COALESCE(
                    SUM(m.stock * m.precio),
                    0
                ) AS valor_inventario,

                COALESCE(
                    SUM(
                        CASE
                            WHEN m.stock = 0 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS agotados,

                COALESCE(
                    SUM(
                        CASE
                            WHEN m.stock > 0
                                AND m.stock <= m.stock_minimo
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS bajo_stock

            FROM medicamentos AS m

            LEFT JOIN categorias AS c
                ON c.id = m.categoriaId

            GROUP BY
                m.categoriaId,
                c.nombre

            ORDER BY
                total_medicamentos DESC,
                categoria ASC
        """

        try:
            return self._fetch_all(query_with_join)

        except Exception:
            fallback_query = """
                SELECT
                    categoriaId AS categoria_id,

                    CONCAT(
                        'Categoría ',
                        categoriaId
                    ) AS categoria,

                    COUNT(*) AS total_medicamentos,

                    COALESCE(
                        SUM(stock),
                        0
                    ) AS unidades,

                    COALESCE(
                        SUM(stock * precio),
                        0
                    ) AS valor_inventario,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN stock = 0 THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS agotados,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN stock > 0
                                    AND stock <= stock_minimo
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS bajo_stock

                FROM medicamentos

                GROUP BY categoriaId

                ORDER BY
                    total_medicamentos DESC,
                    categoria ASC
            """

            return self._fetch_all(fallback_query)

    def obtener_estadisticas_proveedores(
        self,
    ) -> list[dict[str, Any]]:
        query_with_join = """
            SELECT
                m.proveedorId AS proveedor_id,

                COALESCE(
                    p.nombre,
                    CONCAT(
                        'Proveedor ',
                        m.proveedorId
                    )
                ) AS proveedor,

                COUNT(*) AS total_medicamentos,

                COALESCE(
                    SUM(m.stock),
                    0
                ) AS unidades,

                COALESCE(
                    SUM(m.stock * m.precio),
                    0
                ) AS valor_inventario,

                COALESCE(
                    SUM(
                        CASE
                            WHEN m.stock = 0 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS agotados,

                COALESCE(
                    SUM(
                        CASE
                            WHEN m.caducidad < CURDATE()
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS caducados

            FROM medicamentos AS m

            LEFT JOIN proveedores AS p
                ON p.id = m.proveedorId

            GROUP BY
                m.proveedorId,
                p.nombre

            ORDER BY
                total_medicamentos DESC,
                proveedor ASC
        """

        try:
            return self._fetch_all(query_with_join)

        except Exception:
            fallback_query = """
                SELECT
                    proveedorId AS proveedor_id,

                    CONCAT(
                        'Proveedor ',
                        proveedorId
                    ) AS proveedor,

                    COUNT(*) AS total_medicamentos,

                    COALESCE(
                        SUM(stock),
                        0
                    ) AS unidades,

                    COALESCE(
                        SUM(stock * precio),
                        0
                    ) AS valor_inventario,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN stock = 0 THEN 1
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
                    ) AS caducados

                FROM medicamentos

                GROUP BY proveedorId

                ORDER BY
                    total_medicamentos DESC,
                    proveedor ASC
            """

            return self._fetch_all(fallback_query)

    def obtener_mayor_stock(
        self,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                id,
                nombre,
                lote,
                stock,
                stock_minimo,
                precio,
                caducidad
            FROM medicamentos
            ORDER BY stock DESC, nombre ASC
            LIMIT %s
        """

        return self._fetch_all(
            query,
            (limite,),
        )

    def obtener_menor_stock(
        self,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                id,
                nombre,
                lote,
                stock,
                stock_minimo,
                precio,
                caducidad
            FROM medicamentos
            ORDER BY stock ASC, nombre ASC
            LIMIT %s
        """

        return self._fetch_all(
            query,
            (limite,),
        )


inventory_repository = InventoryRepository()
